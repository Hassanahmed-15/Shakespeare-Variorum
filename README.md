# Shakespeare Variorum Digital Edition

A comprehensive digital platform for exploring Shakespeare's plays with integrated New Variorum commentary and analysis tools.

## Overview

This project provides an interactive web application that combines Shakespeare's original texts with scholarly commentary from the New Variorum editions. Users can navigate through plays, access detailed character lists (Dramatis Personae), and explore extensive critical analysis from centuries of Shakespeare scholarship.

## Features

### 📚 Complete Play Library
- **21 Shakespeare Plays** including major works like Hamlet, Macbeth, King Lear, Romeo and Juliet, and Othello
- **Dramatis Personae** for each play with properly formatted character lists
- **Scene-by-scene navigation** with easy access to any act or scene

### 🔍 Advanced Analysis Tools
- **Three Analysis Modes:**
  - **Basic**: Simple AI-powered text analysis
  - **Expert**: Advanced literary analysis with contextual insights
  - **Full Fathom Five**: Traditional New Variorum commentary integration

### 📖 New Variorum Integration
- **Five Core Plays** with full New Variorum Analysis:
  - Hamlet (analysis only, no critics list)
  - Macbeth (with critics bibliography)
  - King Lear (with German critics list)
  - Romeo and Juliet (with English works, editions & translations, French & German criticism)
  - Othello (with comprehensive critics list)

### 🎭 Critics & Authorities
- **Extensive Bibliography** of Shakespeare scholars and critics
- **Multi-language Sources** including German, French, Italian, and other European scholarship
- **Historical Context** spanning from 18th-century pioneers to modern critics

## Technical Architecture

### Frontend
- **Pure HTML/CSS/JavaScript** - No external frameworks required
- **Responsive Design** - Works on desktop, tablet, and mobile devices
- **Modern UI** - Clean, accessible interface with dark/light theme support

### Data Structure
- **JSON-based Play Data** - Each play stored as structured JSON with scenes, characters, and notes
- **Modular Design** - Easy to add new plays or update existing ones
- **Optimized Loading** - Efficient parsing and display of large text files

### Deployment (Netlify)
- **`netlify.toml`** sets `publish = "."` — the live site uses **`index.html` in the repo root only**.
- **`My Website/index.html`** is a symlink to that root file so local work in either place stays aligned. **Edit the root `index.html` for changes to go live.**

#### Production domain (`www.newvariorum.com`)
The public site should use the custom domain, not only the default `*.netlify.app` URL.

1. In **Netlify** → your site → **Domain management** → **Add domain** → enter `newvariorum.com` and `www.newvariorum.com` (or add `www` first, as you prefer).
2. Follow Netlify’s **DNS** instructions at your registrar: typically a **CNAME** for `www` pointing to Netlify’s target (e.g. `your-site-name.netlify.app`), and for the apex `newvariorum.com` either Netlify’s **A records** / **ALIAS** as shown, or redirect apex to `www`.
3. In Netlify, set **`www.newvariorum.com`** as the **primary domain** (and enable **HTTPS**; Netlify provisions certificates automatically).
4. Redeploy or wait for DNS to propagate; then open the site at **`https://www.newvariorum.com`**.

Serverless functions (`functions/shakespeare.js`) load play JSON from the same host using `URL` / `DEPLOY_PRIME_URL` when present, with **`https://www.newvariorum.com`** as fallback so API calls resolve to the live site after the domain is attached.

### File Organization
```
├── index.html              # Main application file (this is what Netlify serves)
├── styles/                 # CSS styling
│   ├── modern-ui.css      # Main stylesheet
│   └── tokens.css         # Design tokens
├── Public/Data/           # Play data files
│   ├── *.json            # Individual play files
│   ├── app.js            # Legacy application logic
│   └── notes-integration.js # Notes processing
└── functions/             # Serverless functions (Netlify)
```

## Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Local web server (for development)

### Installation
1. Clone or download the repository
2. Open `index.html` in a web browser, or
3. Serve the files using a local web server:
   ```bash
   # Using Python
   python -m http.server 8000
   
   # Using Node.js
   npx serve .
   ```

