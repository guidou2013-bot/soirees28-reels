# Robot Reels promo @soireeschartres28 (soirees28-reels)

Publie les Reels « abonne-toi » sur l'Instagram **@soireeschartres28** et la Page Facebook **SoireesChartres28**
aux dates prévues, via l'API officielle Meta. Tourne sur GitHub Actions : le PC peut être éteint.
Séparé du robot des soirées (`soirees-chartres`), qui n'est pas touché.

## Fonctionnement (copie du robot PSK)
- `schedule.json` : le planning (vidéo, légende Instagram avec hashtags, légende Facebook sans, date heure de Paris, statut).
- `publish.py` : passe toutes les 30 min de 6h à minuit.
  - Facebook : programmé nativement dès qu'on est à moins de 28 jours (visible dans Business Suite > Programmé).
  - Instagram : publié à l'heure dite (30 min de décalage au plus).
- Vidéos : dossier `media/`, servies par GitHub Pages (`https://guidou2013-bot.github.io/soirees28-reels/media/`).
- Bilan de chaque publication (et panne) envoyé sur Telegram à Guillaume.

## Les vidéos
Fabriquées dans `F:\Desktop\CLAUDE ALL PROJECT\hyperframes\videos\soirees28-reels\` (scénarios `videos.mjs`).
Copies lisibles : `F:\Desktop\AUTRES PROJETS\Soirées Chartres 28 - VISUELS\8 - Reels pour gagner des abonnes (28-09)\`.
`planning-initial.mjs` a posé les 10 premiers Reels (28/09 → 20/10, lundi, mercredi, vendredi).

## Ajouter / retirer
```
cd "F:\Desktop\CLAUDE ALL PROJECT\soirees28-reels-robot"
node ajouter.mjs "<video.mp4>" 2026-10-22T18:30 legende-ig.txt --fb legende-fb.txt --titre "Reel 11"
node ajouter.mjs liste
node ajouter.mjs retirer <id>
```

## Secrets (posés le 28/09 depuis le .env du robot des soirées)
`META_PAGE_TOKEN` (même jeton que le robot des soirées, sans expiration), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

## Tester
Actions > « Publier les Reels Soirees Chartres 28 » > Run workflow : `check_only = 1` (connexion) ou `dry_run = 1` (simulation).
