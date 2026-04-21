#!/usr/bin/env python3
"""
Comprehensive Embeddings Generator for Zyntalic

This script generates and stores embeddings and vocabulary mappings
to ensure proper Zyntalic language generation with Hangul and Polish characters.

Usage:
    python scripts/generate_embeddings.py

Output:
    - data/embeddings/anchor_embeddings.json
    - data/embeddings/vocabulary_mappings.json
    - data/embeddings/word_cache.json
"""

import hashlib
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from zyntalic.core import (  # noqa: E402
    ANCHORS,
    create_hangul_syllable,
    create_latin_syllable,
    generate_word,
    get_rng,
    load_lexicons,
)

try:
    from zyntalic.embeddings import embed_text
    HAS_EMBEDDINGS = True
except Exception:
    HAS_EMBEDDINGS = False
    print("Warning: sentence-transformers not available. Using deterministic embeddings.")


class ZyntalicEmbeddingsGenerator:
    """Generates comprehensive embeddings and vocabulary mappings for Zyntalic."""

    def __init__(self, output_dir: str = "data/embeddings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.anchor_embeddings = {}
        self.vocabulary_mappings = {}
        self.word_cache = {}

        print(f"📁 Output directory: {self.output_dir}")
        print(f"🔤 Embeddings available: {HAS_EMBEDDINGS}")

    def generate_anchor_embeddings(self) -> dict[str, list[float]]:
        """Generate embeddings for all anchor texts."""
        print("\n🎯 Generating anchor embeddings...")

        lexicons = load_lexicons()

        for anchor_name in ANCHORS:
            print(f"  Processing: {anchor_name}")

            # Get lexicon data for this anchor if available
            if anchor_name in lexicons:
                lex_data = lexicons[anchor_name]

                # Sample text from the lexicon
                sample_texts = []
                if "adjectives" in lex_data:
                    sample_texts.extend(lex_data["adjectives"][:5])
                if "nouns" in lex_data:
                    sample_texts.extend(lex_data["nouns"][:5])
                if "verbs" in lex_data:
                    sample_texts.extend(lex_data["verbs"][:5])

                combined_text = " ".join(sample_texts) if sample_texts else anchor_name.replace("_", " ")
            else:
                combined_text = anchor_name.replace("_", " ")

            # Generate embedding
            if HAS_EMBEDDINGS:
                embedding = embed_text(combined_text, dim=384)
            else:
                # Deterministic hash-based embedding
                seed = int(hashlib.sha256(combined_text.encode()).hexdigest()[:16], 16)
                rng = get_rng(str(seed))
                embedding = [rng.random() for _ in range(384)]

            self.anchor_embeddings[anchor_name] = embedding
            print(f"    ✓ Generated {len(embedding)}-dim embedding")

        return self.anchor_embeddings

    def generate_vocabulary_mappings(self, num_words_per_category: int = 500) -> dict:
        """Generate Zyntalic words for common English vocabulary."""
        print(f"\n📚 Generating vocabulary mappings ({num_words_per_category} per category)...")

        # Load English words from lexicons
        lexicons = load_lexicons()
        english_words = {
            "adjectives": set(),
            "nouns": set(),
            "verbs": set()
        }

        # Collect unique English words from all anchors
        for anchor_name, lex_data in lexicons.items():
            if "adjectives" in lex_data:
                english_words["adjectives"].update(lex_data["adjectives"][:100])
            if "nouns" in lex_data:
                english_words["nouns"].update(lex_data["nouns"][:100])
            if "verbs" in lex_data:
                english_words["verbs"].update(lex_data["verbs"][:100])

        # Generate Zyntalic words for each category
        for category, words in english_words.items():
            print(f"  {category.capitalize()}: {len(words)} words")
            self.vocabulary_mappings[category] = {}

            pos_hint = "noun" if category in ["nouns", "adjectives"] else "verb"

            for english_word in list(words)[:num_words_per_category]:
                zyntalic_word = self._generate_zyntalic_word(english_word, pos_hint)
                self.vocabulary_mappings[category][english_word] = zyntalic_word

        # Add common words that might be missing
        self._add_common_words()

        return self.vocabulary_mappings

    def _generate_zyntalic_word(self, english_word: str, pos: str = "noun") -> str:
        """Generate a proper Zyntalic word with Hangul and Polish characters."""
        rng = get_rng(f"vocab::{english_word}")

        # Determine word length based on English word length
        en_len = len(english_word)
        if en_len <= 3:
            num_syllables = 2
        elif en_len <= 6:
            num_syllables = 3
        elif en_len <= 10:
            num_syllables = 4
        else:
            num_syllables = 5

        syllables = []

        # Generate syllables with proper distribution
        # Nouns: 85% Hangul, 15% Polish
        # Verbs: 85% Polish, 15% Hangul
        for i in range(num_syllables):
            r = rng.random()

            if pos == "noun":
                # Hangul-heavy for nouns
                if r < 0.85:
                    syl = create_hangul_syllable(rng)
                else:
                    syl = create_latin_syllable(rng)
            else:
                # Polish-heavy for verbs
                if r < 0.85:
                    syl = create_latin_syllable(rng)
                else:
                    syl = create_hangul_syllable(rng)

            syllables.append(syl)

        # Add Polish markers occasionally for flavor
        if rng.random() < 0.2:
            polish_markers = ["ć", "ść", "rz", "ż", "sz", "cz"]
            marker = rng.choice(polish_markers)
            insert_pos = rng.randint(1, len(syllables) - 1)
            syllables[insert_pos] = syllables[insert_pos] + marker

        return "".join(syllables)

    def _add_common_words(self):
        """Add common words that should always be mapped."""
        print("  Adding common words...")

        common_words = {
            "adjectives": [
                "good", "bad", "big", "small", "happy", "sad", "bright", "dark",
                "ancient", "modern", "beautiful", "ugly", "strong", "weak",
                "fast", "slow", "hot", "cold", "new", "old"
            ],
            "nouns": [
                "love", "life", "death", "time", "world", "man", "woman", "child",
                "day", "night", "light", "shadow", "truth", "lie", "hope", "fear",
                "soul", "body", "heart", "mind", "journey", "path", "way", "home"
            ],
            "verbs": [
                "be", "have", "do", "make", "go", "come", "see", "hear", "know",
                "think", "feel", "love", "hate", "want", "need", "give", "take",
                "speak", "listen", "walk", "run", "live", "die", "create", "destroy"
            ]
        }

        for category, words in common_words.items():
            if category not in self.vocabulary_mappings:
                self.vocabulary_mappings[category] = {}

            pos_hint = "noun" if category in ["nouns", "adjectives"] else "verb"

            for word in words:
                if word not in self.vocabulary_mappings[category]:
                    zyntalic_word = self._generate_zyntalic_word(word, pos_hint)
                    self.vocabulary_mappings[category][word] = zyntalic_word

    def generate_word_cache(self, num_cached_words: int = 1000) -> dict:
        """Pre-generate common words for faster lookup."""
        print(f"\n💾 Generating word cache ({num_cached_words} words)...")

        for i in range(num_cached_words):
            seed = f"cache_{i}"
            word = generate_word(seed)
            self.word_cache[seed] = word

            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{num_cached_words} words")

        return self.word_cache

    def save_embeddings(self):
        """Save all generated embeddings and mappings to disk."""
        print("\n💾 Saving embeddings to disk...")

        # Save anchor embeddings
        anchor_path = self.output_dir / "anchor_embeddings.json"
        with open(anchor_path, 'w', encoding='utf-8') as f:
            json.dump(self.anchor_embeddings, f, ensure_ascii=False, indent=2)
        print(f"  ✓ Anchor embeddings: {anchor_path}")

        # Save vocabulary mappings
        vocab_path = self.output_dir / "vocabulary_mappings.json"
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(self.vocabulary_mappings, f, ensure_ascii=False, indent=2)
        print(f"  ✓ Vocabulary mappings: {vocab_path}")

        # Save word cache
        cache_path = self.output_dir / "word_cache.json"
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.word_cache, f, ensure_ascii=False, indent=2)
        print(f"  ✓ Word cache: {cache_path}")

        # Generate statistics
        self._save_statistics()

    def _save_statistics(self):
        """Generate and save statistics about the embeddings."""
        stats = {
            "num_anchors": len(self.anchor_embeddings),
            "embedding_dimension": len(list(self.anchor_embeddings.values())[0]) if self.anchor_embeddings else 0,
            "vocabulary_categories": list(self.vocabulary_mappings.keys()),
            "words_per_category": {
                cat: len(words) for cat, words in self.vocabulary_mappings.items()
            },
            "total_vocabulary_size": sum(len(words) for words in self.vocabulary_mappings.values()),
            "cached_words": len(self.word_cache),
            "has_transformer_embeddings": HAS_EMBEDDINGS
        }

        stats_path = self.output_dir / "statistics.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        print("\n📊 Statistics:")
        print(f"  Anchors: {stats['num_anchors']}")
        print(f"  Embedding dimension: {stats['embedding_dimension']}")
        print(f"  Total vocabulary: {stats['total_vocabulary_size']} words")
        print(f"  Cached words: {stats['cached_words']}")
        print(f"  ✓ Statistics saved: {stats_path}")

    def generate_sample_translations(self, num_samples: int = 10):
        """Generate sample translations to verify output quality."""
        print(f"\n🔍 Generating {num_samples} sample translations...")

        samples = []
        test_sentences = [
            "I love you",
            "The ancient philosopher wrote",
            "Beautiful birds sing",
            "Time flows like water",
            "Knowledge is power",
            "Life is beautiful",
            "The sun rises",
            "Wisdom comes with age",
            "Truth prevails",
            "Hope springs eternal"
        ]

        for sentence in test_sentences[:num_samples]:
            words = sentence.lower().split()
            zyntalic_words = []

            for word in words:
                # Try to find in vocabulary mappings
                found = False
                for category, vocab in self.vocabulary_mappings.items():
                    if word in vocab:
                        zyntalic_words.append(vocab[word])
                        found = True
                        break

                if not found:
                    # Generate on the fly
                    zyntalic_words.append(self._generate_zyntalic_word(word, "noun"))

            samples.append({
                "english": sentence,
                "zyntalic": " ".join(zyntalic_words)
            })
            print(f"  {sentence} → {samples[-1]['zyntalic']}")

        # Save samples
        samples_path = self.output_dir / "sample_translations.json"
        with open(samples_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
        print(f"  ✓ Samples saved: {samples_path}")


def main():
    """Main entry point for embeddings generation."""
    print("=" * 70)
    print("🌟 Zyntalic Embeddings Generator")
    print("=" * 70)

    generator = ZyntalicEmbeddingsGenerator()

    # Step 1: Generate anchor embeddings
    generator.generate_anchor_embeddings()

    # Step 2: Generate vocabulary mappings
    generator.generate_vocabulary_mappings(num_words_per_category=500)

    # Step 3: Generate word cache
    generator.generate_word_cache(num_cached_words=1000)

    # Step 4: Generate sample translations
    generator.generate_sample_translations(num_samples=10)

    # Step 5: Save everything
    generator.save_embeddings()

    print("\n" + "=" * 70)
    print("✅ Embeddings generation complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Check data/embeddings/ for generated files")
    print("  2. Update core.py to load vocabulary mappings")
    print("  3. Test translation with: python -m zyntalic.cli translate 'Hello world'")


if __name__ == "__main__":
    main()
