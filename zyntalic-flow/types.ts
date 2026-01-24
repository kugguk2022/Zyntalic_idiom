
export enum TranslationEngine {
  SEMANTIC = 'Transformer (Semantic)',
  NEURAL = 'Neural (Direct)',
  LITERAL = 'Deterministic (Literal)',
  TEST_SUITE = 'Test Suite (Validation)',
  REVERSE = 'Reverse (Zyntalic -> English)'
}

export interface TranslationConfig {
  engine: TranslationEngine;
  mirror: number;
  sourceLang: string;
  targetLang: string;
}

export interface TranslationResult {
  text: string;
  detectedSentiment?: string;
  latency: number;
  confidence: number;
  mirrorText?: string;
}
