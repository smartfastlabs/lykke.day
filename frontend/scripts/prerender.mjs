import { renderToString } from "solid-js/web";
import { MetaProvider } from "@solidjs/meta";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const distDir = join(__dirname, "../dist");
const indexHtmlPath = join(distDir, "index.html");

// Marketing routes to prerender
const MARKETING_ROUTES = [
  {
    path: "/",
    title: "Lykke — Find happiness in everyday moments",
    description:
      "Lykke (loo-kah) — the Danish art of finding happiness in everyday moments. A daily companion that helps you get the small stuff done so you're more effective to do the big stuff.",
  },
  {
    path: "/resources",
    title: "Resources",
    description:
      "Channels, podcasts, and books that explore attention, rest, purpose, and kinder systems—voices that helped rethink productivity and presence.",
  },
  {
    path: "/apps",
    title: "Apps We've Tried",
    description:
      "From productivity apps and habit trackers to wellness apps, meditation apps, and mental health apps—there are many excellent health and wellness tools available.",
  },
  {
    path: "/books",
    title: "Books We Recommend",
    description:
      "These books resonated during the journey to adapting to life after covid—books that explore attention, rest, purpose, and kinder ways to rebuild.",
  },
  {
    path: "/youtube",
    title: "YouTube Channels We Recommend",
    description:
      "Channels that explore attention, rest, purpose, and kinder systems—voices that helped rethink productivity and presence through visual learning and making complex ideas click.",
  },
  {
    path: "/podcasts",
    title: "Podcasts We Recommend",
    description:
      "Conversations on attention, burnout recovery, and building a kinder relationship with productivity. Brilliant companions for in-between moments that explore mindfulness and intentional living.",
  },
  {
    path: "/faq",
    title: "Frequently Asked Questions",
    description:
      "Learn about lykke.day—a calm, day-at-a-time companion that helps you build gentle routines and find happiness in everyday moments. Quick answers to common questions.",
  },
  {
    path: "/privacy",
    title: "Privacy Policy",
    description:
      "Your data is yours. We collect only what's needed to run lykke.day and we never sell your information. You can export or delete your data anytime.",
  },
  {
    path: "/terms",
    title: "Terms of Service",
    description:
      "By using lykke.day, you agree to these terms. We provide a daily planning and wellness companion—use it kindly and lawfully.",
  },
];

const BASE_URL = "https://lykke.day";
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
