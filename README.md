# turf-data

Enregistrement de l'évolution des cotes PMU (simple gagnant) dans les 15 dernières minutes avant chaque course française, pour tester une stratégie de paris sur données réelles.

- `scripts/enregistreur_cotes.py` : capture les cotes (données publiques PMU, aucune connexion à un compte).
- `.github/workflows/cotes.yml` : lance l'enregistrement chaque jour sur GitHub Actions (3 sessions).
- `donnees/cotes/` : une ligne JSON par capture.
- `scripts/fetch.py`, `features.py`, `train.py`, `diag.py` : collecte de l'historique et modèle (l'historique reste en local, dans `historique/`).

Aucun pari n'est placé automatiquement.
