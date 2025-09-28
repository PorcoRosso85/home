# Gallery Page UI Specification

## Purpose/Overview

This specification defines the structure and requirements for gallery-style pages in the programmatic SEO system. Gallery pages are content-rich, image-focused pages designed to showcase collections of visual content while maximizing SEO performance through structured data and optimized internal linking.

**Primary Goals:**
- Rich visual content presentation with SEO-optimized markup
- JSON-LD structured data for enhanced search engine understanding
- Strategic internal linking for improved site architecture
- Efficient pagination for large image collections
- Performance-optimized image loading and metadata

## JSON-LD Requirements

### Core Schema Types

**1. ImageObject Schema (Individual Images)**
```javascript
{
  "@context": "https://schema.org",
  "@type": "ImageObject",
  "url": "https://example.com/images/photo-1.jpg",
  "name": "Image Title",
  "description": "Detailed image description",
  "width": 1200,
  "height": 800,
  "thumbnailUrl": "https://example.com/images/thumbs/photo-1.jpg",
  "contentUrl": "https://example.com/images/photo-1.jpg",
  "representativeOfPage": false,
  "isAccessibleForFree": true,
  "author": {
    "@type": "Person",
    "name": "Photographer Name"
  }
}
```

**2. Collection/ItemList Schema (Gallery Container)**
```javascript
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Gallery Collection Title",
  "description": "Collection description optimized for search",
  "url": "https://example.com/gallery/collection-name",
  "numberOfItems": 24,
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "ImageObject",
        "url": "https://example.com/images/photo-1.jpg",
        "name": "Image Title"
      }
    }
  ],
  "creator": {
    "@type": "Person",
    "name": "Gallery Creator"
  },
  "isAccessibleForFree": true
}
```

### JSON-LD Insertion Points

**1. Head Section (Primary Structured Data)**
- Collection schema for the entire gallery
- Hero image schema (representativeOfPage: true)
- BreadcrumbList schema for navigation

**2. Individual Image Containers**
- ImageObject schema for each visible image
- Embedded within `<figure>` or image container elements
- Include metadata like dimensions, alt text, and author information

**3. Pagination Context**
- SiteNavigationElement schema for pagination controls
- Additional Collection schemas for paginated subsets

## Page Structure

### HTML Structure Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- SEO Meta Tags -->
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>[Gallery Name] - [Page X of Y] | [Site Name]</title>
  <meta name="description" content="[SEO-optimized gallery description]">
  <link rel="canonical" href="[canonical-url]">

  <!-- Pagination Meta -->
  <link rel="prev" href="[previous-page-url]" />
  <link rel="next" href="[next-page-url]" />

  <!-- JSON-LD Structured Data -->
  <script type="application/ld+json">[Collection Schema]</script>
  <script type="application/ld+json">[BreadcrumbList Schema]</script>
</head>
<body>
  <!-- Header/Navigation -->
  <header>
    <nav aria-label="Site navigation">
      <!-- Site navigation -->
    </nav>
    <nav aria-label="Breadcrumb">
      <!-- Breadcrumb navigation -->
    </nav>
  </header>

  <!-- Main Content -->
  <main>
    <header>
      <h1>[Gallery Title]</h1>
      <p class="gallery-description">[Gallery Description]</p>
      <div class="gallery-meta">
        <span>Page [X] of [Y]</span>
        <span>[Total] images</span>
      </div>
    </header>

    <!-- Gallery Grid -->
    <section class="gallery-grid" aria-label="Image gallery">
      <!-- Image items with structured data -->
    </section>

    <!-- Pagination -->
    <nav aria-label="Gallery pagination">
      <!-- Pagination controls -->
    </nav>
  </main>

  <!-- Footer -->
  <footer>
    <!-- Footer content and links -->
  </footer>
