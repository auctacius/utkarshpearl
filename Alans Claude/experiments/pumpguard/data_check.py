"""PumpGuard feasibility check: does the labelled pump-and-dump dataset load,
and how are pump events spread across years and coins?

Data: La Morgia, Mei, Sassi and Stefa, "Pump and Dumps in the Bitcoin Era",
ICCCN 2020. https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset
"""
import pandas as pd

URL = ("https://raw.githubusercontent.com/SystemsLab-Sapienza/pump-and-dump-dataset/"
       "master/labeled_features/features_25S.csv.gz")
df = pd.read_csv(URL)
df["year"] = df["date"].str[:4]
print("rows, columns:", df.shape)
print("pump starts (gt = 1):", int(df["gt"].sum()))
print("\npump starts by year:\n", df.groupby("year")["gt"].sum().to_string())
early = set(df[df.year.isin(["2018", "2019"])].symbol)
late = set(df[df.year.isin(["2020", "2021"])].symbol)
print(f"\ncoins in 2018-19: {len(early)}, in 2020-21: {len(late)}, only in 2020-21: {len(late - early)}")
