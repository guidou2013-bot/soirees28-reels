"""Attend l'heure exacte du prochain post Instagram (30/09/2026).

Le cron GitHub saute des passages (parfois 5 h sans run). Chaque passage
regarde donc si un post Instagram tombe dans les 5 h 30 qui viennent et,
si oui, dort jusqu'a son heure avant de lancer publish.py. Aucun ordinateur
allume n'est necessaire : l'attente se fait sur le serveur GitHub.
"""
import json
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HORIZON = timedelta(hours=5, minutes=30)

with open("schedule.json", encoding="utf-8") as f:
    sched = json.load(f)
tz = ZoneInfo(sched.get("timezone", "Europe/Paris"))
now = datetime.now(tz)

prochains = []
for p in sched["posts"]:
    if p.get("ig_done") or p.get("statut") in ("publie", "manque"):
        continue
    quand = datetime.fromisoformat(p["quand"]).replace(tzinfo=tz)
    if now < quand <= now + HORIZON:
        prochains.append((quand, p.get("titre", p["id"])))

if not prochains:
    print("Rien dans les 5 h 30 : pas d'attente.")
else:
    quand, titre = min(prochains)
    attente = (quand - now).total_seconds() + 30
    print(f"Attente de {attente / 60:.0f} min jusqu'a {quand:%d/%m %H:%M} ({titre}).")
    time.sleep(attente)
