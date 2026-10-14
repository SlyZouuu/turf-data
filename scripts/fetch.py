import json, os, urllib.request, datetime
from concurrent.futures import ThreadPoolExecutor
B="https://online.turfinfo.api.pmu.fr/rest/client/1/programme"
OUT="historique/raw"
def get(u):
    for _ in range(4):
        try: return json.load(urllib.request.urlopen(u,timeout=30))
        except Exception: pass
KEEP_P=["numPmu","nom","age","sexe","race","statut","placeCorde","oeilleres","entraineur","driver","driverChange","indicateurInedit","musique","nombreCourses","nombreVictoires","nombrePlaces","nombrePlacesSecond","nombrePlacesTroisieme","gainsParticipant","handicapValeur","handicapPoids","poidsConditionMonte","deferre","ordreArrivee","incident","nomPere","dernierRapportDirect","dernierRapportReference","allure","jumentPleine","supplement","engagement","tempsObtenu","reductionKilometrique","avisEntraineur"]
def day(d):
    ds=d.strftime("%d%m%Y"); fn=f"{OUT}/{d.isoformat()}.json"
    if os.path.exists(fn): return d,"skip"
    j=get(f"{B}/{ds}?specialisation=OFFLINE")
    if not j: return d,"fail"
    races=[]
    for r in j["programme"]["reunions"]:
        if r.get("pays",{}).get("code")!="FRA": continue
        for c in r["courses"]:
            base=f"{B}/{ds}/R{r['numOfficiel']}/C{c['numOrdre']}"
            parts=(get(base+"/participants?specialisation=OFFLINE") or {}).get("participants",[])
            rap=get(base+"/rapports-definitifs?specialisation=OFFLINE") or []
            races.append(dict(date=d.isoformat(),R=r["numOfficiel"],C=c["numOrdre"],hippo=r["hippodrome"]["code"],
                course={k:c.get(k) for k in ["heureDepart","discipline","specialite","distance","corde","montantPrix","nombreDeclaresPartants","categorieParticularite","conditionAge","conditionSexe","typePiste","statut","categorieStatut","penetrometre","libelle","parcours","conditions","handicap"] if k in c} | {"terrain":(c.get("penetrometre") or {}).get("intitule")},
                parts=[{k:p.get(k) for k in KEEP_P if k in p} for p in parts],
                rap={x["typePari"]:[(z["combinaison"],z["dividendePourUnEuro"]/100) for z in x["rapports"]] for x in rap if x["typePari"] in ("SIMPLE_GAGNANT","SIMPLE_PLACE","E_SIMPLE_GAGNANT","E_SIMPLE_PLACE")}))
    json.dump(races,open(fn,"w"))
    return d,len(races)
days=[datetime.date(2026,4,1)+datetime.timedelta(i) for i in range((datetime.date(2026,10,13)-datetime.date(2026,4,1)).days+1)]
with ThreadPoolExecutor(10) as ex:
    for d,n in ex.map(day,days): pass
import glob; print(len(glob.glob(OUT+"/*.json")), sum(len(json.load(open(f))) for f in glob.glob(OUT+"/*.json")))
