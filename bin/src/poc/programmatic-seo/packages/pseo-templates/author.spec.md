# Author/Profile Page UI Specification

## Purpose/Overview

This specification defines the UI and data requirements for author/profile pages in the programmatic SEO system. Author pages serve as authoritative identity hubs that establish credibility, showcase representative works, and provide comprehensive cross-linking to boost domain authority.

**Core Objectives:**
- Establish author authority and credibility through structured data
- Drive traffic through featured works and cross-linking
- Provide comprehensive identity verification via social media links
- Optimize for search engines with rich JSON-LD Person schema

## Person Schema Requirements

### Core JSON-LD Structure
```typescript
type AuthorPersonSchema = {
  '@context': 'https://schema.org';
  '@type': 'Person';
  '@id': string;                    // Canonical author identifier
  name: string;                     // Full display name
  url: string;                      // Canonical profile URL
  identifier: string | string[];    // Unique identifiers (ORCID, etc.)
  sameAs: string[];                 // Social media and external profile URLs
  image: ImageObject;               // Professional headshot/avatar
  description: string;              // Professional bio (160-320 characters)
  jobTitle?: string;                // Current role/position
  worksFor?: Organization;          // Current employer/affiliation
  alumniOf?: Organization[];        // Educational institutions
  knowsAbout: string | string[];    // Areas of expertise/topics
  mainEntityOfPage: string;         // This profile page URL
  author?: CreativeWork[];          // Featured works (3-10 items)
  creator?: CreativeWork[];         // Created works
  contributor?: CreativeWork[];     // Contributed works
}
```

### Required Properties
- `@id`: Unique identifier (e.g., `https://domain.com/author/john-doe#person`)
- `name`: Author's full name
- `url`: Canonical profile page URL
- `sameAs`: Minimum 2-3 verified social profiles
- `image`: High-quality profile image (minimum 400x400px)
- `description`: SEO-optimized bio (target 200-250 characters)

### Optional Properties
- `identifier`: ORCID, Google Scholar ID, or other academic identifiers
- `jobTitle`, `worksFor`: Professional context
- `knowsAbout`: Topic expertise for topical authority

## Featured Works Selection (3-10 items)

### Selection Criteria
1. **Performance Priority**: Highest traffic/engagement works first
2. **Topical Diversity**: Represent different expertise areas
3. **Recency Balance**: Mix of recent and evergreen content
4. **Quality Threshold**: Only include high-performing, well-optimized content

### Work Representation
```typescript
type FeaturedWork = {
  '@type': 'Article' | 'BlogPosting' | 'CreativeWork';
  '@id': string;                    // Canonical work URL
  headline: string;                 // Title
  description: string;              // Meta description or excerpt
  url: string;                      // Full URL
  datePublished: string;            // ISO 8601 date
  image?: ImageObject;              // Featured image
  keywords?: string[];              // Primary topics
  wordCount?: number;               // Article length
}
```

### Display Requirements
- **Grid Layout**: 3-column grid on desktop, 1-column on mobile
- **Card Format**: Image, title, excerpt, publish date, read time
- **Call-to-Action**: Clear "Read More" or "View Article" buttons
- **Performance Data**: Optional view count or engagement metrics

## Identity and Verification (SameAs, identifiers)

### Social Media Requirements
**Minimum Required (2-3 platforms):**
- LinkedIn (professional credibility)
- Twitter/X (thought leadership)
- One additional platform relevant to niche (GitHub, Medium, etc.)

**Additional Platforms (as applicable):**
- Instagram (visual content creators)
- YouTube (video content)
- TikTok (short-form content)
- GitHub (technical authors)
- Medium/Substack (content platforms)
- ORCID (academic authors)

### Verification Strategy
1. **Bio Consistency**: Ensure bio and expertise align across platforms
2. **Cross-References**: Include website URL in social media bios
3. **Posting Activity**: Regular posting demonstrates active presence
4. **Professional Imagery**: Consistent profile photos across platforms

### Implementation
```html
<!-- JSON-LD sameAs array -->
"sameAs": [
  "https://linkedin.com/in/username",
  "https://twitter.com/username",
  "https://github.com/username"
]

<!-- Visible social links section -->
<section class="author-social">
  <h3>Connect with [Author Name]</h3>
  <ul class="social-links">
    <li><a href="linkedin-url" rel="noopener">LinkedIn</a></li>
    <li><a href="twitter-url" rel="noopener">Twitter</a></li>
    <li><a href="github-url" rel="noopener">GitHub</a></li>
  </ul>
</section>
```

