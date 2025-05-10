import type { LocationUri } from '../entity/locationUri';

export function groupByScheme(locationUris: LocationUri[]): Record<string, LocationUri[]> {
  return locationUris.reduce((groups, uri) => {
    if (!groups[uri.scheme]) {
      groups[uri.scheme] = [];
    }
    groups[uri.scheme].push(uri);
    return groups;
  }, {} as Record<string, LocationUri[]>);
}
