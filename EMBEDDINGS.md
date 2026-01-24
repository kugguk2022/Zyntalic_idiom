# Zyntalic Embeddings System

This document explains the comprehensive embeddings system for generating proper Zyntalic language output.

## Overview

The Zyntalic language uses a unique blend of:
- **Hangul (Korean) characters** - predominantly for nouns (85%)
- **Polish/Latin characters** - predominantly for verbs (85%)
- **Cultural anchors** - 20 classical texts that influence word generation
- **Semantic embeddings** - for intelligent word mapping and generation

## Quick Start

### 1. Generate Embeddings

Run the embeddings generator to create vocabulary mappings:

```bash
python scripts/generate_embeddings.py
```

This creates:
- `data/embeddings/anchor_embeddings.json` - Embeddings for 20 cultural anchors
- `data/embeddings/vocabulary_mappings.json` - English→Zyntalic word mappings (1500+ words)
- `data/embeddings/word_cache.json` - Pre-generated Zyntalic words (1000 cached)
- `data/embeddings/sample_translations.json` - Example translations
- `data/embeddings/statistics.json` - System statistics

### 2. Test Translations

```bash
python test_translations.py
```

Or test individual sentences:

```python
from zyntalic.translator import translate_text

result = translate_text("I love you", mirror_rate=0.3, engine='core')
print(result[0]['target'])
# Output: 릫떂rz 산얍dom 를뎖 ⟦ctx:han=훕옍헿; ...⟧
```

## Translation Engines

### Core Engine (Recommended)
Uses vocabulary mappings and cultural anchors:
```python
translate_text("Hello world", engine='core', mirror_rate=0.3)
```

### Transformer Engine
Uses semantic matching via sentence-transformers:
```python
translate_text("Hello world", engine='transformer')
```

### Chiasmus Engine
Generates philosophical chiasmus patterns:
```python
translate_text("Hello world", engine='chiasmus')
```

### Test Suite Engine
Validates input through comprehensive test suite:
```python
translate_text("Hello world", engine='test_suite')
```

## Mirror Rate Parameter

The `mirror_rate` controls the balance between:
- **Low (0.0-0.3)**: More Zyntalic vocabulary (Hangul + Polish)
  - Example: `엢낯풿극 źęg옶fek żaźa낈źó`
- **High (0.7-1.0)**: More Zyntalic chiasmus templates (mirror structure without English)
  - Example pattern: `<A> <zy-connector> <B> · <B> <zy-connector> <A>`

**Recommended**: `0.3` for authentic Zyntalic output

## Output Format

Each translation produces:

```
[Zyntalic Text] ⟦ctx:han=[Hangul]; lemma=[root]; pos=[type]; anchors=[sources]⟧
```

Example:
```
엢낯풿극 źęg옶fek żaźa낈źó ⟦ctx:han=훕옍헿; lemma=love; pos=verb; anchors=Homer_Iliad|Plato_Republic⟧
```

Components:
- **Main text**: Zyntalic translation (Hangul-heavy nouns, Polish-heavy verbs)
- **ctx:han**: Korean phonetic context marker
- **lemma**: Root form of source word
- **pos**: Part of speech hint
- **anchors**: Cultural texts influencing this translation

## Cultural Anchors

The system uses 20 classical texts as semantic anchors:

| Western Canon | Eastern Canon | Scientific |
|--------------|--------------|-----------|
| Homer (Iliad/Odyssey) | Laozi (Tao Te Ching) | Darwin (Origin) |
| Plato (Republic) | Sunzi (Art of War) | Descartes (Meditations) |
| Aristotle (Organon) | | Bacon (Novum Organum) |
| Virgil (Aeneid) | | Spinoza (Ethics) |
| Dante (Divine Comedy) | | |
| Shakespeare (Sonnets) | | |
| Milton (Paradise Lost) | | |
| Goethe (Faust) | | |
| Cervantes (Don Quixote) | | |
| Tolstoy (War & Peace) | | |
| Dostoevsky (Brothers K.) | | |
| Austen (Pride & Prejudice) | | |
| Melville (Moby Dick) | | |

## Vocabulary Statistics

After running `generate_embeddings.py`:

```json
{
  "num_anchors": 20,
  "embedding_dimension": 384,
  "total_vocabulary_size": 1536,
  "words_per_category": {
    "adjectives": 579,
    "nouns": 511,
    "verbs": 628
  },
  "cached_words": 1000
}
```

## Language Characteristics

### Phonology
- **Hangul syllable structure**: CV, CVC, CCV, CCVC
- **Polish consonant clusters**: ść, rz, cz, sz, dz
- **Nasal vowels**: ą, ę
- **Liquid consonants**: ł, ń, ź, ć

### Morphology
- **Noun-Verb distinction**: Reflected in script choice
- **Case marking**: Encoded in Hangul final consonants (codas)
- **Verbal aspects**: Mixed with Polish conjugation patterns