### Usage
1. **Select a Play**: Choose from the dropdown in the sidebar
2. **Navigate**: Click on scenes in the left navigation panel
3. **Analyze Text**: Select text and choose an analysis mode
   - You can highlight up to 1–3 consecutive lines by clicking and dragging over the passage.  The selection is what the analysis tools will use.
   - To clear your selection, just click anywhere outside the text or press the `Esc` key; this will un‑highlight the lines and reset the interface.
4. **Explore Commentary**: Access New Variorum critics lists for supported plays

## Supported Plays

### Full New Variorum Integration
- **Hamlet** - Complete analysis with character studies
- **Macbeth** - Full commentary with critics bibliography
- **King Lear** - German scholarship integration
- **Romeo and Juliet** - Multi-language editions and criticism
- **Othello** - Comprehensive critics database

### Standard Plays
- As You Like It
- Coriolanus
- Cymbeline
- Henry IV (Parts 1 & 2)
- Julius Caesar
- King John
- Love's Labour's Lost
- Merchant of Venice
- Midsummer Night's Dream
- Much Ado About Nothing
- Richard II & III
- The Tempest
- The Winter's Tale
- Troilus and Cressida
- Twelfth Night

## Complete List of New Variorum Critics & Authorities for Macbeth

E. A. Abbott, Shakespearian Grammar, London, 1870  
Prof. Allen, MS notes on Macbeth, 1867  
Angellier et Montegut, Macbeth, Paris, 1889  
Anonymous, Variorum Edition of Macbeth, London, 1807  
Ethics of Macbeth (Dublin University Magazine, March), 1865  
Theatrical Register, York, 1788  
Antidote Against Melancholy (Collier's reprint), 1661  
W. Archer and R. W. Lowe, Macbeth on the Stage (English Illustrated Magazine, December), 1888  
W. R. Arrowsmith, Shakespeare's Editors and Commentators, London, 1865  
C. Badham, Text of Shakespeare (Cambridge Essays), 1856  
Criticism Applied to Shakespeare, 1846  
S. Bailey, The Received Text of Shakespeare, 1862  
J. Baret, An Alvearie, 1580  
C. Bathurst, Differences of Shakespeare's Versification, 1857  
T. S. Baynes, Shakespeare Studies and other Essays, 1896  
Beaumont and Fletcher, Works (ed. Dyce), 1843  
A. Becket, Shakespeare Himself Again, 1815  
S. Beisley, Shakespeare's Garden, 1864  
H. Beckhaus, Shakespeare's Macbeth und die Schillersche Bearbeitung, Ostrovo, 1889  
J. W. O. Benda, Shakespeare's Dramatische Werke, Leipzig, 1825  
A. Beljame, Macbeth, Paris, 1897  
G. J. Bell, Notes on Mrs. Siddons's Lady Macbeth (Nineteenth Century, February), 1878  
Edwin Booth, Macbeth, Prompt-book (ed. W. Winter), New York, 1878  
W. J. Birch, Inquiry into the Philosophy and Religion of Shakespeare, London, 1848  
J. B. Bittinger, Transactions American Philological Association, 1876  
K. Blind, Shakespeare's Schicksalsschwestern. Die Gegenwart, 26 April, 1879  
J. Boaden, Life of J. P. Kemble, 1825  
K. Börner, Ueber Shakespeare's Macbeth, Lüdenscheid, 1870  
J. T. Brockett, Glossary of North Country Words, Newcastle, 1829  
C. A. Brown, Shakespeare's Autobiographical Poems, London, 1838  
J. C. Bucknill, Mad Folk of Shakespeare, 1867  
J. Bulloch, Studies on Text of Shakespeare, 1878  
G. N. Bürger, Macbeth, Göttingen, 1784  
N. Butler, Miscellanies, Louisville, 1880  
R. Böttner, Erläuterungen zu Shakespeare's Macbeth, Leipzig, n. d.  
T. Campbell, Life of Mrs. Siddons, London, 1834  
Lord Campbell, Legal Acquirements of Shakespeare, New York, 1859  
E. Capell, Notes, etc., London, 1779  
Miss C. Carmichael, Academy, 8 February, 1879  
J. C. Carr, Lord and Lady Macbeth, 1897  
W. Carr, Dialect of Craven, 1828  
R. Carruthers and W. Chambers, Works of Shakespeare, 1861  
R. Cartwright, New Readings in Shakespeare, 1866  
G. Chalmers, Supplemental Apology, etc., 1799  
Caledonia, 1807  
W. and R. Chambers, Book of Days, 1863  
V. E. P. Chasles, Études sur Shakespeare, Paris, 1851  
Chevalier de Chatelain, Macbeth, traduite en Vers Français, London, 1862  
Lord John Chedworth, Notes on some of the Obscure Passages of Shakespeare's Plays, London, 1805  
C. Cowden-Clarke, Shakespeare Characters, etc., 1863  
P. W. Clayden, Macbeth and Lady Macbeth (Fortnightly Review, 1 August), 1867  
J. Coleman, Gentleman's Magazine, March, 1889  
S. T. Coleridge, Notes and Lectures upon Shakespeare, 1849  
Seven Lectures on Shakespeare and Milton (ed. Collier), 1856  
J. P. Collier, Annals of the Stage, 1831  
New Particulars, etc., 1836  
Notes and Emendations, 1853  
H. Corson, Chaucer's Legende of Goode Women, Boston, 1864  
Introduction to Shakespeare, 1889  
R. Cotgrave, Dictionarie of the French and English Tongues, London, 1632  
G. L. Craik, English of Shakespeare (ed. Rolfe), Boston, 1872  
J. H. Crawford, Good Words, June, 1893  
W. S. Dalgleish, Macbeth, London, 1869  
P. A. Daniel, Notes and Conjectural Emendations, 1870  
J. Darmesteter, Macbeth, Paris, 1881  
T. Davies, Dramatic Miscellanies, London, 1784  
N. Delius, Macbeth, Bremen, 1841  
Die Tieck'sche Shakspere-kritik, Elberfeld, 1846  
Shakespeare-Lexikon, 1852  
Shakespeare's Dramatische Werke (ed. ii.), 1869  
T. De Quincey, Miscellaneous Essays, Boston, 1851  
E. Dowden, Shakespeare, His Mind and Art, London, 1875  
G. D'Hugues, Macbeth, Paris, 1883  
F. Douce, Illustrations of Shakespeare, London, 1807  
N. Drake, Shakespeare and His Times, 1817  
Memorials of Shakespeare, 1828  
P. Duport, Essais Littéraire sur Shakespeare, Paris, 1828  
A. Dyce, Remarks on Collier's and Knight's Editions, London, 1844  
Few Notes, etc., 1853  
Strictures on Collier's New Edition, 1859  
J. F. T. Dyer, Folk-Lore of Shakespeare, New York, 1884  
T. R. Eaton, Shakespeare and the Bible, London, 1858  
T. Edwards, Canons of Criticism (Seventh Edition), 1765  
A. J. Ellis, Early English Pronunciation, etc., 1869  
L. C. Elson, Shakespeare in Music, 1901  
H. Elwin, Shakespeare Restored, Norwich, 1853  
K. Elze, Notes on Elizabethan Dramatists, Halle, 1889  
J. J. Eschenburg, Shakespeare's Schauspiele, Strassburg, 1776  
R. Farmer, Essay on the Learning of Shakespeare, London, 1767  
J. C. Fick, Macbeth, with German Notes, Erlangen, 1812  
H. Fietkau, Schiller's Macbeth, Königsberg, 1897  
P. Fitzgerald, Life of Garrick, London, 1868  
J. L. F. Flathe, Shakespeare in seiner Wirklichkeit, Leipzig, 1863  
F. G. Fleay, Shakespeare Manual, London, 1876  
F. G. Fleay, Life and Work of Shakespeare, London, 1886  
G. Fletcher, Studies of Shakespeare, 1847  
R. Fletcher, Witches Pharmacopoeia, Baltimore, 1896  
R. Forby, Vocabulary of East Anglia, London, 1830  
J. Florio, A World of Words, 1598  
J. Ford, Works (ed. Gifford), 1869  
E. Forsyth, Some Notes on Shakespeare's Character and Writings, 1867  
C. L. Francke, Macbeth sprachlich und sachlich erläutert, Braunschweig, 1833  
G. R. French, Shakespeareana Genealogica, London, 1869  
F. Fritzart, War Shakespeare ein Christ ?, Heidelberg, 1832  
F. Friesen, Shakespeare von Gervinus, Leipzig, 1869  
F. J. Furnivall, Introduction to Leopold Shakespeare, London, 1877  
R. Genée, Geschichte der Shakespear'schen Dramen in Deutschland, Leipzig, 1870  
G. G. Gervinus, Shakespeare, 1862  
H. Giles, Human Life in Shakespeare, Boston, 1868  
A. H. Gilkes, Electra and Macbeth, London, 1880  
St. M. Girardin, Cours de Litterature Dramatique, Paris, 1845  
T. R. Gould, The Tragedian, London, 1868  
G. Gould, Corrigenda, etc., 1884  
H. Green, Shakespeare and the Emblem Writers, 1870  
Z. Grey, Critical, Historical, and Explanatory Notes on Shakespeare, 1754  
Mrs Griffiths, Morality of Shakespeare's Dramas, 1775  
Sir G. Grove, Dictionary of Music, 1890  
E. Guest, History of English Rhythms, 1838  
M. Guizot, Œuvres complètes de Shakespeare (ed. vii.), Paris, 1821  
Shakespeare et son Temps (Nouvelle Edition), 1869  
W. E. Hales, Notes and Essays, London, 1884  
H. Hallam, Introduction to the Literature of Europe, 1855  
Dr R. P. Harris, Tolerance in Pregnant Women, Philadelphia, 1892  
J. E. Harting, Ornithology of Shakespeare, London, 1871  
W. Hazlitt, Characters of Shakespeare's Plays, 1817  
F. F. Heard, Legal Acquirements of Shakespeare, Boston, 1865  
Shakespeare a Lawyer, 1883  
B. Heath, A Revisal of Shakespeare's Text, London, 1765  
C. Hebler, Aufsätze über Shakespeare, Bern, 1865  
H. Heine, Shakespeare's Mädchen und Frauen, Philadelphia, 1839  
C. Heinichen, Macbeth, Bonn, 1841  
J. Henry, Æneidea, or Critical, Exegetical, and Æsthetical Remarks on the Æneis, Dublin, 1881  
L. Herrig, Macbeth, Berlin, 1853  
C. C. Heuse, Vorträge über Shakespeare, etc., Halberstadt, 1856  
J. A. Heraud, Shakespeare's Inner Life, London, 1865  
R. H. Hiecke, Macbeth, erläutert und gewürdigt, Merseburg, 1846  
L. Hilsenberg, Shakespeare's Dramatische Werke, Leipzig, 1836  
E. Hills, Notes & Queries, 2 October, 1869  
C. W. Hodell, Poet Lore, vol. xiii, No. 2, 1901  
Holinshed, Chronicles, London, 1587  
C. Hollyband, French Dictionary, 1593  
F. Hörn, Shakespeare's Schauspiele Erlaütert, Leipzig, 1823  
H. N. Hudson, Shakespeare: His Life, Art, and Character, Boston, 1872  
François-Victor Hugo, Œuvres complètes de Shakespeare, Paris, 1859  
V. Hugo, William Shakespeare, 1864  
E. Hülseman, Shakespeare, sein Geist und seine Werke, Leipzig, 1856  
Joseph Hunter, New Illustrations of Shakespeare, London, 1853  
Few Words, etc., 1853  
Rev. John Hunter, Macbeth, 1869  
C. M. Ingleby, The Shakespeare Fabrications, 1859  
Henry Irving, Nineteenth Century, April, 1877  
Macbeth, as produced at the Lyceum, 1889  
Character of Macbeth (Lecture delivered at Owens College, Manchester, 11 December), 1894  
Z. Jackson, Shakespeare's Genius Justified, 1819  
A. Jacob, Macbeth, Berlin, 1848  
Mrs Jameson, Characteristics of Women, London, 1833  
M. Jastrow, Jr., Poet Lore, vol. ii., 1890  
J. Jekeli, Die Gesetze der Tragödie nach gewiesen an Shakespeare's Macbeth, Hermanstadt, 1873  
F. Jencken, Macbeth, Mainz, 1855  
S. Jervis, Proposed Emendations, etc., London, 1860  
S. Johnson, Miscellaneous Observations on Macbeth (Works, ed. 1825), 1745  
B. Jonson, Works (ed. Gifford), 1816  
I. M. Jost, Erklärendes Wörterbuch zu Shakespeare's Plays, Berlin, 1840  
J. J. Jusserand, Shakespeare in France, London, 1899  
F. Kaim, Shakespeare's Macbeth, Stuttgart, 1888  
P. Kaufmann, Shakespeare's Dramatische Werke, Berlin, 1830  
T. Keightley, Shakespeare Expositor, London, 1867  
Keller und Rapp, Shakespeare's Dramatische Werke, Stuttgart, 1843  
Mrs F. A. Kemble, Some Notes upon the Characters in Macbeth (Macmillan's Magazine, May), 1867  
Lady Macbeth (Macmillan's Magazine, May), 1867  
J. P. Kemble, Macbeth, as represented on opening Drury Lane Theatre, 21st of April, London, 1786  
Macbeth Reconsidered, 1786  
Macbeth and Richard the Third, 1817  
Kemp's nine daies wonder (Dyce's reprint), 1600  
B. G. Kinnear, Cruce's Shakespeariana, 1883  
J. S. Knowles, Lectures on Dramatic Literature, 1843  
E. Kölbing, Byron und Shakespeare's Macbeth (Englische Studien, xix, 2), 1894  
R. Koppel, Shakespeare-Studien, Berlin, 1896  
J. Körner, Shakespeare's Dramatische Werke, Wien, 1836  
F. Kreyssig, Vorlesungen über Shakespeare, Berlin, 1862  
Shakespeare-Fragen, 1871  
K. Lachmann, Macbeth, Berlin, 1829  
A. Lacroix, Histoire de l' Influence de Shakespeare sur le Théâtre Français, Bruxelles, 1856  
A. de Lamartine, Shakespeare et son Œuvres, Paris, 1865  
C. Lamb, Dramatic Poets (ed. Bohn, 1854), London, 1808  
R. J. Lane, Charles Kemble's Shakspere Readings, 1870  
G. Langbaine, English Dramatic Poets, Oxford, 1691  
B. Laroche, Œuvres complètes de Shakespeare (ed. v.), Paris, 1842  
S. Lee, Life of William Shakespeare, London, 1898  
W. Leighton, Robinson's Epitome of Literature, 15 April, 1879  
T. Lennig, Macbeth (Penn Monthly, May), 1870  
F. A. Leo, Shakespeare's Frauen-Ideale, Halle, 1868  
Macbeth, 1871  
M. F. Libby, Some New Notes on Macbeth, Toronto, 1893  
W. W. Lloyd, Essays on Shakespeare, London, 1858  
T. R. Lounsbury, Shakespeare as a Dramatic Artist, New York, 1901  
O. Ludwig, Shakespeare-Studien, Leipzig, 1872  
G. MacDonald, A Disk of Orts, London, 1895  
W. Macready, Reminiscences (ed. F. Pollock), 1875  
W. Maginn, Shakespeare Papers, 1860  
Lady Martin, Some of Shakespeare's Female Characters, Edinburgh, 1891  
J. M. Mason, Comments on the Last Edition of Shakespeare, London, 1785  
Comments on the Plays of Beaumont & Fletcher, 1798  
Comments on the Several Editions of Shakespeare, 1807  
P. Massinger, Works (ed. Gifford), 1805  
G. Massey, Secret Drama of Shakespeare's Sonnets Unfolded, 1872  
Ad. Meyer, Shakespeare's Verletzung der historischen und natürlichen Wahrheit, Schwerm, 1863  
E. Meyer, Shakespeare's Dramatische Werke, Hamburg, 1825  
A. Mézières, Shakespeare, ses Œuvres et ses Critiques, Paris, 1860  
F. Michel, Œuvres complètes de Shakespeare. Précédée de la vie de Shakespeare par (Thomas Campbell), 1855  
T. Middleton, Works (ed. Dyce), London, 1843  
The Witch, 1778  
C. Mitchell, Essay on the Character of Macbeth (A Reply to Fletcher), 1846  
J. Mitford, Cursory Notes, etc., 1856  
M. Max Moltke, Shakespeare's Dramatische Werke, Leipzig, n. d.  
J. P. Morris, Glossary of the Words and Phrases of Furness, London, 1869  
R. G. Moulton, Shakespeare as a Dramatic Artist, Oxford, 1893  
J. Moyes, Medicine in Shakespeare, Glasgow, 1896  
M. Mull, Macbeth, London, 1889  
R. Nares, Glossary (ed. Halliwell and Wright), 1888  
G. Neilson, Scottish Antiquary, October, 1897  
New Exegesis of Shakespeare, 1859  
New Shakespeare Society (Transactions), 1877-9  
J. Nichols, Literary Illustrations, etc., 1817  
Notes on Shakespeare, 1861  
M. Leigh-Noel, Lady Macbeth, London, 1884  
Notes & Queries, 1873-1901  
J. G. Orger, Notes on Shakespeare's Histories and Tragedies, 1890  
E. Ortlepp, Shakespeare's Dramatische Werke, Stuttgart, 1838  
Oxon, Analysis and Study of the Characters in Macbeth, London, 1886  
A. P. Paton, Few Notes on Macbeth, Edinburgh, 1877  
R. Patterson, Natural History, etc., London, 1838  
F. Peck, Memoirs of Milton, 1740  
Sir Philip Perring, Hard Knots in Shakespeare (ed. ii.), 1886  
M. Petri, Zur Einführung Shakespeare's in die Christliche Familie, Hanover, 1868  
R. Pitcairn, Ancient Criminal Trials in Scotland, Edinborough, 1822  
J. R. Planché, British Costume, London, 1846  
K. L. Pörschke, Ueber Shakespeare's Macbeth, Königsberg, 1801  
Lin Rayne, Macbeth, Arranged for Dramatic Reading, 1868  
Henry Reed, English History and Poetry, London, 1869  
J. Rees, Life of Edwin Forrest, Philadelphia, 1874  
J. W. Redhouse, Academy, 24 July, 1886  
Miss A. Repplier, Fireside Sphinx, 1901  
J. E. Riddle, Illustrations of Aristotle from Shakespeare, Oxford, 1832  
W. Richardson, Essays on Shakespeare's Dramatic Characters, London, 1797  
J. Ritson, Remarks Critical and Illustrative, etc., 1783  
J. G. Ritter, Programm der Realschule zu Leer, 1871  
J. Forbes-Robertson, Macbeth, 1898  
A. Roffe, Handbook of Shakespearian Music, 1878  
E. Roffe, Essay Upon the Ghost Belief of Shakespeare, 1851  
Rossi and Corbould, Side-lights on Shakespeare, 1897  
H. T. Rötscher, Cyclus Dramatische Charaktere, Berlin, 1844  
Die Kunst der Dramatischen Darstellung, 1864  
Shakespeare in seinen höchsten Charakter-bilden, 1864  
Harry Rowe, Macbeth (Second Edition), London, 1799  
H. I. Ruggles, Method of Shakespeare, New York, 1870  
G. Rümelin, Shakespeare-Studien, Stuttgart, 1866  
W. L. Rushton, Shakespeare a Lawyer, London, 1858  
Shakespeare's Legal Maxims, 1859  
Shakespeare Illustrated by Old Authors, 1867  
Shakespeare's Testamentary Language, 1869  
Shakespeare Illustrated by the Lex Scripta, 1870  
W. B. Rye, England as seen by Foreigners, 1865  
G. Sarrazin, Shakespeare's Macbeth und Kyd's Spanische Tragödie (Englische Studien, xxi, 2), Berlin, 1895  
A. W. Schlegel, Lectures (trans. by J. Black), London, 1815  
Schlegel und Tieck, Shakespeare's Dramatische Werke, Berlin, 1833, 1855  
J. Schiller, Macbeth, Leipzig, 1801  
R. Scot, Discoverie of Witchcraft, 1584  
A. Schwartzkopf, Shakespeare in seiner bedeutung für die Kirche in unserer Tage, Halle, 1864  
Sir W. Scott, Miscellaneous Essays, Philadelphia, 1826  
E. H. Seymour, Remarks, Critical, Conjectural, and Explanatory, on Shakespeare, London, 1805  
Shakespeare Society's Publications, 1850  
K. Simrock, Shakespeare als Vermittler, etc., Hildburghausen, 1842  
Die Quellen des Shakespeare, 1870  
S. W. Singer, Text of Shakespeare Vindicated, London, 1853  
W. W. Skeat, Notes on English Etymology, Oxford, 1901  
A. Skottowe, Life of Shakespeare, London, 1824  
D. J. Snider, System of Shakespeare's Dramas, St. Louis, 1877  
T. A. Spalding, Elizabethan Demonology, London, 1880  
S. H. Spiker, Macbeth, Berlin, 1826  
C. W. Stearns, Shakespeare's Medical Knowledge, London, 1865  
Stephanie der Jüngere, Macbeth, Wien, 1773  
G. Stephens, Macbeth, Earl Siward, and Dundee, London, 1876  
H. P. Stokes, Chronological Order of Shakespeare's Plays, 1878  
W. W. Story, Excursions in Art and Letters, Edinburgh, 1891  
A. Symons, Studies in Two Literatures, London, 1897  
H. Taine, Litterature Anglaise, Paris, 1866  
E. Taunton, History of Jesuits in England, London, 1901  
L. Theobald, Shakespeare Restored, 1726  
R. M. Theobald, Shakespeare Studies in Baconian Light, 1901  
Moy Thomas, Athenæum, 14 April, 1877  
A. H. Tolman, Notes on Macbeth, Baltimore, 1896  
E. Topsell, History of Serpents, London, 1608  
C. Travers, Macbeth, Boulogne, 1844  
B. Tschischwitz, Shakespeare-Forschungen, Halle, 1868  
De Ornantibus Epithetis, etc., 1871  
T. Tyrwhitt, Observations and Conjectures upon some Passages of Shakespeare, London, 1766  
H. Ulrici, Shakespeare's dramatische Kunst (trans. by A. J. W. Morrison), 1846  
J. Upton, Critical Observations on Shakespeare, 1746  
B. A. P. Van Dam, William Shakespeare: Prosody and Text, 1899  
E. Vehse, Shakespeare als Protestant, etc., Hamburg, 1851  
A. F. Villemain, Études de Litterature Ancienne et Étrangere, Paris, 1849  
F. T. Vischer, Æsthetik, oder Wissenschaft des Schönen, Stuttgart, 1846  
Shakespeare-Vorträge, 1900  
N. Voss, Shakespeare's Dramatische Werke, Leipzig, 1810, 1829  
W. S. Walker, Shakespeare's Versification, London, 1854  
Critical Examination, etc., 1860  
J. Webster, Works (ed. Dyce), 1830  
H. Wellesley, Stray Notes on the Text of Shakespeare, 1865  
K. Werder, Vorlesungen über Shakespeare's Macbeth, Berlin, 1885  
W. Wetz, Die Inneren Beziehungen Zwischen Shakespeare's Macbeth und seinen Königsdramen (Englische Studien, xvi, 1), 1891  
T. Whately, Remarks on Some of the Characters of Shakespeare (Second Edition, 1808; Third Edition, edited by Archbishop Whately, 1839), Oxford, 1785  
R. G. White, Shakespeare's Scholar, New York, 1854  
Lady Gruch's Husband (The Galaxy, May), 1870  
Words and their Use, 1871  
Studies in Shakespeare, Boston, 1886  
W. Whiter, Specimen of a Commentary on Shakespeare, London, 1794  
J. Wilson, Dies Boreales (Blackwood's Magazine, November), 1849  
W. Winter, Life and Art of Edwin Booth, New York, 1893  
C. Wordsworth, Shakespeare's Knowledge and Use of the Bible, London, 1864  
'X', Courier, 25 April, Boston, 1857

## Development

### Adding New Plays
1. Create a JSON file in `Public/Data/`
2. Follow the existing structure with scenes and Dramatis Personae
3. Update the play loading logic in `index.html`

### Customizing Analysis
- Modify the analysis modes in the JavaScript functions
- Add new critics lists for additional plays
- Extend the New Variorum integration

## Browser Compatibility

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## Contributing

This project welcomes contributions for:
- Adding new plays or improving existing ones
- Enhancing the analysis tools
- Expanding the critics database
- Improving accessibility and usability

## License

- **Software** (code, scripts, UI): [MIT License](LICENSE)
- **JSON corpus** (`Public/Data/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Citation & archival deposit

Development repository: [github.com/bradrcarson/Shakespeare-Variorum](https://github.com/bradrcarson/Shakespeare-Variorum)

Archival release (Zenodo): [doi.org/10.5281/zenodo.21126208](https://doi.org/10.5281/zenodo.21126208)

> Carson, J. (2026). *Shakespeare Digital New Variorum: Corpus, Alignment Pipeline, and Analysis Platform* (v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.21126208

See also [`CITATION.cff`](CITATION.cff) for machine-readable citation metadata.

## Acknowledgments

- New Variorum Shakespeare series
- Historical Shakespeare scholars and critics
- Modern digital humanities community
- Open source web technologies

---

**Version**: 2.0  
**Last Updated**: 2024  
**Maintainer**: Shakespeare Variorum Digital Project
