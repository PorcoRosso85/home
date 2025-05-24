import type { ValidationResult } from '../validationResult';

// REFACTORED: 究極の最小化LocationURIスキーマ（1プロパティのみ）
export type LocationUriData = {
  id: string;              // 完全なURI情報（全ての情報を含む）
};

export function validateLocationUri(data: LocationUriData): ValidationResult<LocationUriData> {
  const errors: Array<{ field: string; message: string }> = [];
  const allowedSchemes = ['file', 'http', 'https', 'requirement', 'test', 'document'];

  // 必須: id
  if (!data.id || typeof data.id !== 'string') {
    errors.push({ field: 'id', message: 'id is required and must be a string' });
  } else if (data.id.trim().length === 0) {
    errors.push({ field: 'id', message: 'id cannot be empty' });
  } else {
    // スキーマバリデーション（idから派生）
    const scheme = data.id.split(':')[0];
    if (scheme && !allowedSchemes.includes(scheme)) {
      errors.push({ field: 'id', message: `Invalid scheme '${scheme}'. Allowed: ${allowedSchemes.join(', ')}` });
    }
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
    data: {
      id: data.id
    }
  };
}
