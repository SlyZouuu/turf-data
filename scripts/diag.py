exec(open("scripts/train.py").read().split("def roi")[0].replace('print(','(lambda *a,**k:None)('))
import numpy as np
d=valid.copy(); d["p"]=res[("boosting","valid août-sept")]
imp_f=1/d.cote_fin; d["p_fin"]=imp_f/imp_f.groupby(d.rid).transform("sum")
print("log-loss cote réf (30 min avant):",round(ll(d,d.p_mkt.values),4)," modèle:",round(ll(d,d.p.values),4)," cote FINALE:",round(ll(d,d.p_fin.values),4))
for thr in [1.0,1.2,1.5]:
    s=d[d.p*d.cote_ref>thr]
    print(f"seuil {thr}: {len(s)} paris | cote réf moyenne {s.cote_ref.mean():.1f} -> cote finale moyenne {s.cote_fin.mean():.1f} | % où la cote a BAISSÉ: {(s.cote_fin<s.cote_ref).mean()*100:.0f}% | taux de victoire réel {s.win.mean()*100:.1f}% vs prévu {s.p.mean()*100:.1f}%")
# importance approx: corrélation tendance
print("chevaux dont la cote baisse ensuite : ROI gagnant si on les jouait à la cote finale =", round((d[d.cote_fin<d.cote_ref*0.8].div_g.mean()-1)*100,1),"%")
