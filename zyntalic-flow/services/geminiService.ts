
import { TranslationConfig, TranslationResult } from "../types";

// Resolve API base: prefer env, then browser origin, then localhost fallback.
const API_BASE_URL = (import.meta as any)?.env?.VITE_API_BASE_URL
  || (typeof window !== "undefined" ? window.location.origin : "")
  || "http://127.0.0.1:8001";

export const performGeminiTranslation = async (
  text: string,
  config: TranslationConfig
): Promise<TranslationResult> => {
  const startTime = Date.now();

  try {
    const response = await fetch(`${API_BASE_URL}/translate/gemini`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        mirror_rate: config.mirror,
        target_lang: config.targetLang,
        source_lang: config.sourceLang,
        engine: config.engine,
      }),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      const detail = (payload as any).detail || response.statusText;
      throw new Error(`Gemini proxy error: ${detail}`);
    }

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
    throw new Error("Failed to connect to Gemini proxy.");
  }
};
