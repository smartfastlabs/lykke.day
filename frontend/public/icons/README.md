# lykke.day Icon Pack

A complete favicon and icon set for lykke.day PWA.

## Colors
- Background: `#FEF7ED` (warm cream)
- Text: `#57534e` (stone)
- Accent: `#F59E0B` (amber)

## Files Included

### Core Favicons
- `favicon.ico` — Multi-resolution ICO (16, 32, 48px)
- `favicon.svg` — Scalable vector favicon
- `favicon-16x16.png` — Standard small favicon
- `favicon-32x32.png` — Standard favicon

### Apple
- `apple-touch-icon.png` — 180x180 iOS home screen icon
- `safari-pinned-tab.svg` — Monochrome pinned tab icon

### Android / PWA
- `android-chrome-192x192.png` — Chrome/Android icon
- `android-chrome-512x512.png` — Chrome/Android splash icon
- `maskable-icon-192x192.png` — Maskable icon with safe zone
- `maskable-icon-512x512.png` — Maskable icon with safe zone

### Windows
- `mstile-150x150.png` — Windows tile icon
- `browserconfig.xml` — Windows tile configuration

### Standard Sizes (for general use)
- `icon-16x16.png`
- `icon-32x32.png`
- `icon-48x48.png`
- `icon-64x64.png`
- `icon-96x96.png`
- `icon-128x128.png`
- `icon-192x192.png`
- `icon-256x256.png`
- `icon-512x512.png`

### Configuration
- `site.webmanifest` — PWA manifest file

## HTML Implementation

Add this to your `<head>`:

```html
<!-- Favicons -->
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">

<!-- Apple -->
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="mask-icon" href="/safari-pinned-tab.svg" color="#F59E0B">

<!-- PWA Manifest -->
<link rel="manifest" href="/site.webmanifest">

<!-- Windows -->
<meta name="msapplication-TileColor" content="#FEF7ED">
<meta name="msapplication-config" content="/browserconfig.xml">

<!-- Theme -->
<meta name="theme-color" content="#FEF7ED">
```

## File Placement

Place all files in your public/static root directory, or adjust paths in the HTML accordingly.

## Maskable Icons

The maskable icons include extra padding to ensure content remains visible when the OS applies various mask shapes (circles, rounded squares, etc.). These are recommended for PWA installations on Android.
