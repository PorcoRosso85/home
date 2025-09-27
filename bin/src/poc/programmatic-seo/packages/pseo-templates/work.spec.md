# Work/Portfolio Page UI Specification

**Version**: 1.0
**Target**: Phase 1.2 Edge-Min Implementation
**Purpose**: Programmatic SEO-optimized work/portfolio pages with structured data and performance tracking

## Overview

This specification defines the UI requirements for work/portfolio pages that leverage programmatic SEO techniques through structured data, performance measurement, and content optimization. These pages showcase creative work, technical projects, and professional achievements while maximizing search engine visibility and user engagement.

## Schema Selection Guidelines

### When to Use HowTo Schema
- **Process-focused projects**: Step-by-step tutorials, implementation guides, workflows
- **Educational content**: Teaching methodologies, skill development processes
- **Technical documentation**: API implementation guides, setup procedures
- **Required elements**: Clear sequential steps, estimated time, tools/supplies

```typescript
// HowTo implementation example
{
  "@type": "HowTo",
  "name": "Building a React Component Library",
  "step": [
    { "name": "Setup TypeScript configuration", "text": "..." },
    { "name": "Create component structure", "text": "..." }
  ],
  "totalTime": "PT4H",
  "tool": ["TypeScript", "React", "Storybook"]
}
```

### When to Use CreativeWork Schema
- **Outcome-focused projects**: Finished products, designs, applications
- **Portfolio pieces**: Visual work, completed software, creative outputs
- **Project showcases**: Case studies, final deliverables, demonstrations
- **Required elements**: Clear deliverable, creation date, author/creator

```typescript
// CreativeWork implementation example
{
  "@type": "CreativeWork",
  "name": "E-commerce Dashboard Design",
  "creator": { "@type": "Person", "name": "..." },
  "dateCreated": "2024-09-15",
  "genre": "UI/UX Design",
  "material": "Figma, React, TypeScript"
}
```

## Content Structure Requirements

### Essential Metadata
- **Title**: SEO-optimized with primary keywords (50-60 characters)
- **Description**: Compelling summary with secondary keywords (150-160 characters)
- **Creation/Publication dates**: ISO 8601 format for structured data
- **Author/Creator information**: Person or Organization schema
- **Categories/Tags**: Hierarchical taxonomy for content organization
- **URL slug**: Descriptive, keyword-rich, kebab-case format

### Content Hierarchy
```
1. Hero Section
   - Project title
   - Brief description (1-2 sentences)
   - Primary image/thumbnail
   - Quick metadata (date, type, technologies)

2. Project Overview
   - Detailed description
   - Context and objectives
   - Key challenges addressed

3. Implementation Details
   - Technical approach (HowTo) OR Final outcome (CreativeWork)
   - Visual assets and demonstrations
   - Code snippets or design artifacts

4. Results and Impact
   - Metrics and achievements
   - User feedback or testimonials
   - Performance improvements

5. Related Works
   - Cross-linked similar projects
   - Technology-based groupings
   - Chronological navigation
```

## Image and Media Specifications

### Image Requirements
- **Hero image**: 1200x630px (Open Graph optimized)
- **Thumbnail**: 400x300px (4:3 aspect ratio)
- **Gallery images**: 800x600px minimum, maintain aspect ratio
- **Formats**: WebP primary, PNG/JPG fallbacks
- **Optimization**: < 100KB per image, progressive loading
- **Alt text**: Descriptive, keyword-relevant, < 125 characters

### Image Schema Integration
```typescript
{
  "@type": "ImageObject",
  "url": "https://example.com/project-hero.webp",
  "width": 1200,
  "height": 630,
  "caption": "Dashboard interface showing user analytics",
  "contentUrl": "https://example.com/project-hero.webp",
  "embedUrl": "https://example.com/embed/project-hero"
}
```

### Video/Demo Requirements
- **Format**: MP4 with H.264 encoding
- **Duration**: 30-120 seconds for demos
- **Resolution**: 1920x1080 maximum
- **Autoplay**: Muted, with play controls
- **Captions**: Required for accessibility

## Performance Metrics Integration

### Core KPIs
```typescript
interface WorkPageMetrics {
  // Engagement metrics
  viewDuration: number;      // Time spent on page
  scrollDepth: number;       // Percentage scrolled
  imageViews: number;        // Gallery engagement
  demoInteractions: number;  // Video/demo plays

  // SEO metrics
  organicTraffic: number;    // Search engine referrals
  clickThroughRate: number;  // From search results
  bounceRate: number;        // Single-page sessions

  // Conversion metrics
  contactClicks: number;     // CTA interactions
  portfolioDownloads: number; // Asset downloads
  externalLinkClicks: number; // Related work visits
}
```

