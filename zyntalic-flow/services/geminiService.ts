import { TranslationConfig, TranslationResult } from "../types";

const DEFAULT_LOCAL_API_PORTS = ["8001", "8000"];

const unique = (values: string[]): string[] => {
  const seen = new Set<string>();
  return values.filter((value) => {
    if (!value || seen.has(value)) {
      return false;
    }
    seen.add(value);
    return true;
  });
};

const buildApiCandidates = (): string[] => {
  const envBase = (import.meta as any)?.env?.VITE_API_BASE_URL?.trim?.() || "";
  const browserOrigin = typeof window !== "undefined" ? window.location.origin : "";
  const localhostBases = DEFAULT_LOCAL_API_PORTS.map((port) => `http://127.0.0.1:${port}`);

  return unique([
    envBase,
    browserOrigin,
    ...localhostBases,
  ]);
};

const API_BASE_CANDIDATES = buildApiCandidates();

const postJsonWithFallback = async (path: string, body: object): Promise<Response> => {
  let lastError: Error | null = null;

  for (const baseUrl of API_BASE_CANDIDATES) {
    try {
      const response = await fetch(`${baseUrl}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const detail = (payload as any).detail || response.statusText;
        throw new Error(`${baseUrl}${path} -> ${detail}`);
      }

      return response;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
    }
  }

  throw lastError || new Error("No API base URL candidates were reachable.");
};

export const performGeminiTranslation = async (
  text: string,
  config: TranslationConfig
): Promise<TranslationResult> => {
  const startTime = Date.now();

  try {
    const response = await postJsonWithFallback("/translate/gemini", {
      text,
      mirror_rate: config.mirror,
      target_lang: config.targetLang,
      source_lang: config.sourceLang,
      engine: config.engine,
    });

    const data = await response.json();
    const endTime = Date.now();

    return {
      text: data.translated_text || "No translation generated.",
      latency: endTime - startTime,
      confidence: data.confidence ?? 1.0,
      detectedSentiment: data.detected_source_language,
    };
  } catch (error) {
    console.error("Gemini Translation Error:", error);
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to connect to Gemini proxy. ${detail}`);
  }
};
