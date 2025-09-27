/**
 * JSON-LD HowTo Generator
 * Generates schema.org compliant HowTo structured data
 * Optimized for step-by-step guides and tutorials
 */

// Base types for schema.org compliance
type SchemaContextType = 'https://schema.org';
type HowToType = 'HowTo';

// Core HowTo properties
type HowToProperties = {
  '@context': SchemaContextType;
  '@type': HowToType;
  name: string;
  description?: string;
  image?: ImageObject | ImageObject[] | string | string[];
  step: HowToStep[];
  totalTime?: string; // ISO 8601 duration format
  prepTime?: string; // ISO 8601 duration format
  performTime?: string; // ISO 8601 duration format
  yield?: string | number;
  estimatedCost?: MonetaryAmount;
  tool?: HowToTool[];
  supply?: HowToSupply[];
  author?: PersonOrOrganization;
  creator?: PersonOrOrganization;
  publisher?: PersonOrOrganization;
  dateCreated?: string;
  dateModified?: string;
  datePublished?: string;
  keywords?: string | string[];
  url?: string;
  identifier?: string;
  inLanguage?: string;
  audience?: Audience;
  about?: Thing;
  category?: string | Thing;
  difficulty?: string;
  isAccessibleForFree?: boolean;
  license?: string;
  copyrightHolder?: PersonOrOrganization;
  copyrightYear?: number;
  video?: VideoObject;
};

// Supporting types
type HowToStep = {
  '@type': 'HowToStep';
  name: string;
  text: string;
  url?: string;
  image?: ImageObject | string;
  video?: VideoObject;
  position?: number;
  tool?: HowToTool[];
  supply?: HowToSupply[];
};

type HowToTool = {
  '@type': 'HowToTool';
  name: string;
  description?: string;
  image?: string;
  url?: string;
  requiredQuantity?: QuantitativeValue;
};

type HowToSupply = {
  '@type': 'HowToSupply';
  name: string;
  description?: string;
  image?: string;
  url?: string;
  requiredQuantity?: QuantitativeValue;
  estimatedCost?: MonetaryAmount;
};

type ImageObject = {
  '@type': 'ImageObject';
  url: string;
  width?: number;
  height?: number;
  caption?: string;
  description?: string;
};

