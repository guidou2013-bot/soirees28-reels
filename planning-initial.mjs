// Planning initial des 10 Reels promo (28/09/2026) : 3 par semaine, heures de préparation des sorties.
// Copie les vidéos rendues dans media/ (réencodées plus légères) et écrit schedule.json.
// Pour la suite, ajouter/retirer avec ajouter.mjs (voir LISEZMOI.md).
import { writeFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const SRC = 'F:/Desktop/CLAUDE ALL PROJECT/hyperframes/videos/soirees28-reels/renders/';
const PAGES = 'https://guidou2013-bot.github.io/soirees28-reels/media/';
const TAGS = '#chartres #soireeschartres #chartres28 #eureetloir #sortirachartres #soireechartres #clubchartres #concertchartres';

// [numéro vidéo, date heure de Paris, titre, légende]
const PLAN = [
  ['05', '2026-09-28T22:30', 'Y a rien a faire a Chartres', "« Y'a rien à faire à Chartres. » Faux. Jeudi, vendredi, samedi, et même en semaine : il se passe toujours quelque chose. La preuve, chaque semaine ici."],
  ['07', '2026-09-30T18:30', 'Envoie ca a ton pote', "Tag le pote qui dit toujours « y'a rien à faire à Chartres ». Montre-lui."],
  ['01', '2026-10-02T18:30', 'Tu sors ou ce week-end', "Tu sors où ce week-end ? Clubs, concerts, bars, shows : toutes les soirées de Chartres sont ici. Abonne-toi et tu ne rates plus rien."],
  ['02', '2026-10-05T19:00', 'Les chiffres', "Depuis juin, 328 soirées de Chartres partagées, 61 lieux et organisateurs, plus de 1 000 abonnés. Et toi, tu nous suis ?"],
  ['04', '2026-10-07T18:30', 'Club Concert Bar Show', "T'es plutôt club, concert, bar ou show ? Peu importe, à Chartres on a tout. Abonne-toi pour voir ce qui se passe chaque soir."],
  ['08', '2026-10-09T18:30', 'Ce soir t as le choix', "Ce soir, t'as le choix. Trop de choix ? On trie pour toi : que les soirées de Chartres."],
  ['03', '2026-10-12T19:00', 'Tu l as su le lendemain', "La meilleure soirée du mois, tu l'as apprise le lendemain ? Plus jamais. Chaque soirée de Chartres est publiée ici, avant."],
  ['09', '2026-10-15T18:30', 'Chartres la nuit', "Chartres, la nuit. Le soir, on sort. Toutes les soirées de la ville au même endroit."],
  ['06', '2026-10-17T18:00', '3 raisons de s abonner', "3 raisons de t'abonner : toutes les soirées au même endroit, les soirées du jour en story, et c'est gratuit. Un clic."],
  ['10', '2026-10-20T18:30', 'Rejoins la page', "Toutes les soirées de Chartres en un clic. Rejoins les plus de 1 000 abonnés."],
];

const posts = [];
for (const [n, quand, titre, texte] of PLAN) {
  const id = `${quand.slice(0, 10)}-reel-${n}`;
  const dest = `media/${id}.mp4`;
  if (!existsSync(dest)) {
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', SRC + n + '.mp4', '-c:v', 'libx264', '-crf', '21', '-preset', 'slow', '-pix_fmt', 'yuv420p',
      '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', dest]);
  }
  posts.push({ id, titre: `Reel ${n} - ${titre}`, type: 'reel', video: PAGES + `${id}.mp4`,
    caption: `${texte}\n\n${TAGS}`, caption_fb: texte, quand, statut: 'planifie' });
}
writeFileSync('schedule.json', JSON.stringify({ timezone: 'Europe/Paris', posts }, null, 2) + '\n');
console.log(posts.length + ' Reels planifiés');
