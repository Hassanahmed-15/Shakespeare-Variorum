# Span mismatch adjudication packets (v2 tail-bounded spans)

Human review template: classify each as (a) extraction artifact, (b) witness OCR noise,
(c) genuine span mismatch / paraphrase.

## 1. A Midsummer Night's Dream — ACT 1 SCENE 2 / line 76 / note 1

- Witness: `/Users/work/Projects/Shakespeare-Variorum/data/ia_cache/amidsommernight01furngoog_djvu.txt`
- anchor_method: `lemma_bracket`
- full_ratio: **51.3** | tail_ratio: 57.3
- span_method: `span_estimated:note_len_296_401_tail_tail_below_threshold` | span_len_ratio: 1.04

### Note (electronic)

```
and ’twere] STEEVENS: As if it were. Compare Tro. & Cres. I, ii, 188: 'Her hair, like wires, metally, sleek and fine, Like to the strings of Orpheus’ harp, she was; Her eyes, like marigolds, run through with wine; Her teeth, like pearls, her forehead full of brass; Her lips, like coral, red, and full of gaps; And as for all the rest, her straw-coloured beard made up the show.’—I. G.
```

### Witness span (bounded)

```
and 'twere] Steevens: As if it were. Compare Tro. <5r* Cres. I, ii, 188: 



ACT I, sc. ii.] A MIDSOMMER NIGHTS DREAME 41 

Qidn. You can play no part but Piramus^ for Pira- 82 

nius is a fweet-iac'd man^ a proper man as one fhall fee in 
a fummers day ; a mod louely Gentleman-like man^ ther- 
fore you mull needs play Piramus. 85 

BoU Well, I will vndertake it What beard were I 
beft to play it i
```

---

## 2. Henry IV, Part 1 — ACT 4 ,SCENE 4 / line 34 / note 0

- Witness: `/Users/work/Projects/Shakespeare-Variorum/data/ia_cache/newvariorumediti21shak_djvu.txt`
- anchor_method: `lemma_bracket`
- full_ratio: **49.1** | tail_ratio: 58.8
- span_method: `span_estimated:note_len_365_494_tail_tail_below_threshold` | span_len_ratio: 1.1

### Note (electronic)

```
estimation] SCHMIDT (1874): Reputation. Drawing on the provided sources, I have completed the line-by-line audit of the Notes for Act 5, Scene 1. I have identified each keyword or phrase in the notes, located its position in the Play Text (lines 1–148), and updated the line numbers in the notes to reflect their exact location in the text. As instructed, no words have been changed, and I have added spacing after every line of text and every note.
```

### Witness span (bounded)

```
estimation]  Warburton  (ed.  1747):  Estimation  for  conjec¬ 
ture.  But  between  this  and  the  foregoing  line,  it  appears  there  were  some 
lines  that  are  now  lost.  For,  consider  the  sense.  What  was  it  that  was  rumi¬ 
nated,  plotted,  and  set  down? — Johnson  (ed.  1765):  If  the  editor  had,  before 
he  wrote  this  note,  read  ten  lines  forward,  he  would  have  seen  that  nothing  is 
omitted.  Worcester  gives  a  dark  hint  of  a  conspiracy.  Hots
```

---
