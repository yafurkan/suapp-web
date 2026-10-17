#!/usr/bin/env node
/**
 * Suu — Kişisel profil sayfasını kendi verisinden yeniden basar.
 *
 * Sayfalar normalde panelden (suuapp.com/<slug>/admin/) düzenlenir; panel
 * aynı çiziciyi (assets/js/profile-render.js) tarayıcıda çalıştırıp sonucu
 * GitHub'a yazar. Bu script, veriyi elle değiştirdiğinizde ya da çizici
 * değiştiğinde aynı işi yerelde yapar.
 *
 *   node scripts/build-profile.mjs furkan            # önizleme
 *   node scripts/build-profile.mjs furkan --apply
 *   node scripts/build-profile.mjs --all --apply     # tüm profil sayfaları
 */
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const P = createRequire(import.meta.url)(join(ROOT, 'assets/js/profile-render.js'));

const args = process.argv.slice(2);
const apply = args.includes('--apply');
let slugs = args.filter((a) => !a.startsWith('--'));

// Profil sayfası = içinde #profile-data bulunan <slug>/index.html
if (args.includes('--all')) {
    slugs = readdirSync(ROOT, { withFileTypes: true })
        .filter((d) => d.isDirectory() && existsSync(join(ROOT, d.name, 'index.html')))
        .map((d) => d.name)
        .filter((s) => readFileSync(join(ROOT, s, 'index.html'), 'utf8').includes('id="profile-data"'));
}
if (!slugs.length) {
    console.error('Kullanım: node scripts/build-profile.mjs <slug> [--apply]  |  --all [--apply]');
    process.exit(2);
}

let changed = 0;
for (const slug of slugs) {
    const file = join(ROOT, slug, 'index.html');
    const html = readFileSync(file, 'utf8');
    const data = P.readData(html);
    if (data.slug !== slug) throw new Error(`${slug}: verideki slug "${data.slug}" klasör adıyla aynı değil`);
    const out = P.apply(html, data);
    const state = out === html ? 'aynı' : 'güncellenecek';
    if (out !== html) {
        changed++;
        if (apply) writeFileSync(file, out);
    }
    console.log(`${slug}/index.html  ${Math.round(out.length / 1024)} KB  ${apply && out !== html ? 'yazıldı' : state}`);
}
console.log(`\n${changed} dosya ${apply ? 'yazıldı' : 'değişecek'}${apply ? '' : '  (yazmak için --apply)'}`);
