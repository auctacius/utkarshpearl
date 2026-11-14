import pandas as pd, numpy as np, pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score
df = pd.read_csv("https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv", sep="\t", header=None, names=["label","text"])
df["is_spam"] = (df.label=="spam").astype(int)
Xtr, Xte, ytr, yte = train_test_split(df.text, df.is_spam, test_size=0.2, stratify=df.is_spam, random_state=42)
vec = TfidfVectorizer(); A = vec.fit_transform(Xtr)
m = LogisticRegression(max_iter=1000, class_weight="balanced").fit(A, ytr)
p = m.predict(vec.transform(Xte))
print("repro precision %.3f recall %.3f" % (precision_score(yte,p), recall_score(yte,p)))
SKIP = ["sex","saucy","busty","moan","darling","dating","xxx","naughty","horny","babe","lingerie","adult","knickers","beg","admirer","singles","kiss","naked","hot ","girls","flirt","love"]
caught = [t for t,y,pp in zip(Xte,yte,p) if y==1 and pp==1 and not any(w in t.lower() for w in SKIP)]
print(len(caught), "caught printable spams")
for i,t in enumerate(caught[:30]):
    print(i, "|", round(m.predict_proba(vec.transform([t]))[0,1],2), "|", t)
pickle.dump((vec,m), open("model2.pkl","wb"))
