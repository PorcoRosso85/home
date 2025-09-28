/**
 * JSON-LD Collection Generator
 * Generates schema.org compliant Collection and ItemList structured data
 * Optimized for programmatic SEO galleries and listings
 */

// Base types for schema.org compliance
type SchemaContextType = 'https://schema.org';
type CollectionType = 'Collection' | 'ItemList';

// Core Collection/ItemList properties
type CollectionProperties = {
  '@context': SchemaContextType;
  '@type': CollectionType;
  name: string;
  description?: string;
  url?: string;
  identifier?: string;
  numberOfItems?: number;
  itemListElement?: ListItem[];
  hasPart?: Thing[];
  about?: Thing;
  creator?: PersonOrOrganization;
  author?: PersonOrOrganization;
  publisher?: PersonOrOrganization;
  dateCreated?: string;
  dateModified?: string;
  datePublished?: string;
  keywords?: string | string[];
  image?: ImageObject;
  thumbnailUrl?: string;
  isAccessibleForFree?: boolean;
  license?: string;
  copyrightHolder?: PersonOrOrganization;
  copyrightYear?: number;
  inLanguage?: string;
  audience?: Audience;
  genre?: string;
  temporalCoverage?: string;
  spatialCoverage?: Place;
  isPartOf?: Thing;
  mainEntity?: Thing;
  mentions?: Thing[];
};

// Supporting types
type ListItem = {
  '@type': 'ListItem';
  position: number;
  item: Thing | string;
  name?: string;
  description?: string;
  image?: string;
  url?: string;
};

type Thing = {
  '@type': string;
  '@id'?: string;
  name: string;
  description?: string;
  url?: string;
  image?: string;
  identifier?: string;
  sameAs?: string[];
  additionalType?: string;
};

type PersonOrOrganization = Person | Organization;

type Person = {
  '@type': 'Person';
  name: string;
  url?: string;
  image?: string;
  sameAs?: string[];
  identifier?: string;
};

type Organization = {
  '@type': 'Organization';
  name: string;
  url?: string;
  logo?: string;
  sameAs?: string[];
  identifier?: string;
};

type ImageObject = {
  '@type': 'ImageObject';
  url: string;
  width?: number;
  height?: number;
  caption?: string;
  description?: string;
};

type Audience = {
  '@type': 'Audience' | 'PeopleAudience' | 'BusinessAudience';
  audienceType?: string;
  name?: string;
  description?: string;
};

type Place = {
  '@type': 'Place';
  name: string;
  address?: string;
  geo?: {
    '@type': 'GeoCoordinates';
    latitude: number;
    longitude: number;
  };
};

// Input data structures
type CollectionInput = {
  type?: 'Collection' | 'ItemList';
  name: string;
  description?: string;
  url?: string;
  identifier?: string;
  items?: CollectionItemInput[];
  about?: ThingInput;
  creator?: PersonOrOrganizationInput;
  author?: PersonOrOrganizationInput;
  publisher?: PersonOrOrganizationInput;
  dateCreated?: string;
  dateModified?: string;
  datePublished?: string;
  keywords?: string | string[];
  image?: ImageObjectInput;
  thumbnailUrl?: string;
  isAccessibleForFree?: boolean;
  license?: string;
  copyrightHolder?: PersonOrOrganizationInput;
  copyrightYear?: number;
  inLanguage?: string;
  audience?: AudienceInput;
  genre?: string;
  temporalCoverage?: string;
  spatialCoverage?: PlaceInput;
  isPartOf?: ThingInput;
  mainEntity?: ThingInput;
  mentions?: ThingInput[];
};

type CollectionItemInput = {
  type: string;
  name: string;
  description?: string;
  url?: string;
  image?: string;
  identifier?: string;
  sameAs?: string[];
  additionalType?: string;
  id?: string;
};

type ThingInput = {
  type: string;
  name: string;
  description?: string;
  url?: string;
  image?: string;
  identifier?: string;
  sameAs?: string[];
  additionalType?: string;
  id?: string;
};

type PersonOrOrganizationInput = {
  type: 'Person' | 'Organization';
  name: string;
  url?: string;
  image?: string;
  sameAs?: string[];
  identifier?: string;
};

type ImageObjectInput = {
  url: string;
  width?: number;
  height?: number;
  caption?: string;
  description?: string;
};

type AudienceInput = {
  type?: 'Audience' | 'PeopleAudience' | 'BusinessAudience';
  audienceType?: string;
  name?: string;
  description?: string;
};

