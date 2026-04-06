
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
    if (config.engine.includes("Reverse")) {
        engine = "reverse";
    } else if (config.engine.includes("Transformer")) {
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
            evidentiality: config.evidentiality,
            register: config.register,
            dialect: config.dialect,
            frame_a: config.frameA,
            frame_b: config.frameB,
            zyntalic_only: true,
        }),
    });

    if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
    }

    const data = await response.json();
    const endTime = Date.now();
    
    // Backend returns { rows: [{ source, target, lemma, anchors, engine }] }
    // We only display the Zyntalic output in the target pane.
    // If rows is missing or empty, handle gracefully.
    const rows = (data.rows || []).map((row: any) => ({
      text: row.target || "???",
      mirrorText: row.mirror_text || undefined,
      sidecar: row.sidecar || undefined,
    }));

    const translatedText = rows
      .map((row) => row.text)
      .join("\n\n");
    const mirrorText = rows
      .map((row) => row.mirrorText)
      .filter((t: string) => t && t.trim().length > 0)
      .join("\n\n");

    return {
      text: translatedText || "No translation generated.",
      latency: endTime - startTime,
      confidence: 1.0, // Backend doesn't give confidence yet
      detectedSentiment: "English", // Placeholder
      mirrorText: mirrorText || undefined,
      sidecar: rows[0]?.sidecar,
      rows,
    };
  } catch (error) {
    console.error("Translation Error:", error);
    throw new Error("Failed to connect to Zyntalic Local Engine.");
  }
};
