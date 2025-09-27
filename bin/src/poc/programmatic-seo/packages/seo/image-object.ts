/**
 * JSON-LD Image Object Generator
 * Generates schema.org compliant ImageObject structured data
 * Optimized for Google Rich Results compliance
 */

// Base types for schema.org compliance
type SchemaContextType = 'https://schema.org';
type ImageObjectType = 'ImageObject';

// Core ImageObject properties based on schema.org specification
type ImageObjectProperties = {
  '@context': SchemaContextType;
  '@type': ImageObjectType;
  url: string;
  width?: number;
  height?: number;
  caption?: string;
  description?: string;
  name?: string;
  alternateName?: string;
  author?: PersonOrOrganization;
  creator?: PersonOrOrganization;
  copyrightHolder?: PersonOrOrganization;
  copyrightYear?: number;
  license?: string;
  acquireLicensePage?: string;
  creditText?: string;
  contentUrl?: string;
  thumbnailUrl?: string;
  encodingFormat?: string; // MIME type
  fileFormat?: string; // File extension
  uploadDate?: string; // ISO 8601 format
  keywords?: string | string[];
  about?: Thing;
  representativeOfPage?: boolean;
  isAccessibleForFree?: boolean;
  usageInfo?: string;
  exifData?: ExifData;
};

// Supporting types
type PersonOrOrganization = Person | Organization;

type Person = {
  '@type': 'Person';
  name: string;
  url?: string;
  image?: string;
  sameAs?: string[];
};

type Organization = {
  '@type': 'Organization';
  name: string;
  url?: string;
  logo?: string;
  sameAs?: string[];
};

type Thing = {
  '@type': string;
  name: string;
  description?: string;
  url?: string;
};

type ExifData = {
  exposureTime?: string;
  fNumber?: string;
  photographicSensitivity?: number;
  focalLength?: string;
  lens?: string;
  flash?: string;
  colorSpace?: string;
  whiteBalance?: string;
  gpsLatitude?: number;
  gpsLongitude?: number;
  gpsAltitude?: number;
};

// Input data structure for image generation
type ImageObjectInput = {
  url: string;
  width?: number;
  height?: number;
  caption?: string;
  description?: string;
  name?: string;
  alternateName?: string;
  author?: {
    type: 'Person' | 'Organization';
    name: string;
    url?: string;
    image?: string;
    sameAs?: string[];
  };
  creator?: {
    type: 'Person' | 'Organization';
    name: string;
    url?: string;
    image?: string;
    sameAs?: string[];
  };
  copyrightHolder?: {
    type: 'Person' | 'Organization';
    name: string;
    url?: string;
    image?: string;
    sameAs?: string[];
  };
  copyrightYear?: number;
  license?: string;
  acquireLicensePage?: string;
  creditText?: string;
  contentUrl?: string;
  thumbnailUrl?: string;
  encodingFormat?: string;
  fileFormat?: string;
  uploadDate?: string;
  keywords?: string | string[];
  about?: {
    type: string;
    name: string;
    description?: string;
    url?: string;
  };
  representativeOfPage?: boolean;
  isAccessibleForFree?: boolean;
  usageInfo?: string;
  exifData?: ExifData;
};

// Validation functions
const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

const isValidDate = (dateString: string): boolean => {
  const date = new Date(dateString);
  return !isNaN(date.getTime()) && dateString.includes('T');
};

const isValidMimeType = (mimeType: string): boolean => {
  return /^image\/(jpeg|jpg|png|webp|gif|svg\+xml|bmp|tiff)$/i.test(mimeType);
};

// Transform input person/organization to schema.org format
const transformPersonOrOrganization = (input: {
  type: 'Person' | 'Organization';
  name: string;
  url?: string;
  image?: string;
  sameAs?: string[];
}): PersonOrOrganization => {
  const base = {
    '@type': input.type as 'Person' | 'Organization',
    name: input.name,
  };

  if (input.url && isValidUrl(input.url)) {
    if (input.type === 'Person') {
      return { ...base, url: input.url, image: input.image, sameAs: input.sameAs } as Person;
    } else {
      return { ...base, url: input.url, logo: input.image, sameAs: input.sameAs } as Organization;
    }
  }

  return base as PersonOrOrganization;
};