### Measurement Implementation
- **Page view tracking**: Automatic on load with referrer analysis
- **Scroll tracking**: 25%, 50%, 75%, 100% milestones
- **Click tracking**: All CTA buttons, external links, image gallery
- **Time-based events**: 30s, 60s, 120s engagement markers
- **UTM parameter capture**: Campaign attribution and source tracking

### Analytics Integration
```javascript
// Phase 1.2 measurement snippet integration
pSEO.init({
  provider: 'ga4',
  siteId: 'GA_MEASUREMENT_ID',
  customDimensions: {
    projectType: 'creative-work', // or 'how-to'
    technology: ['React', 'TypeScript'],
    category: 'Web Development'
  }
});

// Track specific work page interactions
pSEO.trackEvent('project_demo_play', {
  projectId: 'ecommerce-dashboard',
  demoType: 'video'
});
```

## Canonical URL Strategy

### URL Structure
```
/work/{category}/{project-slug}

Examples:
/work/web-development/react-component-library
/work/ui-design/ecommerce-dashboard
/work/mobile-app/fitness-tracker-ios
```

### Canonical Implementation
- **Primary canonical**: Self-referencing for original content
- **Cross-platform**: Unified URLs across staging/production
- **Parameter handling**: Ignore tracking parameters in canonical
- **Duplicate content**: Use canonical to consolidate similar projects

### Sitemap Integration
```xml
<url>
  <loc>https://example.com/work/web-development/react-component-library</loc>
  <lastmod>2024-09-15T10:30:00Z</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
  <image:image>
    <image:loc>https://example.com/images/react-library-hero.webp</image:loc>
    <image:caption>React Component Library Architecture</image:caption>
  </image:image>
</url>
```

## Cross-linking Between Works

### Related Work Logic
```typescript
interface RelatedWorkCriteria {
  // Primary relationships
  sameTechnology: string[];     // Shared tech stack
  sameCategory: string;         // Same work category
  timeProximity: number;        // Within 6 months

  // Secondary relationships
  similarComplexity: string;    // Beginner/Intermediate/Advanced
  sharedTools: string[];        // Common tools/frameworks
  relatedSkills: string[];      // Overlapping competencies
}
```

### Navigation Patterns
- **Previous/Next**: Chronological project sequence
- **Technology clusters**: Group by React, Vue, Python, etc.
- **Category browsing**: Web dev, design, mobile, etc.
- **Complexity progression**: Beginner → Advanced pathways
- **Featured collections**: "Best of 2024", "Most Popular", etc.

### Internal Linking Strategy
- **Contextual links**: Embedded within project descriptions
- **Footer recommendations**: 3-4 related projects per page
- **Breadcrumb navigation**: Category → Subcategory → Project
- **Tag-based discovery**: Multi-tag intersection browsing

## Technical Requirements

### Framework Integration
- **Next.js compatibility**: SSR/SSG with dynamic metadata
- **React components**: Reusable work page templates
- **TypeScript support**: Type-safe schema generation
- **CSS-in-JS**: Styled-components or CSS modules
- **Responsive design**: Mobile-first, progressive enhancement

### Performance Targets
- **Core Web Vitals**:
  - LCP: < 2.5s (hero image optimized)
  - FID: < 100ms (minimal JavaScript)
  - CLS: < 0.1 (fixed image dimensions)
- **Page Speed**: > 90 Lighthouse score
- **Bundle size**: < 200KB total JavaScript
- **Time to Interactive**: < 3s on 3G networks

### SEO Technical Requirements
- **Meta tags**: Open Graph, Twitter Cards, LinkedIn
- **Structured data**: JSON-LD injection with validation
- **Schema validation**: Rich Results Test compliance
- **Accessibility**: WCAG 2.1 AA compliance
- **Internationalization**: lang attributes, hreflang support

### Phase 1.2 Integration Points
- **Edge Worker**: Sitemap generation from url_index table
- **D1 Database**: Project metadata and analytics storage
- **KV Storage**: Cache frequently accessed work listings
- **Revalidation**: On-demand ISR for updated projects
- **Measurement**: Event tracking to D1 events table

## Implementation Notes

### Content Management
- **Static generation**: Pre-build all work pages for optimal performance
- **Incremental updates**: ISR for new projects without full rebuild
- **Preview mode**: Draft project review before publication
- **Version control**: Git-based content with automatic deployments

### Quality Assurance
- **Schema validation**: Automated testing with Google's tools
- **Image optimization**: Automated WebP conversion and sizing
- **Performance monitoring**: Continuous Core Web Vitals tracking
- **SEO auditing**: Monthly comprehensive SEO health checks

This specification provides the foundation for implementing high-performance, SEO-optimized work/portfolio pages that integrate seamlessly with the programmatic SEO infrastructure and Phase 1.2 edge deployment strategy.