type PlaceInput = {
  name: string;
  address?: string;
  latitude?: number;
  longitude?: number;
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

const isValidLanguageCode = (code: string): boolean => {
  // Simple validation for ISO 639-1 language codes
  return /^[a-z]{2}(-[A-Z]{2})?$/.test(code);
};

// Transform functions
const transformThing = (input: ThingInput): Thing => {
  const thing: Thing = {
    '@type': input.type,
    name: input.name,
  };

  if (input.id) thing['@id'] = input.id;
  if (input.description) thing.description = input.description;
  if (input.url && isValidUrl(input.url)) thing.url = input.url;
  if (input.image && isValidUrl(input.image)) thing.image = input.image;
  if (input.identifier) thing.identifier = input.identifier;
  if (input.sameAs) thing.sameAs = input.sameAs.filter(isValidUrl);
  if (input.additionalType) thing.additionalType = input.additionalType;

  return thing;
};

const transformPersonOrOrganization = (input: PersonOrOrganizationInput): PersonOrOrganization => {
  const base = {
    '@type': input.type as 'Person' | 'Organization',
    name: input.name,
  };

  if (input.identifier) (base as PersonOrOrganization).identifier = input.identifier;
  if (input.sameAs) (base as PersonOrOrganization).sameAs = input.sameAs.filter(isValidUrl);

  if (input.url && isValidUrl(input.url)) {
    if (input.type === 'Person') {
      return { ...base, url: input.url, image: input.image } as Person;
    } else {
      return { ...base, url: input.url, logo: input.image } as Organization;
    }
  }

  return base as PersonOrOrganization;
};

const transformImageObject = (input: ImageObjectInput): ImageObject => {
  const image: ImageObject = {
    '@type': 'ImageObject',
    url: input.url,
  };

  if (input.width && input.width > 0) image.width = input.width;
  if (input.height && input.height > 0) image.height = input.height;
  if (input.caption) image.caption = input.caption;
  if (input.description) image.description = input.description;

  return image;
};

const transformAudience = (input: AudienceInput): Audience => {
  return {
    '@type': input.type || 'Audience',
    ...(input.audienceType && { audienceType: input.audienceType }),
    ...(input.name && { name: input.name }),
    ...(input.description && { description: input.description }),
  };
};

const transformPlace = (input: PlaceInput): Place => {
  const place: Place = {
    '@type': 'Place',
    name: input.name,
  };

  if (input.address) place.address = input.address;
  if (input.latitude && input.longitude) {
    place.geo = {
      '@type': 'GeoCoordinates',
      latitude: input.latitude,
      longitude: input.longitude,
    };
  }

  return place;
};

// Main collection generator
export const createCollection = (input: CollectionInput): CollectionProperties => {
  // Validate required fields
  if (!input.name) {
    throw new Error('Collection name is required');
  }

  // Validate optional fields
  if (input.url && !isValidUrl(input.url)) {
    throw new Error('Collection URL must be valid');
  }

  if (input.license && !isValidUrl(input.license)) {
    throw new Error('License must be a valid URL');
  }

  if (input.thumbnailUrl && !isValidUrl(input.thumbnailUrl)) {
    throw new Error('Thumbnail URL must be valid');
  }

  if (input.dateCreated && !isValidDate(input.dateCreated)) {
    throw new Error('dateCreated must be in ISO 8601 format');
  }

  if (input.dateModified && !isValidDate(input.dateModified)) {
    throw new Error('dateModified must be in ISO 8601 format');
  }

  if (input.datePublished && !isValidDate(input.datePublished)) {
    throw new Error('datePublished must be in ISO 8601 format');
  }

  if (input.inLanguage && !isValidLanguageCode(input.inLanguage)) {
    throw new Error('inLanguage must be a valid language code (e.g., "en", "en-US")');
  }

  // Build the collection object
  const collection: CollectionProperties = {
    '@context': 'https://schema.org',
    '@type': input.type || 'ItemList',
    name: input.name,
  };

  // Add optional properties
  if (input.description) collection.description = input.description;
  if (input.url) collection.url = input.url;
  if (input.identifier) collection.identifier = input.identifier;
  if (input.thumbnailUrl) collection.thumbnailUrl = input.thumbnailUrl;
  if (input.keywords) collection.keywords = input.keywords;
  if (input.license) collection.license = input.license;
  if (input.genre) collection.genre = input.genre;
  if (input.temporalCoverage) collection.temporalCoverage = input.temporalCoverage;
  if (input.inLanguage) collection.inLanguage = input.inLanguage;
  if (input.dateCreated) collection.dateCreated = input.dateCreated;
  if (input.dateModified) collection.dateModified = input.dateModified;
  if (input.datePublished) collection.datePublished = input.datePublished;
  if (typeof input.isAccessibleForFree === 'boolean') {
    collection.isAccessibleForFree = input.isAccessibleForFree;
  }
  if (input.copyrightYear && input.copyrightYear > 0) {
    collection.copyrightYear = input.copyrightYear;
  }

  // Transform complex objects
  if (input.image) {
    collection.image = transformImageObject(input.image);
  }
  if (input.creator) {
    collection.creator = transformPersonOrOrganization(input.creator);
  }
  if (input.author) {
    collection.author = transformPersonOrOrganization(input.author);
  }
  if (input.publisher) {
    collection.publisher = transformPersonOrOrganization(input.publisher);
  }
  if (input.copyrightHolder) {
    collection.copyrightHolder = transformPersonOrOrganization(input.copyrightHolder);
  }
  if (input.about) {
    collection.about = transformThing(input.about);
  }
  if (input.audience) {
    collection.audience = transformAudience(input.audience);
  }
  if (input.spatialCoverage) {
    collection.spatialCoverage = transformPlace(input.spatialCoverage);
  }
  if (input.isPartOf) {
    collection.isPartOf = transformThing(input.isPartOf);
  }
  if (input.mainEntity) {
    collection.mainEntity = transformThing(input.mainEntity);
  }
  if (input.mentions) {
    collection.mentions = input.mentions.map(transformThing);
  }

  // Handle items
  if (input.items && input.items.length > 0) {
    collection.numberOfItems = input.items.length;

    if (input.type === 'ItemList' || !input.type) {
      // For ItemList, use itemListElement with position
      collection.itemListElement = input.items.map((item, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        item: transformThing(item),
        ...(item.name && { name: item.name }),
        ...(item.description && { description: item.description }),
        ...(item.image && isValidUrl(item.image) && { image: item.image }),
        ...(item.url && isValidUrl(item.url) && { url: item.url }),
      }));
    } else {
      // For Collection, use hasPart
      collection.hasPart = input.items.map(transformThing);
    }
  }

  return collection;
};