// Main image object generator
export const createImageObject = (input: ImageObjectInput): ImageObjectProperties => {
  // Validate required fields
  if (!input.url || !isValidUrl(input.url)) {
    throw new Error('Valid image URL is required');
  }

  // Validate optional fields
  if (input.contentUrl && !isValidUrl(input.contentUrl)) {
    throw new Error('contentUrl must be a valid URL');
  }

  if (input.thumbnailUrl && !isValidUrl(input.thumbnailUrl)) {
    throw new Error('thumbnailUrl must be a valid URL');
  }

  if (input.license && !isValidUrl(input.license)) {
    throw new Error('license must be a valid URL');
  }

  if (input.acquireLicensePage && !isValidUrl(input.acquireLicensePage)) {
    throw new Error('acquireLicensePage must be a valid URL');
  }

  if (input.uploadDate && !isValidDate(input.uploadDate)) {
    throw new Error('uploadDate must be in ISO 8601 format (YYYY-MM-DDTHH:mm:ss)');
  }

  if (input.encodingFormat && !isValidMimeType(input.encodingFormat)) {
    throw new Error('encodingFormat must be a valid image MIME type');
  }

  // Build the image object
  const imageObject: ImageObjectProperties = {
    '@context': 'https://schema.org',
    '@type': 'ImageObject',
    url: input.url,
  };

  // Add optional properties with validation
  if (input.width && input.width > 0) imageObject.width = input.width;
  if (input.height && input.height > 0) imageObject.height = input.height;
  if (input.caption) imageObject.caption = input.caption;
  if (input.description) imageObject.description = input.description;
  if (input.name) imageObject.name = input.name;
  if (input.alternateName) imageObject.alternateName = input.alternateName;
  if (input.contentUrl) imageObject.contentUrl = input.contentUrl;
  if (input.thumbnailUrl) imageObject.thumbnailUrl = input.thumbnailUrl;
  if (input.encodingFormat) imageObject.encodingFormat = input.encodingFormat;
  if (input.fileFormat) imageObject.fileFormat = input.fileFormat;
  if (input.uploadDate) imageObject.uploadDate = input.uploadDate;
  if (input.license) imageObject.license = input.license;
  if (input.acquireLicensePage) imageObject.acquireLicensePage = input.acquireLicensePage;
  if (input.creditText) imageObject.creditText = input.creditText;
  if (input.usageInfo) imageObject.usageInfo = input.usageInfo;
  if (input.keywords) imageObject.keywords = input.keywords;
  if (typeof input.representativeOfPage === 'boolean') {
    imageObject.representativeOfPage = input.representativeOfPage;
  }
  if (typeof input.isAccessibleForFree === 'boolean') {
    imageObject.isAccessibleForFree = input.isAccessibleForFree;
  }
  if (input.copyrightYear && input.copyrightYear > 0) {
    imageObject.copyrightYear = input.copyrightYear;
  }

  // Transform complex objects
  if (input.author) {
    imageObject.author = transformPersonOrOrganization(input.author);
  }
  if (input.creator) {
    imageObject.creator = transformPersonOrOrganization(input.creator);
  }
  if (input.copyrightHolder) {
    imageObject.copyrightHolder = transformPersonOrOrganization(input.copyrightHolder);
  }
  if (input.about) {
    imageObject.about = {
      '@type': input.about.type,
      name: input.about.name,
      ...(input.about.description && { description: input.about.description }),
      ...(input.about.url && isValidUrl(input.about.url) && { url: input.about.url }),
    };
  }
  if (input.exifData) {
    imageObject.exifData = input.exifData;
  }

  return imageObject;
};

// Helper function for common gallery image
export const createGalleryImage = (
  url: string,
  caption: string,
  options: {
    width?: number;
    height?: number;
    thumbnailUrl?: string;
    author?: string;
    authorUrl?: string;
  } = {}
): ImageObjectProperties => {
  const { author, authorUrl, ...restOptions } = options;
  return createImageObject({
    url,
    caption,
    name: caption,
    representativeOfPage: false,
    isAccessibleForFree: true,
    ...restOptions,
    ...(author && {
      author: {
        type: 'Person',
        name: author,
        url: authorUrl,
      },
    }),
  });
};

// Helper function for hero/featured image
export const createHeroImage = (
  url: string,
  description: string,
  options: {
    width?: number;
    height?: number;
    author?: string;
    authorUrl?: string;
  } = {}
): ImageObjectProperties => {
  const { author, authorUrl, ...restOptions } = options;
  return createImageObject({
    url,
    description,
    name: description,
    representativeOfPage: true,
    isAccessibleForFree: true,
    ...restOptions,
    ...(author && {
      author: {
        type: 'Person',
        name: author,
        url: authorUrl,
      },
    }),
  });
};

// Export types for external use
export type { ImageObjectInput, ImageObjectProperties, ExifData };