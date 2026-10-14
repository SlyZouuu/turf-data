import sys, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
df=pd.read_pickle("historique/data.pkl")
FINAL = "--final" in sys.argv          # le test d'octobre n'est lancé qu'une fois, à la fin
df["trot"]=df.disc.isin(["ATTELE","MONTE"]).astype(int)
F=["log_ref","p_mkt","rang_ref","tend","nb","distance","prix","handicap","age","male","hongre","nc","tx_v","tx_p","inedit","gains_c","gains_a",
   "mu_mean","mu_best","mu_last","mu_n","mu_win","mu_top3","corde","poids","hval","deferre","oeil","drv_chg","supp","drv_n","drv_tx","ent_n","ent_tx",
   "tx_v_rel","tx_p_rel","gains_c_rel","gains_a_rel","mu_mean_rel","drv_tx_rel","ent_tx_rel","hval_rel","trot"]
train=df[df.date<"2026-08-01"]; valid=df[(df.date>="2026-08-01")&(df.date<"2026-10-01")]; test=df[df.date>="2026-10-01"]
def norm(d,p): s=pd.Series(p,index=d.index); return s/s.groupby(d.rid).transform("sum")
def ll(d,p): w=d.win.values==1; return -np.mean(np.log(np.clip(p[w],1e-6,1)))   # log-loss "conditionnelle" = proba donnée au vrai gagnant
models={"logit":make_pipeline(StandardScaler(),LogisticRegression(C=0.3,max_iter=2000)),
        "boosting":HistGradientBoostingClassifier(max_iter=300,learning_rate=0.04,max_leaf_nodes=15,min_samples_leaf=200,l2_regularization=1.0,random_state=0)}
evals=[("valid août-sept",valid)]+([("TEST octobre",test)] if FINAL else [])
print(f"chevaux train={len(train)} valid={len(valid)} test={len(test)}")
for name,d in [("train",train)]+evals: print(f"log-loss MARCHÉ (cote réf.) {name}: {ll(d,d.p_mkt.values):.4f}")
res={}
for mn,m in models.items():
    m.fit(train[F],train.win)
    for name,d in evals:
        p=norm(d,m.predict_proba(d[F])[:,1]).values
        print(f"log-loss {mn:8} {name}: {ll(d,p):.4f}")
        res[(mn,name)]=p
def roi(d,p,thr,lo=1,hi=1000,disc=None):
    sel=(p*d.cote_ref>thr)&(d.cote_ref>=lo)&(d.cote_ref<hi)
    if disc is not None: sel&=d.trot==disc
    n=int(sel.sum())
    if n==0: return n,0,0
    ret=d.div_g[sel].sum(); return n,round((ret/n-1)*100,1),round((ret-n)*10,0)
print("\nPari simple gagnant 10 € quand proba_modèle × cote_réf > seuil")
for (mn,name),p in res.items():
    d=[x for n,x in evals if n==name][0]
    for thr in [1.0,1.1,1.2,1.3,1.5,2.0]:
        a=roi(d,p,thr); b=roi(d,p,thr,1,15); t=roi(d,p,thr,disc=1); g=roi(d,p,thr,disc=0)
        print(f"{mn:8} {name:16} seuil {thr}: tous n={a[0]:5} ROI={a[1]:6}% | cote<15 n={b[0]:5} ROI={b[1]:6}% | trot n={t[0]:5} ROI={t[1]:6}% | galop n={g[0]:5} ROI={g[1]:6}%")
