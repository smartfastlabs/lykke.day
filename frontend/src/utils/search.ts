export const normalizeSearchText = (value: string): string =>
  value.toLowerCase().replace(/\s+/g, "");

export const fuzzyMatch = (query: string, target: string): boolean => {
  const normalizedQuery = normalizeSearchText(query);
  if (!normalizedQuery) return true;

  const normalizedTarget = normalizeSearchText(target);
  if (!normalizedTarget) return false;

  let queryIndex = 0;
  for (const char of normalizedTarget) {
    if (char === normalizedQuery[queryIndex]) {
      queryIndex += 1;
      if (queryIndex >= normalizedQuery.length) {
        return true;
      }
    }
  }
  return false;
};
