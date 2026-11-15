#!/usr/bin/env python3
"""
evaluate.py -- turn the merged ratings and checks into every result in the write-up.  (Owner: Person A)

    python src/evaluate.py                          # real data in outputs/
    python src/evaluate.py --outputs outputs_dummy  # fake data, to test the code (NEVER quote these numbers)

Reads   <outputs>/master.csv    (human verdicts, made by tools/tie_out.py --all --write)
        <outputs>/features.csv  (number/negation checks + round-trip chrF, made by src/run_checks.py)

Writes  results_by_lang.csv, results_detectors.csv, results_error_types.csv, results_correlation.csv,
        failures.csv, thresholds.json, figures/unsafe_rate_by_lang.png, figures/detector_recall_precision.png

The rules (CONTRACT.md section 5, frozen before anyone saw results):
  * A row is one (sentence, language) pair from the main system. "Positive" means the human said unsafe.
  * The chrF threshold is chosen on the DEV sentences only. Every detector number is measured on TEST only.
    (If we picked the threshold on test, we would be grading our own homework.)
  * 95% intervals come from resampling SENTENCES (not rows) 1,000 times with seed 0. The same sentence
    appears in every language, so its rows are not independent; resampling whole sentences respects that.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MAIN_SYSTEM = "nllb600m"
MAIN_LANGS = ["hi", "zh", "ar"]        # the three languages in CONTRACT.md; any others are reported separately
VERDICT_SCORE = {"safe": 0, "minor": 1, "unsafe": 2}
N_BOOT, SEED = 1000, 0


# ---------------------------------------------------------------- loading
def load(outputs: Path) -> pd.DataFrame:
    """Join each human verdict with its automatic checks. One row per (sentence, language)."""
    master = pd.read_csv(outputs / "master.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    feats = pd.read_csv(outputs / "features.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    key = ["sentence_id", "lang", "system"]
    df = master.merge(feats, on=key, how="inner", validate="one_to_one")
    if len(df) != len(master):
        raise SystemExit(f"master.csv has {len(master)} rows but only {len(df)} match features.csv. "
                         "Re-run src/run_checks.py after the latest merge.")
    df = df[df["system"] == MAIN_SYSTEM].copy()
    df["unsafe"] = (df["verdict"] == "unsafe").astype(int)
    df["rt_chrf"] = pd.to_numeric(df["rt_chrf"], errors="coerce")
    df["labse_cos"] = pd.to_numeric(df["labse_cos"], errors="coerce")
    for col in ("number_flag", "negation_flag", "any_rule_flag"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


# ---------------------------------------------------------------- the detectors
def best_threshold(scores: pd.Series, unsafe: pd.Series) -> float | None:
    """The cut-off that maximises F1 for 'unsafe' on dev. A row is flagged when its score is BELOW it.

    Ties go to the higher threshold, which flags more rows (higher recall): for medicine labels a
    missed danger is worse than an extra warning.
    """
    s, y = scores.to_numpy(float), unsafe.to_numpy(int)
    ok = ~np.isnan(s)
    s, y = s[ok], y[ok]
    if len(s) == 0 or y.sum() == 0:
        return None
    best_f1, best_t = -1.0, None
    for t in sorted(set(s) | {s.max() + 1e-9}):          # each distinct score, plus "flag everything"
        flag = s < t
        tp = int((flag & (y == 1)).sum()); fp = int((flag & (y == 0)).sum()); fn = int((~flag & (y == 1)).sum())
        f1 = 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)
        if f1 > best_f1 or (f1 == best_f1 and best_t is not None and t > best_t):
            best_f1, best_t = f1, float(t)
    return best_t


def add_detector_flags(df: pd.DataFrame, thresholds: dict) -> list[str]:
    """Add one 0/1 column per detector. Returns the detector names, in report order."""
    df["det_always_safe"] = 0                                        # the do-nothing baseline: never warns
    df["det_rt_chrf"] = (df["rt_chrf"] < thresholds["rt_chrf"]).astype(int) if thresholds["rt_chrf"] is not None else 0
    df["det_number_rule"] = df["number_flag"]
    df["det_negation_rule"] = df["negation_flag"]
    df["det_rules"] = ((df["number_flag"] == 1) | (df["negation_flag"] == 1)).astype(int)
    df["det_rules_plus_chrf"] = ((df["det_rules"] == 1) | (df["det_rt_chrf"] == 1)).astype(int)
    names = ["always_safe", "rt_chrf", "number_rule", "negation_rule", "rules", "rules_plus_chrf"]
    if thresholds.get("labse_cos") is not None:                     # stretch goal S1, only if C filled the column
        df["det_labse"] = (df["labse_cos"] < thresholds["labse_cos"]).astype(int)
        names.insert(2, "labse")
    return names


# ---------------------------------------------------------------- statistics
def confusion(flag: np.ndarray, y: np.ndarray) -> dict:
    tp = int(((flag == 1) & (y == 1)).sum()); fp = int(((flag == 1) & (y == 0)).sum())
    fn = int(((flag == 0) & (y == 1)).sum()); tn = int(((flag == 0) & (y == 0)).sum())
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def rates(c: dict) -> dict:
    """Precision, recall, F1 and how often it warns. 'nan' when a rate has nothing to divide by."""
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if tp + fp else float("nan")
    recall = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "flag_rate": (tp + fp) / n if n else float("nan"),
            "false_alarms_per_10_nonunsafe": 10 * fp / (fp + tn) if fp + tn else float("nan")}


def bootstrap_ci(rows: pd.DataFrame, flag_col: str, rng: np.random.Generator) -> dict:
    """95% intervals for precision and recall, resampling whole sentences."""
    ids = rows["sentence_id"].unique()
    groups = {sid: g for sid, g in rows.groupby("sentence_id")}
    prec, rec = [], []
    for _ in range(N_BOOT):
        sample = pd.concat([groups[s] for s in rng.choice(ids, size=len(ids), replace=True)])
        r = rates(confusion(sample[flag_col].to_numpy(), sample["unsafe"].to_numpy()))
        if not math.isnan(r["precision"]):
            prec.append(r["precision"])
        if not math.isnan(r["recall"]):
            rec.append(r["recall"])
    q = lambda v: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if v else (float("nan"), float("nan"))
    (plo, phi), (rlo, rhi) = q(prec), q(rec)
    return {"precision_lo": plo, "precision_hi": phi, "recall_lo": rlo, "recall_hi": rhi}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for a proportion k/n (behaves well with small n)."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------- the report
def evaluate(outputs: Path) -> None:
    df = load(outputs)
    langs = [l for l in MAIN_LANGS if l in set(df["lang"])]
    extra = sorted(set(df["lang"]) - set(MAIN_LANGS))      # e.g. Kurmanji, if the lead merges it
    main = df[df["lang"].isin(langs)].copy()

    # 1. Unsafe rate per language, all 60 sentences (needs no threshold)
    by_lang = []
    for lang in langs + extra + ["all"]:
        g = main if lang == "all" else df[df["lang"] == lang]
        counts = g["verdict"].value_counts()
        k, n = int(counts.get("unsafe", 0)), len(g)
        lo, hi = wilson(k, n)
        by_lang.append({"lang": lang, "n": n, "safe": int(counts.get("safe", 0)), "minor": int(counts.get("minor", 0)),
                        "unsafe": k, "unsafe_rate": k / n if n else float("nan"), "unsafe_lo": lo, "unsafe_hi": hi})
    by_lang = pd.DataFrame(by_lang)

    # 2. One global threshold per score, chosen on dev only
    dev, test = main[main["split"] == "dev"], main[main["split"] == "test"].copy()
    thresholds = {"rt_chrf": best_threshold(dev["rt_chrf"], dev["unsafe"]),
                  "labse_cos": best_threshold(dev["labse_cos"], dev["unsafe"]) if dev["labse_cos"].notna().any() else None,
                  "chosen_on": "dev"}

    # 3. Detectors on test only, pooled and per language
    detectors = add_detector_flags(test, thresholds)
    rng = np.random.default_rng(SEED)
    rows = []
    for det in detectors:
        for lang in ["all"] + langs:
            g = test if lang == "all" else test[test["lang"] == lang]
            c = confusion(g[f"det_{det}"].to_numpy(), g["unsafe"].to_numpy())
            n_test = len(g)
            print(f"{'TIE' if sum(c.values()) == n_test else 'GAP'}: {det} {lang}: tp+fp+fn+tn = {sum(c.values())} "
                  f"vs n_test = {n_test}, Diff = {sum(c.values()) - n_test}")
            rows.append({"detector": det, "lang": lang, "n_test": n_test, **c, **rates(c), **bootstrap_ci(g, f"det_{det}", rng)})
    det_cols = ["detector", "lang", "n_test", "tp", "fp", "fn", "tn", "precision", "recall", "f1", "flag_rate",
                "false_alarms_per_10_nonunsafe", "precision_lo", "precision_hi", "recall_lo", "recall_hi"]
    results = pd.DataFrame(rows)[det_cols]

    # 4. Which kinds of mistake the translator made
    errors = (df[df["verdict"] != "safe"].groupby(["lang", "error_type"]).size()
              .reset_index(name="count").sort_values(["lang", "count"], ascending=[True, False]))

    # 5. Does the generic quality score track the human verdict?
    from scipy.stats import spearmanr
    corr = []
    for lang in langs + extra:
        g = df[(df["lang"] == lang) & df["rt_chrf"].notna()]
        ordinal = g["verdict"].map(VERDICT_SCORE)
        if len(g) > 2 and ordinal.nunique() > 1 and g["rt_chrf"].nunique() > 1:
            rho, p = spearmanr(g["rt_chrf"], ordinal)
        else:
            rho, p = float("nan"), float("nan")
        corr.append({"lang": lang, "spearman_rho": rho, "p_value": p, "n": len(g)})
    corr = pd.DataFrame(corr)

    # 6. Where the best detector fails, on test
    fn = test[(test["unsafe"] == 1) & (test["det_rules_plus_chrf"] == 0)].assign(kind="FN")
    fp = test[(test["unsafe"] == 0) & (test["det_rules_plus_chrf"] == 1)].assign(kind="FP")
    failures = pd.concat([fn, fp])[["lang", "sentence_id", "kind", "src_en", "translation", "corrected_translation",
                                    "error_type", "verdict"]].sort_values(["kind", "lang", "sentence_id"])

    # 7. Save everything
    outputs.mkdir(parents=True, exist_ok=True)
    by_lang.to_csv(outputs / "results_by_lang.csv", index=False, float_format="%.4f")
    results.to_csv(outputs / "results_detectors.csv", index=False, float_format="%.4f")
    errors.to_csv(outputs / "results_error_types.csv", index=False)
    corr.to_csv(outputs / "results_correlation.csv", index=False, float_format="%.4f")
    failures.to_csv(outputs / "failures.csv", index=False)
    (outputs / "thresholds.json").write_text(json.dumps(thresholds, indent=2) + "\n", encoding="utf-8")
    draw_figures(by_lang, results, outputs / "figures", langs + extra)

    # 8. A short readable summary
    if "dummy" in str(outputs):
        print("\n!!! DUMMY DATA: these numbers are fake. Never quote them.")
    print(f"\nchrF threshold chosen on dev: {thresholds['rt_chrf']}")
    print("\nUnsafe translations (all 60 sentences):")
    for r in by_lang.itertuples():
        print(f"  {r.lang:5} {r.unsafe:>3}/{r.n:<3} = {r.unsafe_rate:6.1%}  (95% interval {r.unsafe_lo:.0%} to {r.unsafe_hi:.0%})")
    pooled = results[results["lang"] == "all"]
    print(f"\nDetectors on held-out test sentences ({int(pooled['tp'].iloc[0] + pooled['fn'].iloc[0])} unsafe of "
          f"{int(pooled['n_test'].iloc[0])}):")
    for r in pooled.itertuples():
        print(f"  {r.detector:16} caught {r.tp}/{r.tp + r.fn} unsafe  ·  {r.fp} false alarms  ·  "
              f"recall {r.recall:.2f} [{r.recall_lo:.2f}, {r.recall_hi:.2f}]")
    print(f"\nfailures.csv: {len(fn)} missed unsafe rows, {len(fp)} false alarms")
    print(f"Wrote results to {outputs}/")


def draw_figures(by_lang: pd.DataFrame, results: pd.DataFrame, folder: Path, langs: list[str]) -> None:
    """Two charts sized to be read on a video: big labels, counts on the bars."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = {"hi": "Hindi", "zh": "Chinese", "ar": "Arabic", "kmr": "Kurmanji", "all": "All three"}
    folder.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 15, "axes.spines.top": False, "axes.spines.right": False})

    g = by_lang[by_lang["lang"].isin(langs)]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x = np.arange(len(g))
    rate = g["unsafe_rate"].to_numpy() * 100
    err = [rate - g["unsafe_lo"].to_numpy() * 100, g["unsafe_hi"].to_numpy() * 100 - rate]
    ax.bar(x, rate, color="#c0392b", width=0.6)
    ax.errorbar(x, rate, yerr=err, fmt="none", ecolor="#555", capsize=6, lw=1.5)
    for i, r in enumerate(g.itertuples()):
        ax.text(i, r.unsafe_hi * 100 + 2, f"{r.unsafe}/{r.n}", ha="center", fontsize=15, fontweight="bold")
    ax.set_xticks(x, [names.get(l, l) for l in g["lang"]])
    ax.set_ylabel("Unsafe translations (%)")
    ax.set_ylim(0, max(100, float(np.nanmax(g["unsafe_hi"])) * 100 + 12))
    ax.set_title("How often the free translator made a medicine label unsafe", fontsize=16, loc="left")
    fig.tight_layout(); fig.savefig(folder / "unsafe_rate_by_lang.png", dpi=150); plt.close(fig)

    p = results[results["lang"] == "all"]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    y = np.arange(len(p))
    ax.barh(y + 0.2, p["recall"].fillna(0) * 100, height=0.4, color="#c0392b", label="Unsafe ones caught (recall)")
    ax.barh(y - 0.2, p["precision"].fillna(0) * 100, height=0.4, color="#7f8c8d", label="Warnings that were right (precision)")
    for i, r in enumerate(p.itertuples()):
        ax.text((0 if math.isnan(r.recall) else r.recall * 100) + 1.5, i + 0.2, f"{r.tp}/{r.tp + r.fn}", va="center", fontsize=13)
    ax.set_yticks(y, [d.replace("_", " ") for d in p["detector"]])
    ax.invert_yaxis(); ax.set_xlim(0, 118); ax.set_xlabel("%  (held-out test sentences, all languages)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=12, frameon=False)
    ax.set_title("Which checks catch the unsafe translations?", fontsize=16, loc="left", pad=34)
    fig.tight_layout(); fig.savefig(folder / "detector_recall_precision.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--outputs", default="outputs", help="folder with master.csv and features.csv")
    a = ap.parse_args()
    out = Path(a.outputs)
    evaluate(out if out.is_absolute() else ROOT / out)
