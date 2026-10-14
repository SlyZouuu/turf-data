# Construit un tableau cheval-par-course avec UNIQUEMENT des infos connues ~30 min avant le départ.
import json, glob, re, math
import numpy as np, pandas as pd
from collections import defaultdict
rows=[]
files=sorted(glob.glob("historique/raw/*.json"))
def musique(m):
    # "0p3p2p2p3p1p(25)0p8p0p" -> positions récentes (avant l'année entre parenthèses = courses plus anciennes)
    if not m: return []
    m=m.split("(")[0]
    out=[]
    for tok in re.findall(r"([0-9]|D|A|T|R|N)[a-z]",m):
        out.append(int(tok) if tok.isdigit() and tok!="0" else 10)
    return out
# stats glissantes driver / entraîneur : calculées AVANT chaque jour (pas de fuite)
drv=defaultdict(lambda:[0,0]); ent=defaultdict(lambda:[0,0])
for f in files:
    day=json.load(open(f)); today=[]
    for r in day:
        c=r["course"]
        if c.get("categorieStatut")!="ARRIVEE" or "SIMPLE_GAGNANT" not in r["rap"]: continue
        parts=[p for p in r["parts"] if p.get("statut")=="PARTANT" and p.get("dernierRapportReference") and p.get("dernierRapportDirect")]
        if len(parts)<4: continue
        g={a:d for a,d in r["rap"]["SIMPLE_GAGNANT"]}; pl={a:d for a,d in r["rap"].get("SIMPLE_PLACE",[])}
        refs=np.array([p["dernierRapportReference"]["rapport"] for p in parts],float)
        imp=1/refs; impn=imp/imp.sum()
        rid=f'{r["date"]}R{r["R"]}C{r["C"]}'
        for i,p in enumerate(parts):
            mu=musique(p.get("musique")); last=mu[:5]
            nc=p.get("nombreCourses") or 0; gp=p.get("gainsParticipant") or {}
            d=p.get("driver") or ""; e=p.get("entraineur") or ""
            ds,es=drv[d],ent[e]
            rows.append(dict(rid=rid,date=r["date"],disc=c.get("discipline"),num=p["numPmu"],
                nb=len(parts),distance=c.get("distance") or 0,prix=math.log1p(c.get("montantPrix") or 0),
                handicap=int("HANDICAP" in (c.get("categorieParticularite") or "")),
                cote_ref=refs[i],log_ref=math.log(refs[i]),p_mkt=impn[i],rang_ref=int((refs<refs[i]).sum())+1,
                tend=(p["dernierRapportReference"].get("nombreIndicateurTendance") or 0)*(1 if p["dernierRapportReference"].get("indicateurTendance")=="+" else -1),
                age=p.get("age") or 0,male=int(p.get("sexe")=="MALES"),hongre=int(p.get("sexe")=="HONGRES"),
                nc=nc,tx_v=(p.get("nombreVictoires") or 0)/nc if nc else 0,tx_p=(p.get("nombrePlaces") or 0)/nc if nc else 0,inedit=int(bool(p.get("indicateurInedit"))),
                gains_c=math.log1p((gp.get("gainsCarriere") or 0)/max(nc,1)),gains_a=math.log1p(gp.get("gainsAnneeEnCours") or 0),
                mu_mean=np.mean(last) if last else 8,mu_best=min(last) if last else 10,mu_last=last[0] if last else 10,mu_n=len(last),mu_win=sum(1 for x in last if x==1),mu_top3=sum(1 for x in last if x<=3),
                corde=p.get("placeCorde") or 0,poids=p.get("handicapPoids") or 0,hval=p.get("handicapValeur") or 0,
                deferre=int(bool(p.get("deferre")) and p.get("deferre")!="FERRE"),oeil=int(bool(p.get("oeilleres")) and p.get("oeilleres")!="SANS_OEILLERES"),
                drv_chg=int(bool(p.get("driverChange"))),supp=int((p.get("supplement") or 0)>0),
                drv_n=ds[0],drv_tx=(ds[1]+1)/(ds[0]+10),ent_n=es[0],ent_tx=(es[1]+1)/(es[0]+10),
                win=int(p.get("ordreArrivee")==1),div_g=g.get(str(p["numPmu"]),0),div_p=pl.get(str(p["numPmu"]),0),cote_fin=p["dernierRapportDirect"]["rapport"]))
            today.append((d,e,int(p.get("ordreArrivee")==1)))
    for d,e,w in today:   # mise à jour APRES la journée
        drv[d][0]+=1; drv[d][1]+=w; ent[e][0]+=1; ent[e][1]+=w
df=pd.DataFrame(rows)
# features relatives à la course
for col in ["tx_v","tx_p","gains_c","gains_a","mu_mean","drv_tx","ent_tx","hval"]:
    df[col+"_rel"]=df[col]-df.groupby("rid")[col].transform("mean")
df.to_pickle("historique/data.pkl")
print(df.shape, df.rid.nunique(),"courses", df.date.min(), df.date.max())
print(df.groupby(df.date.str[:7]).rid.nunique())