</body>
</html>
```

### Individual Image Item Structure

```html
<figure class="gallery-item" data-position="[position]">
  <a href="[full-image-url]" class="image-link">
    <img
      src="[thumbnail-url]"
      alt="[descriptive-alt-text]"
      width="[thumb-width]"
      height="[thumb-height]"
      loading="lazy"
      data-full-src="[full-image-url]"
      data-full-width="[full-width]"
      data-full-height="[full-height]"
    />
  </a>
  <figcaption>
    <h3 class="image-title">[Image Title]</h3>
    <p class="image-description">[Image Description]</p>
    <div class="image-meta">
      <span class="author">By [Author Name]</span>
      <span class="dimensions">[width] × [height]</span>
    </div>
  </figcaption>
  <script type="application/ld+json">[ImageObject Schema]</script>
</figure>
```

## Internal Linking Strategy

### Hierarchical Navigation Structure

**1. Category-Based Linking**
```
/gallery/ (Root gallery index)
├── /gallery/[category]/ (Category landing pages)
├── /gallery/[category]/[subcategory]/ (Subcategory pages)
└── /gallery/[category]/[subcategory]/page/[n]/ (Paginated content)
```

**2. Related Content Linking**
- **Similar Galleries**: Cross-link to related image collections
- **Tag-Based Relations**: Link galleries sharing common tags/themes
- **Author/Creator Pages**: Link to creator profile or portfolio pages
- **Temporal Relations**: Link to galleries from similar time periods

**3. Strategic Link Placement**
- **Breadcrumb Navigation**: Clear hierarchical path
- **Category Sidebar**: Related categories and popular galleries
- **Footer Links**: Site-wide gallery navigation
- **Related Galleries Section**: 3-5 related collections per page

### Link Attribute Optimization

```html
<!-- Internal gallery links -->
<a href="/gallery/nature/landscapes/"
   title="Nature Landscape Photography Gallery"
   aria-label="View nature landscape photography collection">
   Landscape Gallery
</a>

<!-- Category navigation -->
<a href="/gallery/portraits/"
   rel="category"
   title="Portrait Photography Collection">
   Portraits
</a>

<!-- Pagination links -->
<a href="/gallery/nature/page/2/"
   rel="next"
   title="Next page of nature photography">
   Next →
</a>
```

## Pagination Implementation

### URL Structure
```
/gallery/[collection]/ (Page 1, canonical)
/gallery/[collection]/page/2/ (Page 2+)
/gallery/[collection]/page/[n]/ (Page N)
```

### Pagination Controls HTML

```html
<nav class="pagination" aria-label="Gallery pagination">
  <div class="pagination-info">
    <span>Page <strong>[current]</strong> of <strong>[total]</strong></span>
    <span>Showing [start]-[end] of [total-items] images</span>
  </div>

  <ul class="pagination-controls">
    <li><a href="[first-url]" rel="first" aria-label="First page">« First</a></li>
    <li><a href="[prev-url]" rel="prev" aria-label="Previous page">‹ Previous</a></li>

    <!-- Numbered pagination -->
    <li class="current" aria-current="page"><span>[current]</span></li>
    <li><a href="[next-url]" aria-label="Page [next]">[next]</a></li>

    <li><a href="[next-url]" rel="next" aria-label="Next page">Next ›</a></li>
    <li><a href="[last-url]" rel="last" aria-label="Last page">Last »</a></li>
  </ul>
</nav>
```

### Pagination SEO Requirements

**1. Canonical URLs**
- Page 1: `<link rel="canonical" href="/gallery/collection/">`
- Page 2+: `<link rel="canonical" href="/gallery/collection/page/[n]/">`

**2. Pagination Link Relations**
```html
<!-- Page 1 -->
<link rel="next" href="/gallery/collection/page/2/">

<!-- Middle pages -->
<link rel="prev" href="/gallery/collection/page/[n-1]/">
<link rel="next" href="/gallery/collection/page/[n+1]/">

