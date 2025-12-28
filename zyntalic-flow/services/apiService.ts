
import { TranslationConfig, TranslationResult } from "../types";

// Resolve API base: prefer env, then browser origin, then localhost fallback.
const API_BASE_URL = (import.meta as any)?.env?.VITE_API_BASE_URL
  || (typeof window !== "undefined" ? window.location.origin : "")
  || "http://127.0.0.1:8001";

export const performTranslation = async (
  text: string,
  config: TranslationConfig
): Promise<TranslationResult> => {
  const startTime = Date.now();

  try {
    // Map frontend engines to backend values
    let engine = "core";
    if (config.engine.includes("Transformer")) {
        engine = "transformer";
    } else if (config.engine.includes("Neural")) {
        engine = "chiasmus";
    } else if (config.engine.includes("Test Suite")) {
        engine = "test_suite";
    }

    const response = await fetch(`${API_BASE_URL}/translate`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            text: text,
            mirror_rate: config.mirror,
            engine: engine,
        }),
    });

    if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
    }

    const data = await response.json();
    const endTime = Date.now();
    
    // Backend returns { rows: [{ source, target, lemma, anchors, engine }] }
    // We need to map this to TranslationResult
    // Format to show both source and target for clarity
    
    // If rows is missing or empty, handle gracefully
    const rows = data.rows || [];
    
    // Format each translation to show: [English] → Zyntalic
    const translatedText = rows.map((r: any) => {
      const source = r.source || "Unknown";
      const target = r.target || "???";
      // Show the original sentence followed by its translation
      return `[${source}]\n→ ${target}`;
    }).join("\n\n");

    return {
      text: translatedText || "No translation generated.",
      latency: endTime - startTime,
      confidence: 1.0, // Backend doesn't give confidence yet
      detectedSentiment: "English" // Placeholder
    };
  } catch (error) {
    console.error("Translation Error:", error);
    throw new Error("Failed to connect to Zyntalic Local Engine.");
  }
};
