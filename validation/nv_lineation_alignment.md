# Lineation alignment audit (click simulation + witness)

Generated audit mirroring `findNotesForLine` / `matchesText` in `index.html`.

## Corpus summary

- Plays audited: **21**
- Clickable lines (non-empty `play` + ≥1 note): **18,854**
- Empty `play` with notes (not clickable): **29**

### Layer 1 — Click retrieval (same JSON line key)

- Correct key: **18,827** (99.86%)
- Wrong key (same notes): **0**
- Wrong key (different notes): **27** (0.14% of clickable)
- Lines in duplicate-text groups (diagnostic; not all mis-retrieve): **60** (0.32% of clickable)
- No text match: **0**
- Duplicate `play` text in scene: **60**

### Layer 2 — End-to-end (retrieval + witness on returned notes)

Pass = notes returned to the user's click are witness **exact** or **high** (≥0.75), and when retrieval hits the expected key (or wrong-key collision carries identical notes).

- **E2E pass: 18,819 (99.81%)**
- E2E retrieval fail: **27**
- E2E witness partial: **5**
- E2E witness fail: **3**

### Witness tiers (on retrieved notes)

- exact: **16,385** (86.90%)
- high: **2,444** (12.96%)
- partial: **5** (0.03%)
- fail: **3** (0.02%)
- no_witness: **0** (0.00%)

## Per-play breakdown

| Play | Clickable | Retrieval OK | E2E pass | Wrong-key (diff notes) |
|------|----------:|-------------:|---------:|-----------------------:|
| A Midsummer Night's Dream | 616 | 100.00% | 99.68% | 0 |
| Antony and Cleopatra | 931 | 100.00% | 100.00% | 0 |
| As You Like It | 825 | 100.00% | 99.88% | 0 |
| Coriolanus | 969 | 100.00% | 100.00% | 0 |
| Cymbeline | 920 | 99.89% | 99.89% | 1 |
| Hamlet | 1,590 | 99.94% | 99.94% | 1 |
| Henry IV, Part 1 | 712 | 100.00% | 100.00% | 0 |
| Henry IV, Part 2 | 1,560 | 99.94% | 99.94% | 1 |
| Julius Caesar | 649 | 99.85% | 99.85% | 1 |
| King John | 752 | 99.87% | 99.73% | 1 |
| King Lear | 1,013 | 100.00% | 100.00% | 0 |
| Love's Labour's Lost | 968 | 98.76% | 98.76% | 12 |
| Macbeth | 1,002 | 100.00% | 100.00% | 0 |
| Much Ado About Nothing | 776 | 99.87% | 99.87% | 1 |
| Richard III | 1,069 | 99.53% | 99.44% | 5 |
| Romeo and Juliet | 665 | 100.00% | 99.85% | 0 |
| The Merchant of Venice | 867 | 99.54% | 99.54% | 4 |
| The Tempest | 621 | 100.00% | 100.00% | 0 |
| The Winter's Tale | 856 | 100.00% | 100.00% | 0 |
| Troilus and Cressida | 584 | 100.00% | 99.66% | 0 |
| Twelfth Night | 909 | 100.00% | 100.00% | 0 |

## Sample retrieval failures

### Hamlet
- **retrieval_wrong_key_different_notes** ACT 4 SCENE 5 expected line 225 → returned 30: `OPHELIA sings`

### The Merchant of Venice
- **retrieval_wrong_key_different_notes** ACT 2 SCENE 2 expected line 60 → returned 49: `talk you of young Master Launcelot?`
- **retrieval_wrong_key_different_notes** ACT 2 SCENE 5 expected line 63 → returned 47: `[Exit]`
- **retrieval_wrong_key_different_notes** ACT 3 SCENE 2 expected line 331 → returned 139: `BASSANIO: [Reads`

### Much Ado About Nothing
- **retrieval_wrong_key_different_notes** ACT 5 SCENE 3 expected line 25 → returned 22: `Heavily, heavily.`

### Love's Labour's Lost
- **retrieval_wrong_key_different_notes** ACT 1 SCENE 1 expected line 267 → returned 126: `FERDINAND: [Reads`
- **retrieval_wrong_key_different_notes** ACT 2 SCENE 1 expected line 120 → returned 119: `ROSALINE: Did not I dance with you in Brabant once?`
- **retrieval_wrong_key_different_notes** ACT 3 SCENE 1 expected line 52 → returned 2: `DON`

### Richard III
- **retrieval_wrong_key_different_notes** ACT 3 SCENE 1 expected line 100 → returned 83: `GLOUCESTER: [Aside`
- **retrieval_wrong_key_different_notes** ACT 4 SCENE 2 expected line 101 → returned 31: `[Exit]`
- **retrieval_wrong_key_different_notes** ACT 5 SCENE 3 expected line 174 → returned 149: `Let fall thy lance: despair, and die!`

### Julius Caesar
- **retrieval_wrong_key_different_notes** ACT 3 SCENE 2 expected line 108 → returned 101: `And Brutus is an honourable man.`

### Cymbeline
- **retrieval_wrong_key_different_notes** ACT 1 SCENE 1 expected line 231 → returned 82: `[They exit.]`

### King John
- **retrieval_wrong_key_different_notes** ACT 3 SCENE 1 expected line 137 → returned 135: `BASTARD: And hang a calf's-skin on those recreant limbs.`

### Henry IV, Part 2
- **retrieval_wrong_key_different_notes** ACT 5, SCENE 3 expected line 51 → returned 35: `SILENCE sings`

