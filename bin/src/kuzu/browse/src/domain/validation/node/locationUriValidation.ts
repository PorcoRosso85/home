import type { ValidationResult } from '../validationResult';

export type LocationUriData = {
  uri_id: string;
  scheme: string;
  authority: string;
  path: string;
  fragment: string;
  query: string;
};

export function validateLocationUri(data: LocationUriData): ValidationResult<LocationUriData> {
  const errors: Array<{ field: string; message: string }> = [];
  const allowedSchemes = ['file', 'http', 'https', 'path'];

  // 必須: uri_id
  if (!data.uri_id || typeof data.uri_id !== 'string') {
    errors.push({ field: 'uri_id', message: 'uri_id is required and must be a string' });
  } else if (data.uri_id.trim().length === 0) {
    errors.push({ field: 'uri_id', message: 'uri_id cannot be empty' });
  }

  // 必須: scheme
  if (!data.scheme || typeof data.scheme !== 'string') {
    errors.push({ field: 'scheme', message: 'scheme is required and must be a string' });
  } else if (!allowedSchemes.includes(data.scheme)) {
    errors.push({ field: 'scheme', message: `scheme must be one of: ${allowedSchemes.join(', ')}` });
  }

  // 必須: path
  if (!data.path || typeof data.path !== 'string') {
    errors.push({ field: 'path', message: 'path is required and must be a string' });
  } else if (data.path.trim().length === 0) {
    errors.push({ field: 'path', message: 'path cannot be empty' });
  }

  // authority（オプション）
  if (data.authority !== undefined && typeof data.authority !== 'string') {
    errors.push({ field: 'authority', message: 'authority must be a string' });
  }

  // fragment（オプション）
  if (data.fragment !== undefined && typeof data.fragment !== 'string') {
    errors.push({ field: 'fragment', message: 'fragment must be a string' });
  }

  // query（オプション）
  if (data.query !== undefined && typeof data.query !== 'string') {
    errors.push({ field: 'query', message: 'query must be a string' });
  }

  if (errors.length > 0) {
    return {
      isValid: false,
      errors: errors,
      error: `Validation failed for LocationURI: ${errors.map(e => `${e.field}: ${e.message}`).join(', ')}`
    };
  }

  return {
    isValid: true,
    data: data
  };
}
