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
  evidentiality: string;
  register: string;
  dialect: string;
  frameA: string;
  frameB: string;
}

export interface FrameMeta {
  id: string;
  anchor: string;
  weight: number;
}

export interface AnchorWeight {
  name: string;
  weight: number;
}

export interface TokenMeta {
  surface: string;
  lemma: string;
  pos: string;
  morphemes: Record<string, string | null>;
}

export interface Sidecar {
  frames: FrameMeta[];
  sigil: string | null;
  sigil_type: 'Reflection' | 'Irony' | null;
  anchor_weights: AnchorWeight[];
  evidentiality: string | null;
  register?: string | null;
  dialect?: string | null;
  scope_signature?: string | null;
  pivot: 'diverge' | 'converge' | 'neutral';
  tokens: TokenMeta[] | null;
}

export interface SentenceResult {
  text: string;
  mirrorText?: string;
  sidecar?: Sidecar;
}

export interface TranslationResult {
  text: string;
  detectedSentiment?: string;
  latency: number;
  confidence: number;
  mirrorText?: string;
  sidecar?: Sidecar;
  rows: SentenceResult[];
}
