// Renders public/og.png (1200x630 link preview), public/favicon-32.png, and public/apple-touch-icon.png.
// Run with `npm run og` after changing the headline or headshot; the outputs are committed.
import { readFileSync, writeFileSync } from "node:fs";
import satori from "satori";
import sharp from "sharp";
import { fileURLToPath } from "node:url";

const font = (pkg, file) => readFileSync(new URL(`../node_modules/@fontsource/${pkg}/files/${file}`, import.meta.url));
const fonts = [
  { name: "Literata", data: font("literata", "literata-latin-500-normal.woff"), weight: 500, style: "normal" },
  { name: "Public Sans", data: font("public-sans", "public-sans-latin-400-normal.woff"), weight: 400, style: "normal" },
  { name: "Public Sans", data: font("public-sans", "public-sans-latin-600-normal.woff"), weight: 600, style: "normal" },
];

const photo = await sharp(fileURLToPath(new URL("../assets/headshot.jpg", import.meta.url))).resize(240, 240).jpeg({ quality: 85 }).toBuffer();
const photoUri = `data:image/jpeg;base64,${photo.toString("base64")}`;

const h = (type, style, children) => ({ type, props: { style, children } });

const og = h("div", { width: 1200, height: 630, display: "flex", background: "#fbfbfa", fontFamily: "Public Sans", color: "#1a1f2b" }, [h("div", { position: "absolute", top: 72, left: 80, width: 1040, height: 486, display: "flex", flexDirection: "column" }, [
  h("div", { display: "flex", alignItems: "center", gap: 24 }, [
    { type: "img", props: { src: photoUri, width: 112, height: 112, style: { borderRadius: 56 } } },
    h("div", { display: "flex", flexDirection: "column", fontSize: 26, color: "#5a6172", lineHeight: 1.4 }, [
      h("div", { fontFamily: "Literata", fontSize: 34, color: "#1a1f2b" }, "Graciela De Leon"),
      h("div", {}, "AI product manager · Berkeley MBA/MPH"),
    ]),
  ]),
  h("div", { display: "flex", marginTop: "auto", fontFamily: "Literata", fontSize: 76, lineHeight: 1.1, maxWidth: 980 }, "I measure whether AI agents actually work."),
  h("div", { display: "flex", marginTop: 36, alignItems: "center", gap: 18, fontSize: 26, color: "#5a6172" }, [
    h("div", { width: 6, height: 40, background: "#1f5fae", display: "flex" }, null),
    h("div", { display: "flex" }, "Evals before launch, adoption after, ROI for the business."),
  ]),
])]);

const svg = await satori(og, { width: 1200, height: 630, fonts });
if (process.env.OG_DEBUG) writeFileSync(process.env.OG_DEBUG, svg);
writeFileSync(new URL("../public/og.png", import.meta.url), await sharp(Buffer.from(svg)).png({ compressionLevel: 9 }).toBuffer());

const icon = h("div", { width: 180, height: 180, display: "flex", alignItems: "center", justifyContent: "center", background: "#1f5fae", borderRadius: 36, color: "#fbfbfa", fontFamily: "Literata", fontSize: 120, paddingBottom: 12 }, "G");
const iconSvg = Buffer.from(await satori(icon, { width: 180, height: 180, fonts }));
writeFileSync(new URL("../public/apple-touch-icon.png", import.meta.url), await sharp(iconSvg).png().toBuffer());
writeFileSync(new URL("../public/favicon-32.png", import.meta.url), await sharp(iconSvg).resize(32, 32).png().toBuffer());
console.log("Wrote public/og.png, public/apple-touch-icon.png, public/favicon-32.png");
