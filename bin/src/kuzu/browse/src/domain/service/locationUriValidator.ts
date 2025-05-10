import { validateLocationUri as validateInQuery, validateLocationUriObject as validateObjectInQuery } from '../../../../query/domain/validateUri';
import type { LocationUri, ParsedUri } from '../entity/locationUri';

export function validateUri(uri: string): ParsedUri {
  return validateInQuery(uri);
}

export function validateObject(locationUri: LocationUri): { isValid: boolean; error?: string } {
  return validateObjectInQuery(locationUri);
}
