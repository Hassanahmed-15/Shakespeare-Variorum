# Lexical and biblical source indices

These JSON files power retrieval-based grounding for Basic, Expert, and Full Fathom Five analysis tiers.

| File | Source | Entries |
|------|--------|---------|
| `onions_glossary_index.json` | C. T. Onions, *A Shakespeare Glossary* (1911; rev. 1919) | ~7,800 headwords |
| `schmidt_lexicon_index.json` | Alexander Schmidt, *Shakespeare-Lexicon* (3rd ed., Sarrazin, 1902) | ~16,750 headwords |
| `geneva_bible_index.json` | Geneva Bible (1599), eBible.org USFM (`enggnv`) | ~31,090 verses |

## Onions

```bash
curl -L -o data/onions_ocr.txt \
  'https://archive.org/stream/shakespeareglos00onio/shakespeareglos00onio_djvu.txt'
python3 scripts/build_onions_index.py
```

Source: https://archive.org/details/shakespearegloss00oniouoft

## Schmidt

```bash
curl -L -o data/schmidt_vol1_ocr.txt \
  'https://archive.org/stream/shakespearelexic01schmuoft/shakespearelexic01schmuoft_djvu.txt'
curl -L -o data/schmidt_ocr.txt \
  'https://archive.org/stream/shakespearelexi02sarrgoog/shakespearelexi02sarrgoog_djvu.txt'
python3 scripts/build_schmidt_index.py
```

Sources: https://archive.org/details/shakespearelexic01schmuoft , https://archive.org/details/shakespearelexi02sarrgoog

## Geneva Bible (1599)

```bash
mkdir -p data/geneva_raw
curl -L -o data/geneva_raw/enggnv_usfm.zip \
  'https://ebible.org/Scriptures/enggnv_usfm.zip'
python3 scripts/build_geneva_index.py
```

Source: https://ebible.org/Scriptures/details.php?id=enggnv

Raw OCR/USFM inputs are gitignored; committed indices are used at deploy time via `netlify.toml` `included_files`.
