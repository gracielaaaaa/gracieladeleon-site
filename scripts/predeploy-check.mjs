#!/usr/bin/env node
// Pre-deploy check. Fails (exit 1) on:
//   1. em dashes (the character, &mdash;, or &#8212;) anywhere in site source or content
//   2. any term in private/banned-terms.txt (client names, people), case-insensitive, whole words
//   3. student-data patterns: email addresses other than the allowed one, 8 to 10 digit IDs, "SID" labels
//   4. private Google Drive or Docs links
// private/ is gitignored, so the banned list never leaves this machine. Without it the check fails
// locally; on Vercel (where the file cannot exist) it warns and runs the other checks.
// Usage: node scripts/predeploy-check.mjs [--dist]   (--dist also scans the built HTML in dist/)
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative, extname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const TERMS_FILE = join(ROOT, "private", "banned-terms.txt");
const ALLOWED_EMAILS = new Set(["graciela.deleon@berkeley.edu", "noreply@anthropic.com"]);
const SKIP_DIRS = new Set(["node_modules", ".git", ".astro", ".vercel", "private", "dist"]);
const SKIP_FILES = new Set(["scripts/predeploy-check.mjs", "package-lock.json"]);
const TEXT_EXT = new Set([".astro", ".md", ".mdx", ".html", ".css", ".js", ".mjs", ".ts", ".json", ".svg", ".txt", ".yml", ".yaml", ".xml"]);

const scanDist = process.argv.includes("--dist");

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const rel = relative(ROOT, p);
    if (statSync(p).isDirectory()) {
      if (SKIP_DIRS.has(name) && !(scanDist && rel === "dist")) continue;
      walk(p, out);
    } else if (TEXT_EXT.has(extname(name)) && !SKIP_FILES.has(rel)) {
      out.push(p);
    }
  }
  return out;
}

const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
let terms = [];
const problems = [];
if (existsSync(TERMS_FILE)) {
  terms = readFileSync(TERMS_FILE, "utf8").split("\n").map((t) => t.trim()).filter((t) => t && !t.startsWith("#"));
} else if (process.env.VERCEL) {
  console.warn("warning: private/banned-terms.txt not found (expected on Vercel); run the full check locally before pushing.");
} else {
  problems.push("private/banned-terms.txt is missing. Create it (one term per line) before deploying.");
}
const termRes = terms.map((t) => ({ t, re: new RegExp(`(?<![\\p{L}\\p{N}])${escape(t)}(?![\\p{L}\\p{N}])`, "iu") }));

const checks = [
  { name: "em dash", re: /—|&mdash;|&#8212;|&#x2014;/i },
  { name: "student ID-like number (8 to 10 digits)", re: /(?<![\d.,$#\w-])\d{8,10}(?![\d,.\w])/ },
  { name: "SID label", re: /\bSID\s*[:#]?\s*\d/ },
  { name: "private Google Drive/Docs link", re: /(docs|drive)\.google\.com\/\S*\/d\/[\w-]{20,}/ },
];
const emailRe = /[\w.+-]+@[\w-]+(\.[\w-]+)+/g;

const files = [...walk(ROOT)];
for (const file of files) {
  const rel = relative(ROOT, file);
  const lines = readFileSync(file, "utf8").split("\n");
  // Built CSS and JS bundles include minified third-party code; only scan their text for em dashes and terms.
  const isBundle = rel.startsWith("dist/") && /\.(css|js|mjs)$/.test(rel);
  lines.forEach((line, i) => {
    const at = `${rel}:${i + 1}`;
    for (const c of checks) {
      if (isBundle && c.name !== "em dash") continue;
      if (c.re.test(line)) problems.push(`${at}  ${c.name}`);
    }
    for (const m of line.matchAll(emailRe)) {
      const e = m[0].toLowerCase();
      if (!ALLOWED_EMAILS.has(e) && !/@(example\.(com|org|edu)|[\w.-]*\.(png|jpg|svg|webp|woff2?))$/.test(e) && !/^[\w-]+@\d/.test(e) && !isBundle) {
        problems.push(`${at}  email address not on the allow list (${e})`);
      }
    }
    for (const { t, re } of termRes) if (re.test(line)) problems.push(`${at}  banned term (${t.length > 3 ? t.slice(0, 2) + "..." : "***"})`);
  });
}

if (problems.length) {
  console.error(`Pre-deploy check FAILED (${problems.length}):`);
  for (const p of problems) console.error("  " + p);
  process.exit(1);
}
console.log(`Pre-deploy check passed: ${files.length} files, ${terms.length} banned terms, no em dashes.`);
