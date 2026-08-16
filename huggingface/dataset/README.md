---
license: mit
language:
  - en
pretty_name: Zyntalic Anchor Lexicons
size_categories:
  - 10K<n<100K
task_categories:
  - text-generation
tags:
  - conlang
  - synthetic-language
  - lexicon
  - deterministic
configs:
  - config_name: lexicon
    data_files: lexicon.jsonl
    default: true
  - config_name: motifs
    data_files: motifs.jsonl
---

# Zyntalic Anchor Lexicons

The literary anchor lexicons behind
[Zyntalic](https://github.com/kugguk2022/Zyntalic_idiom), a deterministic
synthetic-language engine. Zyntalic mixes these vocabularies as *anchor priors*
to give generated text a stable stylistic pull toward particular source works.

- **21 anchors** drawn from public-domain literary and philosophical texts
- **12,161 word entries** across three categories
- **84 motif pairs** (opposed concept poles such as `order` / `chaos`)

## Files

| File | Contents |
| --- | --- |
| `lexicon.jsonl` | One row per word: `anchor`, `category`, `word`, `rank` |
| `motifs.jsonl` | One row per motif pair: `anchor`, `pole_a`, `pole_b` |
| `raw/<anchor>.json` | The original per-anchor files, unchanged |

```json
{"anchor": "Homer_Odyssey", "category": "noun", "word": "ship", "rank": 12}
{"anchor": "Alice_in_wonderland", "pole_a": "order", "pole_b": "chaos"}
```

`rank` is the word's position in the source list, which is ordered by descending
corpus frequency. Lower rank means more frequent in that work.

## Anchors

Alice in Wonderland · Aristotle (Organon) · Austen (Pride and Prejudice) ·
Bacon (Novum Organum) · Cervantes (Don Quixote) · Dante (Divine Comedy) ·
Darwin (Origin of Species) · Descartes (Meditations) ·
Dostoevsky (Brothers Karamazov) · Goethe (Faust) · Homer (Iliad) ·
Homer (Odyssey) · Laozi (Tao Te Ching) · Melville (Moby-Dick) ·
Milton (Paradise Lost) · Plato (Republic) · Shakespeare (Sonnets) ·
Spinoza (Ethics) · Sunzi (Art of War) · Tolstoy (War and Peace) ·
Virgil (Aeneid)

## Important limitations

**The `category` labels are not validated parts of speech.** They come from a
frequency-and-heuristic extraction pass over each source text, not from a parser
or a human annotator. The `noun` list in particular contains high-frequency
function words — `the`, `and`, `she` are all labelled `noun`. Treat `category`
as a bucket the engine draws from, not as linguistic ground truth.

The lexicons are also English-only and reflect the specific translations that
were processed, so they carry the vocabulary and period bias of those editions.
They are sized for stylistic flavour, not for coverage: each anchor contributes
at most a few hundred words.

## Provenance and licensing

Source texts are public-domain works. This compilation — the extraction,
bucketing, and packaging — is released under the MIT License, matching the
Zyntalic project. The data contains no personal or confidential information.

## Reproducing

```bash
git clone https://github.com/kugguk2022/Zyntalic_idiom.git
cd Zyntalic_idiom
python huggingface/dataset/build_dataset.py --out dataset_out
```