<!-- Last page -->
<link rel="prev" href="/gallery/collection/page/[n-1]/">
```

**3. Meta Tags for Pagination**
- Include page number in title: `[Gallery Name] - Page [X] of [Y]`
- Modify description for pages 2+: `[Base description] - Page [X]`
- Use `noindex` for deep pagination (page 10+)

## Image Metadata Requirements

### Required Metadata Fields

**1. Core Image Data**
```typescript
{
  url: string;           // Full resolution image URL
  thumbnailUrl: string;  // Optimized thumbnail URL
  width: number;         // Full image width
  height: number;        // Full image height
  thumbWidth: number;    // Thumbnail width
  thumbHeight: number;   // Thumbnail height
  alt: string;           // Accessibility description
  title: string;         // Image title/name
  description?: string;  // Extended description
}
```

**2. SEO Enhancement Data**
```typescript
{
  caption?: string;      // Image caption for display
  keywords?: string[];   // Image-specific keywords
  author?: {            // Image creator/photographer
    name: string;
    url?: string;
  };
  license?: string;      // Usage license information
  exifData?: {          // Camera/technical metadata
    camera?: string;
    lens?: string;
    settings?: string;
    location?: string;
  };
}
```

### Image Optimization Requirements

**1. Format Support**
- WebP for modern browsers with JPEG fallback
- Responsive image sets using `srcset` and `sizes`
- Progressive JPEG encoding for faster loading

**2. Loading Strategy**
- `loading="lazy"` for all non-hero images
- `fetchpriority="high"` for hero/above-fold images
- Preload critical images and thumbnails

**3. Performance Targets**
- Thumbnail images: < 50KB each
- Full images: < 500KB each
- Total page weight: < 2MB initial load
- LCP (Largest Contentful Paint): < 2.5s

## SEO Metadata

### Page-Level Meta Tags

```html
<!-- Primary meta tags -->
<title>[Gallery Name] - [Category] | [Site Name]</title>
<meta name="description" content="[SEO description 150-160 chars]">
<meta name="keywords" content="[relevant, keywords, separated, by, commas]">

<!-- Open Graph -->
<meta property="og:title" content="[Gallery Name]">
<meta property="og:description" content="[Gallery description]">
<meta property="og:image" content="[hero-image-url]">
<meta property="og:url" content="[canonical-url]">
<meta property="og:type" content="website">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="[Gallery Name]">
<meta name="twitter:description" content="[Gallery description]">
<meta name="twitter:image" content="[hero-image-url]">

<!-- Additional SEO -->
<meta name="robots" content="index, follow">
<meta name="author" content="[Gallery Creator]">
<link rel="canonical" href="[canonical-url]">
```

### Image-Level SEO Attributes

```html
<img
  src="[image-url]"
  alt="[descriptive alt text optimized for accessibility and SEO]"
  title="[concise image title]"
  width="[width]"
  height="[height]"
  loading="lazy"
  decoding="async"
/>
```

## Technical Requirements

### Performance Requirements
- **Initial Load**: < 3s on 3G
- **Image Loading**: Progressive with lazy loading
- **Bundle Size**: Core gallery JS < 50KB gzipped
- **Memory Usage**: Efficient image management for large galleries

### Accessibility Requirements
- **Keyboard Navigation**: Full keyboard support for gallery browsing
- **Screen Reader Support**: Proper ARIA labels and descriptions
- **Focus Management**: Clear focus indicators and logical tab order
- **Alt Text**: Descriptive alternative text for all images

### Browser Compatibility
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Progressive Enhancement**: Basic functionality without JavaScript
- **Responsive Design**: Mobile-first approach with breakpoints at 768px, 1024px, 1440px

### Integration Points
- **Measurement System**: Integration with `packages/measurement/` for analytics
- **SEO Package**: Utilization of `packages/seo/` for JSON-LD generation
- **Edge Workers**: Compatible with Phase 1.2 edge deployment requirements
