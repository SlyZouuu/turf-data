#!/usr/bin/env python3
"""Enregistre l'évolution des cotes PMU (simple gagnant) avant chaque course française.

Pour chaque course : une capture par minute de T-15 min jusqu'au départ, puis T+1 et T+3
(pour avoir la cote finale). Données publiques PMU uniquement, aucune connexion à un compte.

Usage :
    python3 enregistreur_cotes.py                # tourne jusqu'à la dernière course du jour
    python3 enregistreur_cotes.py --fin 16:30    # s'arrête à 16h30 (heure de Paris)
    python3 enregistreur_cotes.py --duree 350    # s'arrête au bout de 350 minutes (GitHub Actions)
Sortie : donnees/cotes/AAAA-MM-JJ[_suffixe].jsonl (une ligne JSON par capture)
"""
import argparse, datetime, json, os, sys, time, urllib.request
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
API = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme"
ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "donnees", "cotes")
AVANT = 15 * 60          # début des captures avant le départ (secondes)
APRES = [60, 180]        # captures après le départ, pour la cote finale


def get(url):
    for essai in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "turf-data/1.0"})
            return json.load(urllib.request.urlopen(req, timeout=20))
        except Exception:
            time.sleep(2 + essai * 3)
    return None


def courses_du_jour(jour):
    prog = get(f"{API}/{jour:%d%m%Y}?specialisation=OFFLINE")
    if not prog:
        return []
    out = []
    for r in prog["programme"]["reunions"]:
        if r.get("pays", {}).get("code") != "FRA":
            continue
        for c in r["courses"]:
            out.append(dict(R=r["numOfficiel"], C=c["numOrdre"], depart=c["heureDepart"] / 1000,
                            discipline=c.get("discipline"), hippo=r["hippodrome"]["libelleCourt"]))
    return out


def instants(c):
    """Heures (timestamp) des captures prévues pour une course."""
    t = [c["depart"] - s for s in range(AVANT, -1, -60)]
    return t + [c["depart"] + s for s in APRES]


def capture(jour, c, fichier):
    base = f"{API}/{jour:%d%m%Y}/R{c['R']}/C{c['C']}"
    lignes = []
    for spec in ("OFFLINE", "INTERNET"):
        d = get(f"{base}/rapports/SIMPLE_GAGNANT?specialisation={spec}")
        if not d:
            continue
        lignes.append(dict(t=round(time.time()), course=f"R{c['R']}C{c['C']}", spec=spec,
                           depart=c["depart"], discipline=c["discipline"], hippo=c["hippo"],
                           cotes={str(p["numPmu"]): p.get("rapportDirect") for p in d.get("rapportsParticipant", [])},
                           ref={str(p["numPmu"]): p.get("rapportReference") for p in d.get("rapportsParticipant", [])}))
    with open(fichier, "a") as f:
        for l in lignes:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return len(lignes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", help="heure d'arrêt HH:MM (Paris)")
    ap.add_argument("--duree", type=int, help="durée maximale en minutes")
    ap.add_argument("--suffixe", default="", help="suffixe du fichier (une session = un fichier)")
    a = ap.parse_args()
    jour = datetime.datetime.now(PARIS).date()
    fin = None
    if a.fin:
        h, m = map(int, a.fin.split(":"))
        fin = datetime.datetime.combine(jour, datetime.time(h, m), PARIS).timestamp()
    if a.duree:
        fin = min(fin or 1e12, time.time() + a.duree * 60)
    os.makedirs(SORTIE, exist_ok=True)
    fichier = os.path.join(SORTIE, f"{jour.isoformat()}{'_' + a.suffixe if a.suffixe else ''}.jsonl")

    courses = courses_du_jour(jour)
    plan = sorted((t, i) for i, c in enumerate(courses) for t in instants(c))
    print(f"{jour} : {len(courses)} courses françaises, {len(plan)} captures prévues", flush=True)
    derniere_maj = time.time()
    for t, i in plan:
        if fin and t > fin:
            break
        if t < time.time() - 30:          # capture déjà passée
            continue
        time.sleep(max(0, t - time.time()))
        # les heures de départ peuvent glisser : on recharge le programme toutes les 20 min
        if time.time() - derniere_maj > 1200:
            maj = {(c["R"], c["C"]): c["depart"] for c in courses_du_jour(jour)}
            for c in courses:
                c["depart"] = maj.get((c["R"], c["C"]), c["depart"])
            derniere_maj = time.time()
        c = courses[i]
        n = capture(jour, c, fichier)
        print(f"{datetime.datetime.now(PARIS):%H:%M:%S} R{c['R']}C{c['C']} ({n} captures)", flush=True)


if __name__ == "__main__":
    sys.exit(main())
