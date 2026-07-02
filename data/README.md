# Onions glossary data

`onions_glossary_index.json` — ~7,800 headwords parsed from C. T. Onions,
*A Shakespeare Glossary* (Clarendon Press, 1911; rev. 1919).

**Rebuild** (requires `data/onions_ocr.txt` from Internet Archive):

```bash
curl -L -o data/onions_ocr.txt \
  'https://archive.org/stream/shakespeareglos00onio/shakespeareglos00onio_djvu.txt'
python3 scripts/build_onions_index.py
```

Source: https://archive.org/details/shakespearegloss00oniouoft

## Related lexical source (not yet integrated)

**Alexander Schmidt, *Shakespeare-Lexicon*** (3rd ed., revised by Sarrazin, 1902) is the other
classic Shakespeare lexicon, often used alongside Onions. A future pass could merge Schmidt
entries where Onions has no headword match.