## Social Proof Strategy

### Credibility Indicators (in order of priority)
1. **Professional Credentials**: Job title, company, education
2. **Publication Count**: Total articles/works published
3. **Social Following**: Aggregate follower count (if significant)
4. **External Mentions**: Media appearances, quotes, citations
5. **Awards/Recognition**: Industry awards, certifications

### Placement Guidelines
- **Header Section**: Job title and current affiliation prominently displayed
- **Bio Section**: Credentials and expertise woven into narrative
- **Sidebar/Stats**: Publication count, years of experience
- **Footer**: Awards, certifications, media mentions

### Content Examples
```html
<div class="author-credentials">
  <h2>Senior Data Scientist at TechCorp</h2>
  <p>10+ years experience • 50+ published articles • PhD Computer Science</p>
</div>

<div class="author-stats">
  <span>📝 50+ Articles</span>
  <span>🎓 PhD Computer Science</span>
  <span>🏆 Industry Award Winner</span>
</div>
```

## Cross-linking Architecture

### Internal Link Strategy
1. **Topic Clusters**: Link to related articles on similar topics
2. **Author Archive**: Comprehensive list of all author's content
3. **Category Pages**: Link to topic/category pages author contributes to
4. **Related Authors**: Cross-link to collaborators or similar experts

### External Link Strategy
1. **Authority Sites**: Link to author's profiles on high-authority platforms
2. **Portfolio/Work**: Link to external projects, publications
3. **Citations**: Link to academic papers, research (with rel="nofollow" if needed)

### SEO Implementation
```html
<!-- Topic cluster navigation -->
<nav class="topic-clusters">
  <h3>Explore [Author]'s expertise in:</h3>
  <ul>
    <li><a href="/category/data-science">Data Science (15 articles)</a></li>
    <li><a href="/category/machine-learning">Machine Learning (12 articles)</a></li>
  </ul>
</nav>

<!-- Related authors -->
<section class="related-authors">
  <h3>You might also like</h3>
  <!-- Other expert authors in similar topics -->
</section>
```

## Biography and Content Guidelines

### Bio Structure (200-250 characters for SEO)
1. **Opening**: Name and primary expertise/role
2. **Credentials**: Key qualifications or achievements
3. **Current Focus**: What they're working on or known for
4. **Call-to-Action**: How to connect or follow their work

### Content Tone
- **Professional but approachable**
- **Third-person perspective** for credibility
- **Action-oriented language** (creates, develops, leads)
- **Keyword-rich** without over-optimization

### Example Bio
```
John Doe is a Senior Data Scientist at TechCorp specializing in machine learning and AI ethics. With a PhD in Computer Science and 10+ years of industry experience, he has published 50+ articles on data science best practices. John regularly speaks at tech conferences and contributes to open-source ML frameworks.
```

## Technical Requirements

### Performance Standards
- **Page Load Time**: < 2 seconds
- **Core Web Vitals**: LCP < 2.5s, FID < 100ms, CLS < 0.1
- **Image Optimization**: WebP format, responsive sizing
- **Lazy Loading**: Below-the-fold content and images

### SEO Requirements
- **Meta Title**: "[Author Name] - [Primary Expertise] | [Site Name]" (< 60 chars)
- **Meta Description**: Bio summary with primary keywords (150-160 chars)
- **Canonical URL**: Properly set canonical tag
- **Open Graph**: Complete OG tags for social sharing
- **Schema Markup**: Valid JSON-LD Person schema

### Accessibility
- **WCAG 2.1 AA compliance**
- **Alt text** for all images
- **Semantic HTML** structure
- **Keyboard navigation** support
- **Screen reader** compatibility

### Mobile Optimization
- **Responsive design** (mobile-first approach)
- **Touch-friendly** navigation
- **Readable typography** (minimum 16px font size)
- **Optimized images** for different screen densities

### Analytics Integration
- **Event tracking** for social link clicks
- **Scroll depth** measurement
- **Featured work** click tracking
- **Social sharing** monitoring

---

**Implementation Priority**: This specification supports Phase 1.2 implementation with focus on JSON-LD Person schema, featured works integration, and cross-linking architecture for maximum SEO impact.
