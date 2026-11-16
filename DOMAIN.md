# Connecting gracieladeleon.com (for Graciela to do)

Nothing here has been done yet. The site is only on a protected Vercel preview until you do these steps.

## 1. Launch checklist (in this repo, before the domain points here)

1. Approve every page (see the "pending" markers on each page).
2. In `vercel.json`, delete the `"git": { "deploymentEnabled": { "main": false } }` line so pushes to `main` deploy to production.
3. In `public/robots.txt`, change `Disallow: /` to `Allow: /`.
4. In Vercel: Project, Settings, Environment Variables, add `PUBLIC_ALLOW_INDEXING` = `true` for Production. This removes the `noindex` tag.
5. In Vercel: Project, Analytics, click Enable (Web Analytics; no cookies, so no banner needed).
6. In Vercel: Project, Settings, Deployment Protection. Vercel Authentication is currently set to **All Deployments**, which also locks `gracieladeleon-site.vercel.app` (with the looser default, that address was public). Once the custom domain is attached and you are ready to launch, change it to **Standard Protection** so gracieladeleon.com is public and previews stay private.
7. Run `npm run build` locally (it runs the em dash and banned-terms check), then merge `preview` into `main` and push.

## 2. Add the domain in Vercel

1. Vercel, project `gracieladeleon-site`, Settings, Domains.
2. Add `gracieladeleon.com`. When asked, also add `www.gracieladeleon.com` and choose "Redirect www to the apex" (or the reverse; pick one).
3. Vercel then shows the exact records it expects. If they differ from step 3 below, use Vercel's values.

## 3. DNS records at your registrar

Sign in where gracieladeleon.com is registered, open its DNS settings, and:

| Type | Name / Host | Value | TTL |
|---|---|---|---|
| A | `@` (the bare domain) | `76.76.21.21` | default (or 3600) |
| CNAME | `www` | `cname.vercel-dns.com` | default (or 3600) |

- Delete any other A, AAAA, or CNAME records on `@` and `www` (for example a registrar parking page), or they will conflict.
- Leave MX and TXT records alone, so email keeps working.
- If the registrar does not allow editing records, the alternative is to switch nameservers to `ns1.vercel-dns.com` and `ns2.vercel-dns.com`, but then any email records must be re-created in Vercel first. The A and CNAME route above is safer.

## 4. Check

1. Back in Vercel, Settings, Domains: both rows turn to "Valid Configuration" (usually minutes, up to 48 hours).
2. Vercel issues the HTTPS certificate automatically.
3. Open https://gracieladeleon.com in a private window and paste the link into LinkedIn's Post Inspector (https://www.linkedin.com/post-inspector/) to confirm the preview card shows the headshot and headline.
