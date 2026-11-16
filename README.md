# gracieladeleon.com

Portfolio site of Graciela De Leon. Static site built with [Astro](https://astro.build), hosted on Vercel.

## Work on it

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # runs the pre-deploy check, then builds to dist/
```

## Where things live

- `src/styles/global.css`: design tokens (light and dark) and all styles, ported from `assets/mockup-reference.html`.
- `src/layouts/Base.astro`: shared head (titles, Open Graph, favicon), nav, footer, Vercel Analytics.
- `src/content/work/*.mdx`: one file per project. Frontmatter fills the list rows and the case header; the body uses `<Section title fig figLabel>` blocks. Mark anything unverified with `<Pending what="..." />`, never a guess.
- `src/pages/work/[id].astro`: the one case-study template every project uses.
- `src/content/writing/*.md`: Writing list (set `published: true` once a post exists).
- `scripts/make-og.mjs`: renders the link preview image and icons (`npm run og`).

## Pre-deploy check

`npm run check` (also run by `npm run build`) fails on em dashes, on any term in `private/banned-terms.txt` (gitignored: client names and people, one per line), on email addresses other than the public one, on student ID-like numbers, and on private Drive links. Add `--dist` to scan the built HTML too.

## Deploys

Pushes to `preview` create a Vercel preview behind Vercel Authentication. Production deploys from `main` are off until launch; see `DOMAIN.md`.
