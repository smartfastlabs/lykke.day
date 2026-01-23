import { writeFileSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { BASE_URL, MARKETING_ROUTES } from "./site-data.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const publicDir = join(__dirname, "../public");
const sitemapPath = join(publicDir, "sitemap.xml");

const routes = MARKETING_ROUTES.map((route) => route.path);
const uniqueRoutes = Array.from(new Set(routes));

const urlEntries = uniqueRoutes
  .map((path) => `${BASE_URL}${path}`)
  .map(
    (loc) => `  <url>\n    <loc>${loc}</loc>\n  </url>`
  )
  .join("\n");

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urlEntries}
</urlset>
`;

if (!existsSync(publicDir)) {
  mkdirSync(publicDir, { recursive: true });
}

writeFileSync(sitemapPath, sitemap, "utf-8");
console.log(`✓ Sitemap generated: ${sitemapPath}`);