// Helper functions for common collection types
export const createGalleryCollection = (
  name: string,
  items: Array<{
    name: string;
    image: string;
    url?: string;
    description?: string;
  }>,
  options: {
    description?: string;
    url?: string;
    creator?: string;
    creatorUrl?: string;
  } = {}
): CollectionProperties => {
  return createCollection({
    type: 'ItemList',
    name,
    description: options.description,
    url: options.url,
    isAccessibleForFree: true,
    items: items.map(item => ({
      type: 'ImageObject',
      name: item.name,
      description: item.description,
      url: item.url,
      image: item.image,
    })),
    ...(options.creator && {
      creator: {
        type: 'Person',
        name: options.creator,
        url: options.creatorUrl,
      },
    }),
  });
};

export const createProductCollection = (
  name: string,
  products: Array<{
    name: string;
    url: string;
    image?: string;
    description?: string;
    price?: string;
    brand?: string;
  }>,
  options: {
    description?: string;
    url?: string;
    publisher?: string;
    publisherUrl?: string;
  } = {}
): CollectionProperties => {
  return createCollection({
    type: 'ItemList',
    name,
    description: options.description,
    url: options.url,
    items: products.map(product => ({
      type: 'Product',
      name: product.name,
      url: product.url,
      image: product.image,
      description: product.description,
      additionalType: product.brand ? `Brand: ${product.brand}` : undefined,
    })),
    ...(options.publisher && {
      publisher: {
        type: 'Organization',
        name: options.publisher,
        url: options.publisherUrl,
      },
    }),
  });
};

export const createArticleCollection = (
  name: string,
  articles: Array<{
    name: string;
    url: string;
    description?: string;
    author?: string;
    publishDate?: string;
  }>,
  options: {
    description?: string;
    url?: string;
    publisher?: string;
    publisherUrl?: string;
  } = {}
): CollectionProperties => {
  return createCollection({
    type: 'ItemList',
    name,
    description: options.description,
    url: options.url,
    items: articles.map(article => ({
      type: 'Article',
      name: article.name,
      url: article.url,
      description: article.description,
      additionalType: article.author ? `Author: ${article.author}` : undefined,
    })),
    ...(options.publisher && {
      publisher: {
        type: 'Organization',
        name: options.publisher,
        url: options.publisherUrl,
      },
    }),
  });
};

// Export types for external use
export type {
  CollectionInput,
  CollectionProperties,
  CollectionItemInput,
  ListItem,
  Thing
};
