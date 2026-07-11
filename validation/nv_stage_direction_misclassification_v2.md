# Stage-direction misclassification audit (referee Point 3)

## Method

- **Classifier mirrored:** `isStageDirection()` in `index.html` — any play line that both starts with `[` and ends with `]` receives stage-direction styling.
- **False positive:** bracket-triggered SD line that is not a genuine stage direction (note/apparatus bleed, editorial brackets, dialogue wrapped in brackets, truncated speech).
- **Corpus:** NV dramatic volumes (`Public/Data/*.json`). Scene/act headers and DRAMATIS PERSONAE excluded.

- **Excluded:** Troilus and Cressida (21 plays audited).

## Summary rates

| Metric | Count | Rate |
|--------|------:|-----:|
| Total play lines | 67,502 | — |
| Lines containing `[` | 2,322 | 3.4399% of play lines |
| Bracket SD triggers (`[…]` whole line) | 2,139 | 3.1688% of play lines |
| **Misclassified (false positives)** | **52** | **0.0770% of play lines** |
| Misclassified / bracket SD triggers | 52 / 2,139 | **2.4310%** |

### Interpretation

The misclassification rate is **0.0770%** of play lines (52 / 67,502).

### Paper-ready sentence

> We audited stage-direction styling across all 21 NV playtext volumes (67,502 play lines). The UI treats any line fully wrapped in square brackets as a stage direction. Heuristic review identified **52** false positives (**0.08%** of play lines; **2.43%** of bracket-wrapped lines), chiefly dialogue or note fragments accidentally bracketed during digitization. The failure mode is cosmetic—mis-set typography and TTS skipping—not note loss.

Failure mode: affected lines render in stage-direction typography and are skipped by the audio/TTS pipeline (`_isAudioStageDir` also keys on leading `[`). No note text is lost; the error is display/navigation only.

### False-positive reasons (corpus-wide)

- `lowercase_fragment`: 35
- `truncated_speech`: 6
- `parenthetical_dialogue`: 5
- `apparatus_or_note_bleed`: 2
- `dialogue_in_brackets`: 2
- `merged_sd_and_dialogue`: 2

## Per-play breakdown

| Play | Play lines | Bracket SD | Misclassified | Rate |
|------|----------:|-----------:|--------------:|-----:|
| Coriolanus | 4,110 | 155 | 10 | 0.2433% |
| The Tempest | 2,488 | 74 | 7 | 0.2814% |
| Henry IV, Part 2 | 3,541 | 114 | 7 | 0.1977% |
| The Winter's Tale | 3,586 | 84 | 6 | 0.1673% |
| Macbeth | 2,605 | 98 | 5 | 0.1919% |
| Twelfth Night | 2,625 | 146 | 4 | 0.1524% |
| Cymbeline | 4,062 | 120 | 4 | 0.0985% |
| Romeo and Juliet | 3,364 | 129 | 3 | 0.0892% |
| As You Like It | 3,039 | 92 | 2 | 0.0658% |
| Antony and Cleopatra | 3,869 | 193 | 2 | 0.0517% |
| Much Ado About Nothing | 2,426 | 85 | 1 | 0.0412% |
| Love's Labour's Lost | 2,964 | 108 | 1 | 0.0337% |
| Hamlet | 4,363 | 0 | 0 | 0.0000% |
| King Lear | 3,885 | 0 | 0 | 0.0000% |
| Othello | 3,457 | 23 | 0 | 0.0000% |
| The Merchant of Venice | 2,687 | 110 | 0 | 0.0000% |
| A Midsummer Night's Dream | 1,955 | 15 | 0 | 0.0000% |
| Richard III | 3,911 | 211 | 0 | 0.0000% |
| Julius Caesar | 2,748 | 153 | 0 | 0.0000% |
| King John | 2,745 | 101 | 0 | 0.0000% |
| Henry IV, Part 1 | 3,072 | 128 | 0 | 0.0000% |

## Sample false positives

