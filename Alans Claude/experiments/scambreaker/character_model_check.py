import pandas as pd, runpy
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score
ns = runpy.run_path("attack_pairs.py"); pairs = ns["pairs"]
df = pd.read_csv("https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv", sep="\t", header=None, names=["label","text"]); y=(df.label=="spam").astype(int)
Xtr, Xte, ytr, yte = train_test_split(df.text, y, test_size=0.2, stratify=y, random_state=42)
cv = TfidfVectorizer(analyzer="char_wb", ngram_range=(2,5), sublinear_tf=True)
cm = LogisticRegression(max_iter=1000, class_weight="balanced", C=10).fit(cv.fit_transform(Xtr), ytr)
p = cm.predict(cv.transform(Xte)); print("char model precision %.3f recall %.3f" % (precision_score(yte,p), recall_score(yte,p)))
P = lambda t: cm.predict_proba(cv.transform([t]))[0,1]
leet = str.maketrans({"o":"0","i":"1","e":"3","a":"@"})
print("char model, reworded:", sum(P(n)<0.5 for _,n in pairs), "/20 slip past")
print("char model, look-alikes:", sum(P(o.translate(leet))<0.5 for o,_ in pairs), "/20 slip past")
