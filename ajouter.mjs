// Ajoute une publication au planning du robot Reels Soirees Chartres 28, depuis le PC (session du pont Telegram).
// Usage :
//   node ajouter.mjs <fichier media> <AAAA-MM-JJTHH:MM> <legende-instagram.txt> [--fb legende-facebook.txt] [--type story] [--titre "..."]
//   node ajouter.mjs liste            -> publications a venir
//   node ajouter.mjs retirer <id>     -> annule une publication pas encore partie
// Le media est copie dans media/, converti si besoin (JPEG pour les images, H.264/AAC pour les videos),
// pousse sur GitHub, puis on attend que GitHub Pages le serve (Meta va le chercher par URL).
import { readFileSync, writeFileSync, copyFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { extname, basename, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ICI = dirname(fileURLToPath(import.meta.url));
const PAGES = 'https://guidou2013-bot.github.io/soirees28-reels/media/';
const SCHED = join(ICI, 'schedule.json');
const git = (...a) => execFileSync('git', a, { cwd: ICI, encoding: 'utf8' }).trim();
const lire = () => JSON.parse(readFileSync(SCHED, 'utf8'));
const ecrire = (s) => writeFileSync(SCHED, JSON.stringify(s, null, 2) + '\n');
const pousser = (msg) => {
  // commit d'abord : un pull --rebase refuse un dossier de travail modifie
  git('add', '-A');
  git('commit', '-q', '-m', msg);
  git('pull', '--rebase', '-q', 'origin', 'main');
  git('push', '-q', 'origin', 'main');
};

const [cmd, ...reste] = process.argv.slice(2);

if (cmd === 'liste') {
  git('pull', '--rebase', '-q', 'origin', 'main');
  const s = lire();
  const avenir = s.posts.filter((p) => ['planifie', 'partiel'].includes(p.statut));
  if (!avenir.length) console.log('Aucune publication a venir.');
  for (const p of avenir.sort((a, b) => a.quand.localeCompare(b.quand)))
    console.log(`${p.quand}  ${p.type.padEnd(6)} ${p.id}  ${p.titre}  [FB ${p.fb_done ? 'ok' : '-'} / IG ${p.ig_done ? 'ok' : '-'}]`);
  const erreurs = s.posts.filter((p) => p.fb_error || p.ig_error || p.statut === 'manque');
  for (const p of erreurs) console.log(`!! ${p.id} ${p.statut} ${p.fb_error || ''} ${p.ig_error || ''}`);
  process.exit(0);
}

if (cmd === 'retirer') {
  git('pull', '--rebase', '-q', 'origin', 'main');
  const s = lire();
  const p = s.posts.find((x) => x.id === reste[0]);
  if (!p) { console.error('Id introuvable.'); process.exit(1); }
  if (p.ig_done) { console.error('Deja publie sur Instagram : a supprimer a la main dans l\'appli.'); process.exit(1); }
  p.statut = 'annule';
  ecrire(s);
  pousser(`retirer ${p.id}`);
  console.log(`Annule : ${p.id}.` + (p.fb_done ? ` ATTENTION : deja programme sur Facebook (id ${p.fb_post_id}), le supprimer dans Business Suite > Programme.` : ''));
  process.exit(0);
}

// --- ajout
const opts = {};
const pos = [];
for (let i = 0; i < process.argv.slice(2).length; i++) {
  const a = process.argv.slice(2)[i];
  if (a.startsWith('--')) opts[a.slice(2)] = process.argv.slice(2)[++i];
  else pos.push(a);
}
const [fichier, quand, legendeFichier] = pos;
if (!fichier || !quand || !legendeFichier || !existsSync(fichier) || !existsSync(legendeFichier)) {
  console.error('Usage : node ajouter.mjs <fichier media> <AAAA-MM-JJTHH:MM> <legende-instagram.txt> [--fb legende-facebook.txt] [--type story] [--titre "..."]');
  process.exit(1);
}
if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(quand)) { console.error('Date attendue : AAAA-MM-JJTHH:MM (heure de Paris).'); process.exit(1); }
if (new Date(quand + ':00+01:00') < new Date(Date.now() + 20 * 60000)) { console.error('Date trop proche ou passee (20 min minimum).'); process.exit(1); }

const ext = extname(fichier).toLowerCase();
const video = ['.mp4', '.mov', '.m4v', '.webm'].includes(ext);
const image = ['.jpg', '.jpeg', '.png', '.webp'].includes(ext);
if (!video && !image) { console.error('Format non gere : ' + ext); process.exit(1); }

const slug = (opts.titre || basename(fichier, ext)).normalize('NFD').replace(/[̀-ͯ]/g, '')
  .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
const id = `${quand.slice(0, 10)}-${slug}`;
const s0 = lire();
if (s0.posts.some((p) => p.id === id)) { console.error('Id deja present : ' + id); process.exit(1); }
const nomMedia = id + (video ? '.mp4' : '.jpg');
const cible = join(ICI, 'media', nomMedia);

if (video) {
  // Instagram exige H.264 + AAC ; on reencode seulement si besoin
  const codecs = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', fichier], { encoding: 'utf8' });
  if (ext === '.mp4' && /h264/.test(codecs) && /aac/.test(codecs)) copyFileSync(fichier, cible);
  else execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', fichier, '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', cible]);
} else if (ext === '.jpg' || ext === '.jpeg') copyFileSync(fichier, cible);
else execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', fichier, '-q:v', '2', cible]);

const caption = readFileSync(legendeFichier, 'utf8').trim();
const post = {
  id,
  titre: opts.titre || basename(fichier, ext),
  type: opts.type === 'story' ? 'story' : video ? 'reel' : 'photo',
  [video ? 'video' : 'image']: PAGES + nomMedia,
  caption,
  quand,
  statut: 'planifie',
};
if (opts.fb) post.caption_fb = readFileSync(opts.fb, 'utf8').trim();
const s = lire();
s.posts.push(post);
ecrire(s);
pousser(`ajout ${id}`);

// Attendre que GitHub Pages serve le fichier (sinon Meta ne le trouvera pas)
const url = PAGES + nomMedia;
for (let i = 0; i < 40; i++) {
  try {
    const r = await fetch(url, { method: 'HEAD' });
    if (r.ok) { console.log(`OK : ${id} planifie le ${quand} (${post.type}). Media en ligne : ${url}`); process.exit(0); }
  } catch { /* on reessaie */ }
  await new Promise((r) => setTimeout(r, 10000));
}
console.log(`Planifie (${id}), mais le media n'est pas encore servi par GitHub Pages apres 6 min : verifier ${url}`);
