import { renderToString } from "solid-js/web";
import { MetaProvider } from "@solidjs/meta";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { BASE_URL, MARKETING_ROUTES } from "./site-data.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const distDir = join(__dirname, "../dist");
const indexHtmlPath = join(distDir, "index.html");

const DEFAULT_OG_IMAGE = `${BASE_URL}/images/og-image.png`;

function generateMetaTags(route) {
  const title = `${route.title} | lykke.day`;
  const description = route.description;
  const canonical = `${BASE_URL}${route.path}`;
  const ogImage = DEFAULT_OG_IMAGE;

  return `
    <title>${title}</title>
    <meta name="description" content="${description.replace(/"/g, "&quot;")}" />
    <meta name="robots" content="index, follow" />
    
    <!-- Open Graph / Facebook / iMessage -->
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="lykke.day" />
    <meta property="og:locale" content="en_US" />
    <meta property="og:url" content="${canonical}" />
    <meta property="og:title" content="${title.replace(/"/g, "&quot;")}" />
    <meta property="og:description" content="${description.replace(/"/g, "&quot;")}" />
    <meta property="og:image" content="${ogImage}" />
    <meta property="og:image:secure_url" content="${ogImage}" />
    <meta property="og:image:type" content="image/png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="${description.replace(/"/g, "&quot;")}" />
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:site" content="@lykkeday" />
    <meta name="twitter:creator" content="@lykkeday" />
    <meta name="twitter:url" content="${canonical}" />
    <meta name="twitter:title" content="${title.replace(/"/g, "&quot;")}" />
    <meta name="twitter:description" content="${description.replace(/"/g, "&quot;")}" />
    <meta name="twitter:image" content="${ogImage}" />
    <meta name="twitter:image:alt" content="${description.replace(/"/g, "&quot;")}" />
    
    <!-- Additional meta for better compatibility -->
    <meta name="theme-color" content="#fbbf24" />
    <meta name="apple-mobile-web-app-title" content="lykke.day" />
    
    <!-- Canonical URL -->
    <link rel="canonical" href="${canonical}" />
  `;
}

function prerenderRoute(route, baseHtml) {
  const metaTags = generateMetaTags(route);

  // Remove the default title and inject our meta tags
  let html = baseHtml.replace(/<title>.*?<\/title>/, metaTags.trim());

  // If no title tag was replaced (maybe different format), inject after head opening
  if (!html.includes(metaTags)) {
    html = html.replace(/<head>/, `<head>${metaTags}`);
  }

  // Save to appropriate path
  let filePath;
  if (route.path === "/") {
    filePath = join(distDir, "index.html");
  } else {
    filePath = join(distDir, route.path.slice(1), "index.html");
    const fileDir = dirname(filePath);
    if (!existsSync(fileDir)) {
      mkdirSync(fileDir, { recursive: true });
    }
  }

  writeFileSync(filePath, html, "utf-8");
  console.log(`✓ Prerendered: ${route.path}`);
}

async function main() {
  console.log("Starting prerender...");

  if (!existsSync(indexHtmlPath)) {
    console.error(
      `Error: ${indexHtmlPath} not found. Run 'npm run build' first.`
    );
    process.exit(1);
  }

  const baseHtml = readFileSync(indexHtmlPath, "utf-8");

  for (const route of MARKETING_ROUTES) {
    prerenderRoute(route, baseHtml);
  }

  console.log("✓ Prerendering complete!");
}

main().catch((error) => {
  console.error("Prerender error:", error);
  process.exit(1);
});
