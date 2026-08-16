const STORAGE_KEY = "zyntalic.apiKey";

/**
 * Build-time default, used when the app is served alongside a keyed API and no
 * key has been entered yet. Anything in a Vite bundle is public, so only set
 * VITE_API_KEY for local or trusted-network builds.
 */
const buildTimeKey = ((import.meta as any)?.env?.VITE_API_KEY ?? "").trim();

/**
 * Read the API key the browser should present.
 *
 * An empty string means "send no key", which is what a server started in
 * local unauthenticated mode expects.
 */
export const getApiKey = (): string => {
  if (typeof window === "undefined") {
    return buildTimeKey;
  }
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored !== null) {
      return stored.trim();
    }
  } catch {
    // Private-mode or blocked storage; fall back to the build-time key.
  }
  return buildTimeKey;
};

export const setApiKey = (value: string): void => {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(STORAGE_KEY, value.trim());
  } catch {
    // Nothing to do: the key simply will not persist across reloads.
  }
};

/** Headers carrying the API key, or an empty object when no key is configured. */
export const apiKeyHeaders = (): Record<string, string> => {
  const key = getApiKey();
  return key ? { "X-API-Key": key } : {};
};