type VideoObject = {
  '@type': 'VideoObject';
  name: string;
  description?: string;
  thumbnailUrl: string;
  uploadDate?: string;
  duration?: string; // ISO 8601 duration format
  contentUrl?: string;
  embedUrl?: string;
  width?: number;
  height?: number;
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

type Thing = {
  '@type': string;
  name: string;
  description?: string;
  url?: string;
  image?: string;
};

type Audience = {
  '@type': 'Audience' | 'PeopleAudience' | 'BusinessAudience';
  audienceType?: string;
  name?: string;
  description?: string;
};

type MonetaryAmount = {
  '@type': 'MonetaryAmount';
  currency: string; // ISO 4217 currency code
  value: number;
};

type QuantitativeValue = {
  '@type': 'QuantitativeValue';
  value: number;
  unitText?: string;
  unitCode?: string; // UN/CEFACT Common Code
};

// Input data structures
type HowToInput = {
  name: string;
  description?: string;
  image?: ImageObjectInput | ImageObjectInput[] | string | string[];
  steps: HowToStepInput[];
  totalTime?: string;
  prepTime?: string;
  performTime?: string;
  yield?: string | number;
  estimatedCost?: MonetaryAmountInput;
  tools?: HowToToolInput[];
  supplies?: HowToSupplyInput[];
  author?: PersonOrOrganizationInput;
  creator?: PersonOrOrganizationInput;
  publisher?: PersonOrOrganizationInput;
  dateCreated?: string;
  dateModified?: string;
  datePublished?: string;
  keywords?: string | string[];
  url?: string;
  identifier?: string;
  inLanguage?: string;
  audience?: AudienceInput;
  about?: ThingInput;
  category?: string | ThingInput;
  difficulty?: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
  isAccessibleForFree?: boolean;
  license?: string;
  copyrightHolder?: PersonOrOrganizationInput;
  copyrightYear?: number;
  video?: VideoObjectInput;
};

type HowToStepInput = {
  name: string;
  text: string;
  url?: string;
  image?: ImageObjectInput | string;
  video?: VideoObjectInput;
  tools?: HowToToolInput[];
  supplies?: HowToSupplyInput[];
};

type HowToToolInput = {
  name: string;
  description?: string;
  image?: string;
  url?: string;
  requiredQuantity?: QuantitativeValueInput;
};

type HowToSupplyInput = {
  name: string;
  description?: string;
  image?: string;
  url?: string;
  requiredQuantity?: QuantitativeValueInput;
  estimatedCost?: MonetaryAmountInput;
};

type ImageObjectInput = {
  url: string;
  width?: number;
  height?: number;
  caption?: string;
  description?: string;
};

type VideoObjectInput = {
  name: string;
  description?: string;
  thumbnailUrl: string;
  uploadDate?: string;
  duration?: string;
  contentUrl?: string;
  embedUrl?: string;
  width?: number;
  height?: number;
};

type PersonOrOrganizationInput = {
  type: 'Person' | 'Organization';
  name: string;
  url?: string;
  image?: string;
  sameAs?: string[];
  identifier?: string;
};

type ThingInput = {
  type: string;
  name: string;
  description?: string;
  url?: string;
  image?: string;
};

type AudienceInput = {
  type?: 'Audience' | 'PeopleAudience' | 'BusinessAudience';
  audienceType?: string;
  name?: string;
  description?: string;
};

type MonetaryAmountInput = {
  currency: string;
  value: number;
};

type QuantitativeValueInput = {
  value: number;
  unitText?: string;
  unitCode?: string;
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

const isValidDuration = (duration: string): boolean => {
  // ISO 8601 duration format: P[n]Y[n]M[n]DT[n]H[n]M[n]S
  return /^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$/.test(duration);
};

const isValidLanguageCode = (code: string): boolean => {
  return /^[a-z]{2}(-[A-Z]{2})?$/.test(code);
};

const isValidCurrencyCode = (code: string): boolean => {
  // ISO 4217 currency codes are 3 uppercase letters
  return /^[A-Z]{3}$/.test(code);
};

// Transform functions
const transformImageObject = (input: ImageObjectInput | string): ImageObject | string => {
  if (typeof input === 'string') {
    return input;
  }

  return {
    '@type': 'ImageObject',
    url: input.url,
    ...(input.width && input.width > 0 && { width: input.width }),
    ...(input.height && input.height > 0 && { height: input.height }),
    ...(input.caption && { caption: input.caption }),
    ...(input.description && { description: input.description }),
  };
};

const transformVideoObject = (input: VideoObjectInput): VideoObject => {
  return {
    '@type': 'VideoObject',
    name: input.name,
    thumbnailUrl: input.thumbnailUrl,
    ...(input.description && { description: input.description }),
    ...(input.uploadDate && { uploadDate: input.uploadDate }),
    ...(input.duration && { duration: input.duration }),
    ...(input.contentUrl && { contentUrl: input.contentUrl }),
    ...(input.embedUrl && { embedUrl: input.embedUrl }),
    ...(input.width && input.width > 0 && { width: input.width }),
    ...(input.height && input.height > 0 && { height: input.height }),
  };
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

const transformQuantitativeValue = (input: QuantitativeValueInput): QuantitativeValue => {
  return {
    '@type': 'QuantitativeValue',
    value: input.value,
    ...(input.unitText && { unitText: input.unitText }),
    ...(input.unitCode && { unitCode: input.unitCode }),
  };
};

const transformMonetaryAmount = (input: MonetaryAmountInput): MonetaryAmount => {
  return {
    '@type': 'MonetaryAmount',
    currency: input.currency,
    value: input.value,
  };
};

const transformHowToTool = (input: HowToToolInput): HowToTool => {
  return {
    '@type': 'HowToTool',
    name: input.name,
    ...(input.description && { description: input.description }),
    ...(input.image && isValidUrl(input.image) && { image: input.image }),
    ...(input.url && isValidUrl(input.url) && { url: input.url }),
    ...(input.requiredQuantity && { requiredQuantity: transformQuantitativeValue(input.requiredQuantity) }),
  };
};

const transformHowToSupply = (input: HowToSupplyInput): HowToSupply => {
  return {
    '@type': 'HowToSupply',
    name: input.name,
    ...(input.description && { description: input.description }),
    ...(input.image && isValidUrl(input.image) && { image: input.image }),
    ...(input.url && isValidUrl(input.url) && { url: input.url }),
    ...(input.requiredQuantity && { requiredQuantity: transformQuantitativeValue(input.requiredQuantity) }),
    ...(input.estimatedCost && { estimatedCost: transformMonetaryAmount(input.estimatedCost) }),
  };
};

// Main HowTo generator
export const createHowTo = (input: HowToInput): HowToProperties => {
  // Validate required fields
  if (!input.name) {
    throw new Error('HowTo name is required');
  }

  if (!input.steps || input.steps.length === 0) {
    throw new Error('At least one step is required');
  }

  // Validate optional fields
  if (input.url && !isValidUrl(input.url)) {
    throw new Error('HowTo URL must be valid');
  }

  if (input.license && !isValidUrl(input.license)) {
    throw new Error('License must be a valid URL');
  }

  if (input.totalTime && !isValidDuration(input.totalTime)) {
    throw new Error('totalTime must be in ISO 8601 duration format (e.g., "PT30M" for 30 minutes)');
  }

  if (input.prepTime && !isValidDuration(input.prepTime)) {
    throw new Error('prepTime must be in ISO 8601 duration format');
  }

  if (input.performTime && !isValidDuration(input.performTime)) {
    throw new Error('performTime must be in ISO 8601 duration format');
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
    throw new Error('inLanguage must be a valid language code');
  }

  if (input.estimatedCost && !isValidCurrencyCode(input.estimatedCost.currency)) {
    throw new Error('estimatedCost currency must be a valid ISO 4217 currency code');
  }

  // Validate steps
  input.steps.forEach((step, index) => {
    if (!step.name) {
      throw new Error(`Step ${index + 1} must have a name`);
    }
    if (!step.text) {
      throw new Error(`Step ${index + 1} must have text content`);
    }
    if (step.url && !isValidUrl(step.url)) {
      throw new Error(`Step ${index + 1} URL must be valid`);
    }
  });

  // Build the HowTo object
  const howTo: HowToProperties = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: input.name,
    step: input.steps.map((step, index) => ({
      '@type': 'HowToStep',
      name: step.name,
      text: step.text,
      position: index + 1,
      ...(step.url && { url: step.url }),
      ...(step.image && { image: transformImageObject(step.image) }),
      ...(step.video && { video: transformVideoObject(step.video) }),
      ...(step.tools && { tool: step.tools.map(transformHowToTool) }),
      ...(step.supplies && { supply: step.supplies.map(transformHowToSupply) }),
    })),
  };

  // Add optional properties
  if (input.description) howTo.description = input.description;
  if (input.url) howTo.url = input.url;
  if (input.identifier) howTo.identifier = input.identifier;
  if (input.totalTime) howTo.totalTime = input.totalTime;
  if (input.prepTime) howTo.prepTime = input.prepTime;
  if (input.performTime) howTo.performTime = input.performTime;
  if (input.yield) howTo.yield = input.yield;
  if (input.keywords) howTo.keywords = input.keywords;
  if (input.license) howTo.license = input.license;
  if (input.inLanguage) howTo.inLanguage = input.inLanguage;
  if (input.difficulty) howTo.difficulty = input.difficulty;
  if (input.dateCreated) howTo.dateCreated = input.dateCreated;
  if (input.dateModified) howTo.dateModified = input.dateModified;
  if (input.datePublished) howTo.datePublished = input.datePublished;
  if (typeof input.isAccessibleForFree === 'boolean') {
    howTo.isAccessibleForFree = input.isAccessibleForFree;
  }
  if (input.copyrightYear && input.copyrightYear > 0) {
    howTo.copyrightYear = input.copyrightYear;
  }

  // Transform complex objects
  if (input.image) {
    if (Array.isArray(input.image)) {
      howTo.image = input.image.map(transformImageObject) as ImageObject[] | string[];
    } else {
      howTo.image = transformImageObject(input.image);
    }
  }

  if (input.estimatedCost) {
    howTo.estimatedCost = transformMonetaryAmount(input.estimatedCost);
  }

  if (input.tools) {
    howTo.tool = input.tools.map(transformHowToTool);
  }

  if (input.supplies) {
    howTo.supply = input.supplies.map(transformHowToSupply);
  }

  if (input.author) {
    howTo.author = transformPersonOrOrganization(input.author);
  }

  if (input.creator) {
    howTo.creator = transformPersonOrOrganization(input.creator);
  }

  if (input.publisher) {
    howTo.publisher = transformPersonOrOrganization(input.publisher);
  }

  if (input.copyrightHolder) {
    howTo.copyrightHolder = transformPersonOrOrganization(input.copyrightHolder);
  }

  if (input.video) {
    howTo.video = transformVideoObject(input.video);
  }

  if (input.audience) {
    howTo.audience = {
      '@type': input.audience.type || 'Audience',
      ...(input.audience.audienceType && { audienceType: input.audience.audienceType }),
      ...(input.audience.name && { name: input.audience.name }),
      ...(input.audience.description && { description: input.audience.description }),
    };
  }

  if (input.about) {
    howTo.about = {
      '@type': input.about.type,
      name: input.about.name,
      ...(input.about.description && { description: input.about.description }),
      ...(input.about.url && isValidUrl(input.about.url) && { url: input.about.url }),
      ...(input.about.image && isValidUrl(input.about.image) && { image: input.about.image }),
    };
  }

  if (input.category) {
    if (typeof input.category === 'string') {
      howTo.category = input.category;
    } else {
      howTo.category = {
        '@type': input.category.type,
        name: input.category.name,
        ...(input.category.description && { description: input.category.description }),
        ...(input.category.url && isValidUrl(input.category.url) && { url: input.category.url }),
        ...(input.category.image && isValidUrl(input.category.image) && { image: input.category.image }),
      };
    }
  }

  return howTo;
};

// Helper functions for common how-to types
export const createSimpleHowTo = (
  name: string,
  steps: Array<{ name: string; text: string; image?: string }>,
  options: {
    description?: string;
    totalTime?: string;
    difficulty?: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
    author?: string;
    authorUrl?: string;
  } = {}
): HowToProperties => {
  return createHowTo({
    name,
    description: options.description,
    totalTime: options.totalTime,
    difficulty: options.difficulty,
    isAccessibleForFree: true,
    steps: steps.map(step => ({
      name: step.name,
      text: step.text,
      ...(step.image && { image: step.image }),
    })),
    ...(options.author && {
      author: {
        type: 'Person',
        name: options.author,
        url: options.authorUrl,
      },
    }),
  });
};

export const createRecipeHowTo = (
  name: string,
  description: string,
  steps: Array<{ name: string; text: string }>,
  options: {
    prepTime?: string;
    cookTime?: string;
    totalTime?: string;
    yield?: string | number;
    ingredients?: string[];
    author?: string;
    authorUrl?: string;
  } = {}
): HowToProperties => {
  return createHowTo({
    name,
    description,
    prepTime: options.prepTime,
    performTime: options.cookTime,
    totalTime: options.totalTime,
    yield: options.yield,
    category: 'Recipe',
    isAccessibleForFree: true,
    steps: steps.map(step => ({
      name: step.name,
      text: step.text,
    })),
    ...(options.ingredients && {
      supplies: options.ingredients.map(ingredient => ({
        name: ingredient,
      })),
    }),
    ...(options.author && {
      author: {
        type: 'Person',
        name: options.author,
        url: options.authorUrl,
      },
    }),
  });
};

// Export types for external use
export type {
  HowToInput,
  HowToProperties,
  HowToStepInput,
  HowToStep,
  HowToTool,
  HowToSupply,
};