### Romeo and Juliet
- **lowercase_fragment** (ACT 1 SCENE 1 / line 117): `[and Benvolio exit.]`
- **lowercase_fragment** (ACT 1 SCENE 2 / line 92): `[cup of wine. Rest you merry.    He exits.]`
- **lowercase_fragment** (ACT 2 SCENE 4 / line 149): `[lady.    Mercutio and Benvolio exit.]`

### Macbeth
- **parenthetical_dialogue** (ACT 3 SCENE 1 / line 8): `[(As upon thee, Macbeth, their speeches shine)]`
- **parenthetical_dialogue** (ACT 3 SCENE 1 / line 26): `[(Which still hath been both grave and prosperous)]`
- **parenthetical_dialogue** (ACT 3 SCENE 1 / line 157): `[(To leave no rubs nor botches in the work)]`

### As You Like It
- **lowercase_fragment** (ACT 3 SCENE 2 / line 171): `[retreat, though not with bag and baggage, yet]`
- **lowercase_fragment** (ACT 4 SCENE 3 / line 90): `[company. Silvius exits.]`

### The Tempest
- **lowercase_fragment** (ACT 1 SCENE 1 / line 34): `[hearts!—Out of our way, I say!  He exits.]`
- **dialogue_in_brackets** (ACT 1 SCENE 2 / line 156): `[The gates of Milan, and i’ th’ dead of darkness]`
- **truncated_speech** (ACT 1 SCENE 2 / line 457): `[Aside. I must obey. His art is of such power]`

### The Winter's Tale
- **truncated_speech** (ACT 1 SCENE 2 / line 274): `[Aside. They’re here with me already, whisp’ring,]`
- **lowercase_fragment** (ACT 4 SCENE 4 / line 223): `[the door, you would never dance again after a tabor]`
- **lowercase_fragment** (ACT 4 SCENE 4 / line 258): `[in ’s tunes.   Servant exits.]`

### Much Ado About Nothing
- **apparatus_or_note_bleed** (ACT 2 SCENE 3 / line 10): `[Exit] LLOYD (p. 199): The boy who was sent for a book, and does not reappear, seems to have been the means of the conspirators learning his master's whereabout, and to have been kept away by their management.]`

### Twelfth Night
- **lowercase_fragment** (ACT 1 SCENE 5 / line 147): `[door like a sheriff's post, and be the supporter to]`
- **lowercase_fragment** (ACT 2 SCENE 3 / line 175): `[bed, and dream on the event. Farewell.]`
- **lowercase_fragment** (ACT 2 SCENE 5 / line 173): `[entertainest my love, let it appear in thy smiling;]`

### Love's Labour's Lost
- **apparatus_or_note_bleed** (ACT 4 SCENE 3 / line 330): `[From women's eyes this doctrine I derive;  They are the ground, the books, the academes From whence doth spring the true Promethean fire]`

### Antony and Cleopatra
- **lowercase_fragment** (ACT 3 SCENE 10 / line 4): `[noise of a sea fight.]`
- **lowercase_fragment** (ACT 5 SCENE 2 / line 354): `[worm.    He exits.]`

### Cymbeline
- **lowercase_fragment** (ACT 2 SCENE 2 / line 2): `[bed, and a Lady.]`
- **dialogue_in_brackets** (ACT 2 SCENE 3 / line 67): `[The one is Caius Lucius.   Messenger exits.]`
- **lowercase_fragment** (ACT 5 SCENE 2 / line 2): `[door, and the Briton army at another, Leonatus Posthumus]`

### Coriolanus
- **lowercase_fragment** (ACT 1 SCENE 3 / line 64): `[drum than look upon his schoolmaster.]`
- **lowercase_fragment** (ACT 1 SCENE 4 / line 74): `[the gates, and is shut in.]`
- **lowercase_fragment** (ACT 1 SCENE 9 / line 2): `[door, Cominius with the Romans; at another door]`

### Henry IV, Part 2
- **truncated_speech** (ACT 1, SCENE 2 / line 205): `[Aside. Marry, not in ashes and sackcloth, but in]`
- **lowercase_fragment** (ACT 2, SCENE 1 / line 180): `[and others exit.]`
- **lowercase_fragment** (ACT 2, SCENE 4 / line 373): `[there, Francis.     Francis exits.]`

