import type { ValidationResult } from '../../../domain/validation/validationResult';
import { validateVersionState, type VersionStateData } from '../../../domain/validation/node/versionStateValidation';
import { validateLocationUri, type LocationUriData } from '../../../domain/validation/node/locationUriValidation';

export type VersionedLocationData = {
  version_id: string;
  location_uris: LocationUriData[];
  previous_version_id?: string;
};

export function validateVersionBatch(data: VersionedLocationData): ValidationResult<VersionedLocationData> {
  const errors: Array<{ field: string; message: string }> = [];

  // VersionStateデータの作成とバリデーション
  const versionStateData: VersionStateData = {
    id: data.version_id,
    timestamp: new Date().toISOString(),
    description: `Version ${data.version_id} release`
  };

  const versionStateResult = validateVersionState(versionStateData);
  if (!versionStateResult.isValid) {
    if (versionStateResult.errors) {
      errors.push(...versionStateResult.errors.map(e => ({ field: `versionState.${e.field}`, message: e.message })));
    } else if (versionStateResult.error) {
      errors.push({ field: 'versionState', message: versionStateResult.error });
    }
  }

  // location_urisの型チェック
  if (!Array.isArray(data.location_uris)) {
    errors.push({ field: 'location_uris', message: 'location_uris must be an array' });
  } else {
    // 各LocationURIのバリデーション
    data.location_uris.forEach((uri, index) => {
      const uriResult = validateLocationUri(uri);
      if (!uriResult.isValid) {
        if (uriResult.errors) {
          errors.push(...uriResult.errors.map(e => ({
            field: `location_uris[${index}].${e.field}`,
            message: e.message
          })));
        } else if (uriResult.error) {
          errors.push({ field: `location_uris[${index}]`, message: uriResult.error });
        }
      }
    });
  }

  // previous_version_id（オプション）
  if (data.previous_version_id !== undefined && 
      (typeof data.previous_version_id !== 'string' || data.previous_version_id.trim().length === 0)) {
    errors.push({ field: 'previous_version_id', message: 'previous_version_id must be a non-empty string' });
  }

  if (errors.length > 0) {
    return {
      isValid: false,
      errors: errors,
      error: `Validation failed for VersionBatch: ${errors.map(e => `${e.field}: ${e.message}`).join(', ')}`
    };
  }

  return {
    isValid: true,
    data: data
  };
}
