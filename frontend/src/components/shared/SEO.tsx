import { Title, Meta, Link } from "@solidjs/meta";
import { Component } from "solid-js";

interface SEOProps {
  title: string;
  description: string;
  path?: string;
  ogImage?: string;
  ogImageAlt?: string;
  ogType?: string;
  noindex?: boolean;
  nofollow?: boolean;
}

const BASE_URL = "https://lykke.day";
const DEFAULT_OG_IMAGE = `${BASE_URL}/images/og-image.png`;
const DEFAULT_OG_IMAGE_ALT =
  "lykke.day — Find happiness in everyday moments. A daily companion that helps you get the small stuff done so you're more effective to do the big stuff.";
const DEFAULT_DESCRIPTION =
  "Lykke (loo-kah) — the Danish art of finding happiness in everyday moments. A daily companion that helps you get the small stuff done so you're more effective to do the big stuff.";

const SEO: Component<SEOProps> = (props) => {
  const title = () => `${props.title} | lykke.day`;
  const description = () => props.description || DEFAULT_DESCRIPTION;
  const canonical = () => (props.path ? `${BASE_URL}${props.path}` : BASE_URL);
  const ogImage = () => props.ogImage || DEFAULT_OG_IMAGE;
  const ogImageAlt = () => props.ogImageAlt || DEFAULT_OG_IMAGE_ALT;
  const ogType = () => props.ogType || "website";
  const ogUrl = canonical;

  // Robots meta
  const robotsContent = () =>
    [props.noindex && "noindex", props.nofollow && "nofollow"]
      .filter(Boolean)
      .join(", ") || "index, follow";

  return (
    <>
      <Title>{title()}</Title>
      <Meta name="description" content={description()} />
      <Meta name="robots" content={robotsContent()} />

      {/* Open Graph / Facebook / iMessage */}
      <Meta property="og:type" content={ogType()} />
      <Meta property="og:site_name" content="lykke.day" />
      <Meta property="og:locale" content="en_US" />
      <Meta property="og:url" content={ogUrl()} />
      <Meta property="og:title" content={title()} />
      <Meta property="og:description" content={description()} />
      <Meta property="og:image" content={ogImage()} />
      <Meta property="og:image:secure_url" content={ogImage()} />
      <Meta property="og:image:type" content="image/png" />
      <Meta property="og:image:width" content="1200" />
      <Meta property="og:image:height" content="630" />
      <Meta property="og:image:alt" content={ogImageAlt()} />

      {/* Twitter Card */}
      <Meta name="twitter:card" content="summary_large_image" />
      <Meta name="twitter:site" content="@lykkeday" />
      <Meta name="twitter:creator" content="@lykkeday" />
      <Meta name="twitter:url" content={ogUrl()} />
      <Meta name="twitter:title" content={title()} />
      <Meta name="twitter:description" content={description()} />
      <Meta name="twitter:image" content={ogImage()} />
      <Meta name="twitter:image:alt" content={ogImageAlt()} />

      {/* Additional meta for better compatibility */}
      <Meta name="theme-color" content="#fbbf24" />
      <Meta name="apple-mobile-web-app-title" content="lykke.day" />

      {/* Canonical URL */}
      <Link rel="canonical" href={canonical()} />
    </>
  );
};

export default SEO;