### Syntax
- **Word order**: S-O-V-C (Subject-Object-Verb-Context)
- **Context tail**: Always ends with Korean Hangul metadata
- **Anchor grounding**: Every sentence references cultural sources

## API Usage

### Web API

```bash
curl -X POST http://localhost:8001/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "mirror_rate": 0.3,
    "engine": "core"
  }'
```

Response:
```json
{
  "rows": [{
    "source": "Hello world",
    "target": "엢낯풿극 źęg옶fek ⟦ctx:...⟧",
    "lemma": "hello",
    "anchors": [["Homer_Iliad", 0.4], ...],
    "engine": "core"
  }]
}
```

### Desktop App

```bash
python -m run_desktop
```

Then navigate to: http://localhost:8001

The UI provides:
- Engine selection (Transformer, Neural, Deterministic, Test Suite)
- Mirror threshold slider (0.0 - 1.0)
- Real-time translation
- Diagnostic information

## Troubleshooting

### Issue: Getting English words instead of Zyntalic

**Solution**: Lower the `mirror_rate` to 0.0-0.3

```python
translate_text("Hello", mirror_rate=0.2, engine='core')
```

### Issue: No Hangul in output

**Solution**: 
1. Regenerate embeddings: `python scripts/generate_embeddings.py`
2. Ensure `data/embeddings/vocabulary_mappings.json` exists
3. Check that nouns are being generated (nouns use more Hangul)

### Issue: Missing sentence-transformers

**Solution**: Install optional dependencies:

```bash
pip install sentence-transformers
```

Or the system will use deterministic hash-based embeddings.

### Issue: Context tail not appearing

**Solution**: This is normal. The context tail `⟦ctx:...⟧` is metadata and appears at the end of each translation.

## Advanced Usage

### Custom Anchor Weights

```python
from zyntalic.core import generate_entry

# Force specific anchors
entry = generate_entry("love", mirror_rate=0.2)
print(entry['anchors'])  # Shows which texts influenced this word
```

### Batch Translation

```python
sentences = ["Hello", "Beautiful", "Ancient wisdom"]
results = [translate_text(s, mirror_rate=0.2)[0] for s in sentences]
```

### Export Vocabulary

```python
import json

with open('data/embeddings/vocabulary_mappings.json') as f:
    vocab = json.load(f)

# All Zyntalic adjectives
adjectives = vocab['adjectives']
print(f"Total adjectives: {len(adjectives)}")
for en, zy in list(adjectives.items())[:5]:
    print(f"{en:15} → {zy}")
```

## File Structure

```
data/
  embeddings/
    anchor_embeddings.json       # 384-dim vectors for 20 anchors
    vocabulary_mappings.json     # English→Zyntalic mappings
    word_cache.json             # Pre-generated words
    sample_translations.json    # Example outputs
    statistics.json             # System stats

zyntalic/
  core.py                       # Core generation logic
  embeddings.py                # Embedding utilities
  translator.py                # High-level translation API
  transformers.py              # Semantic matching engine

scripts/
  generate_embeddings.py       # Main generation script
  train_projection.py          # Optional: train embedding projection
```

## Performance

- **Cold start**: ~2s (first embedding generation)
- **Warm cache**: ~50ms per sentence
- **Batch processing**: ~10-20 sentences/second
- **Memory usage**: ~200MB (with sentence-transformers)

## Embedding Model Selection

Default model:
- `all-MiniLM-L6-v2`

Optional higher-accuracy model:
- `BAAI/bge-small-en-v1.5` (install with `pip install .[embeddings-bge]`)

To override the model at runtime:
```bash
export ZYNTALIC_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

Accepted aliases:
- `bge-small-en-v1.5` -> `BAAI/bge-small-en-v1.5`
- `minilm` -> `all-MiniLM-L6-v2`

If the selected model fails to load, Zyntalic retries the default
`all-MiniLM-L6-v2` and then falls back to deterministic hash embeddings.

Note: If model failures are noticeable for your use case, consider making
`BAAI/bge-small-en-v1.5` the default after benchmarking on your idiom/anchor
dataset (expect ~50% extra memory/time).

## Future Enhancements

- [ ] Morphological analyzer for better POS tagging
- [ ] Trained embedding projection matrix (W.npy)
- [ ] Extended vocabulary (5000+ words per category)
- [ ] Grammar checker for Zyntalic output
- [ ] Pronunciation guide generator
- [ ] Reverse translation (Zyntalic → English)

## Contributing

To extend the vocabulary:

1. Add words to lexicon JSON files in `lexicon/`
2. Regenerate embeddings: `python scripts/generate_embeddings.py`
3. Test new mappings: `python test_translations.py`

## References

- Hangul Unicode Range: U+AC00 - U+D7AF
- Polish Diacritics: ą, ć, ę, ł, ń, ó, ś, ź, ż
- Sentence Transformers: `all-MiniLM-L6-v2` model
- Sentence Transformers (optional): `BAAI/bge-small-en-v1.5` model
- Cultural Anchors: Project Gutenberg corpus

## License

See LICENSE file in project root.
