import type { ValidationResult } from '../validationResult';

export type VersionStateData = {
  id: string;
  timestamp: string;
  description: string;
};

export function validateVersionState(data: VersionStateData): ValidationResult<VersionStateData> {
  const errors: Array<{ field: string; message: string }> = [];

  // 必須: id
  if (!data.id || typeof data.id !== 'string') {
    errors.push({ field: 'id', message: 'id is required and must be a string' });
  } else if (data.id.trim().length === 0) {
    errors.push({ field: 'id', message: 'id cannot be empty' });
  }

  // 必須: timestamp
  if (!data.timestamp || typeof data.timestamp !== 'string') {
    errors.push({ field: 'timestamp', message: 'timestamp is required and must be a string' });
  } else {
    // ISO 8601形式のチェック
    const timestampPattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/;
    if (!timestampPattern.test(data.timestamp)) {
      errors.push({ field: 'timestamp', message: 'timestamp must be in ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)' });
    }
  }

  // description（オプション）
  if (data.description !== undefined && typeof data.description !== 'string') {
    errors.push({ field: 'description', message: 'description must be a string' });
  }

  if (errors.length > 0) {
    return {
      isValid: false,
      errors: errors,
      error: `Validation failed for VersionState: ${errors.map(e => `${e.field}: ${e.message}`).join(', ')}`
    };
  }

  return {
    isValid: true,
    data: data
  };
}
