# Destination & Route Images

## Directory Structure

```
/public/images/
├── flights/           # Flight route images
│   ├── delhi-to-mumbai.webp
│   ├── mumbai-to-bangalore.webp
│   ├── delhi-to-goa.webp
│   ├── bangalore-to-delhi.webp
│   ├── mumbai-to-goa.webp
│   └── hyderabad-to-bangalore.webp
│
└── hotels/            # Hotel destination images
    ├── mumbai.webp
    ├── delhi.webp
    ├── goa.webp
    ├── bangalore.webp
    ├── jaipur.webp
    └── chennai.webp
```

## Image Requirements

### Format
- **Preferred**: WebP (best compression + quality)
- **Fallback**: JPEG (if WebP not available)

### Dimensions
- **Recommended**: 400x300px (4:3 aspect ratio)
- **Minimum**: 300x225px
- **Maximum**: 800x600px

### File Size
- **Target**: < 50KB per image
- **Maximum**: 100KB per image

### Naming Convention
- Flights: `{origin}-to-{destination}.webp` (lowercase, hyphenated)
- Hotels: `{city}.webp` (lowercase)

## Content Guidelines

### Flight Route Images
Show the **destination city** (not origin):
- delhi-to-mumbai.webp → Mumbai skyline/Gateway of India
- mumbai-to-goa.webp → Goa beach/coastline
- delhi-to-goa.webp → Goa beach/coastline

### Hotel Destination Images
Show iconic landmarks or hotel-friendly scenes:
- mumbai.webp → Mumbai skyline, Taj Hotel, Marine Drive
- delhi.webp → India Gate, Lotus Temple, city skyline
- goa.webp → Beach, resorts, palm trees
- bangalore.webp → City skyline, gardens
- jaipur.webp → Hawa Mahal, palace, pink buildings
- chennai.webp → Marina Beach, temples

## Image Optimization

### Before Adding Images

1. **Resize** to recommended dimensions
2. **Convert** to WebP format
3. **Compress** using tools like:
   - squoosh.app (free, browser-based)
   - TinyPNG (also supports WebP)
   - ImageOptim (Mac)

### Command Line (if available)
```bash
# Convert and compress with cwebp
cwebp -q 80 -resize 400 300 input.jpg -o output.webp
```

## Licensing

⚠️ **IMPORTANT**: Only use images you have rights to:
- Purchased stock photos
- CC0 / Public domain images
- Self-taken photographs
- Properly licensed images

**Recommended Sources**:
- Unsplash (free, attribution appreciated)
- Pexels (free)
- Pixabay (free)

## Enabling Images in Code

Once images are added, update `/components/seo/InternalLinks.tsx`:

```typescript
// Change from:
const hasImage = false

// To:
const hasImage = true
```

## Current Status

| Category | Images Added | Status |
|----------|--------------|--------|
| Flights  | 0/6          | Pending |
| Hotels   | 0/6          | Pending |

*Last updated: December 2025*
