Full Fathom Five: Transforming the New Variorum
Shakespeare Through Computational Access
Jack Carson
jdcarson@mit.edu
Abstract
This paper introduces a digital system designed to overcome persistent challenges in accessing
theNewVariorumShakespeare(NVS)editions. Ourmethodologyinvolvescomprehensivecorpus
digitization, computational bibliographic reconciliation, and adaptive interface design. The
NVS, a repository of over a century of Shakespearean scholarly endeavor, has historically been
challenging to utilize owing to its limited physical availability, antiquated textual formats, and
complex citation methods. Our solution integrates a multi-phase optical character recognition
(OCR) process with validation by large language models. It pairs the Variorum’s old-spelling
apparatus with modernized reading texts—aligned to the Folger Digital Texts for one play so
far, with the remaining plays using each edition’s own lineation—and uses computational tools
to resolve incomplete citations throughout the corpus. The developed platform offers line-by-
line access to historical annotations and incorporates experimental artificial intelligence–driven
analytical functions. These functions are grounded in public-domain reference works—C. T.
Onions’s A Shakespeare Glossary, Alexander Schmidt’s Shakespeare-Lexicon, period dictionaries
from the University of Toronto’s Lexicons of Early Modern English (LEME), and the 1599
Geneva Bible—and serve as supplementary research tools rather than foundational scholarly
resources. A two-level fidelity audit supports the corpus: an exhaustive structural check of
all 23,712 commentary entries confirmed complete, untruncated notes (100%), and a stratified
sample of 770 entries adjudicated against the original Furness page images found print fidelity of
99.7% (768 of 770), with residual disagreement confined to expected nineteenth-century OCR
noise rather than truncation or editorial invention. This project advances digital humanities
methodologies by illustrating that the infrastructure for accessing historical scholarly editions
is fundamentally different from the process of creating new critical editions. This distinction
carries substantial implications for the application, evaluation, and comparative analysis of
computational methods against TEI-based approaches. The platform currently encompasses
twenty-two of the twenty-three pre-1956 Variorum dramatic editions.
Keywords — Digital Humanities, Shakespeare Studies, Electronic Scholarly Editions, Computa-
tional Bibliography, Optical Character Recognition, Large Language Models
Introduction
The Democratic Vision and Its Technical Barriers
The title of this platform and accompanying paper is derived from Ariel’s lyrical passage in
Shakespeare’s The Tempest (1.2.396–401), which describes a father lying “full fathom five” and
undergoing a “sea-change” into something “rich and strange.” This metaphor is particularly fitting,
as it illustrates how historical scholarship, often obscured by material constraints and antiquated
1

conventions, can be transformed and made more accessible without sacrificing its fundamental
essence.
In 1871, Horace Howard Furness, a Philadelphia attorney with a dedication to amateur scholarship,
initiated a singular endeavor in the history of literary research: the New Variorum Shakespeare.
The term “variorum” originates from the Latin phrase “editio cum notis variorum,” signifying an
edition that incorporates the annotations of multiple editors and commentators. Furness appended
“new” to differentiate his project from preceding variorum editions, the most recent of which was
the Boswell–Malone edition published in 1821. His conception was groundbreaking; he aimed to
consolidate within a single publication all noteworthy commentary, glosses, interpretations, and
textual variations that had emerged concerning Shakespeare’s works since their initial printing.
This undertaking transcended mere editorial work, embodying a democratic aspiration to make the
entirety of scholarly discourse on Shakespeare, previously confined to scarce volumes in exclusive
libraries, accessible to any earnest reader. Furness articulated this vision in the preface to the
inaugural volume, stating his objective was to afford “the humblest student” the “same advantages
as the most learned professor.”
He matched the ambition with sustained labor over four decades. Working from his residence in
Philadelphia, he meticulously compiled the first volume, dedicated to Romeo and Juliet, in 1871.
This involved amassing editions and commentaries dating back to Nicholas Rowe’s 1709 edition,
recognized as the first scholarly attempt to edit Shakespeare’s plays. By the time of his passing in
1912, Furness had personally overseen the editorial process for fifteen plays in the variorum format,
encompassing the major tragedies. The series was, in the words of one subsequent scholar, “the
ultimate reference edition for Shakespeare’s works, the place where a serious student may find an
expression or at least a record of every significant critical action performed on Shakespeare’s text
up to the edition’s cutoff date” (Turner, 1986, p. 10).
Long before his death, Furness enlisted his son, Horace Howard Furness Jr., to continue the work.
Furness Jr. edited four additional plays before his death in 1930. In 1933, the New Variorum
Shakespeare became an official project of the Modern Language Association of America (MLA),
which provided institutional infrastructure and editorial oversight through the twentieth century,
publishing volumes including Marvin Spevack’s Antony and Cleopatra (1990) and Richard Knowles’s
two-volume King Lear (2020).
In 2019, the series entered a new phase when Laura Mandell negotiated with the MLA to move the
NVS to Texas A&M University and make it freely accessible online (Mandell, 2019). That project
produces new born-digital critical editions; its relationship to the present work is discussed under
Related Work below.
Yet the language of “democratic access” deserves scrutiny before it can be claimed. Furness’s
“humblest student” was, in practice, a literate reader with access to a research library, fluency in
Early Modern English conventions, and the scholarly training to navigate dense critical apparatus.
This platform removes some of those barriers, namely physical inaccessibility, citation opacity,
and archaic typography, while leaving others untouched. Internet access, English literacy, and
sufficient academic preparation to interpret variorum commentary remain prerequisites. We use the
democratic access framing not to claim the problem is solved but to identify the aspiration against
which the platform should be evaluated, and to acknowledge that computational solutions to access
barriers are necessarily partial.
2

Related Work
This project integrates three scholarly areas: the digitization of historical editions, scholarly digital
edition theory, and the application of large language models in editorial work.
The digital Shakespeare landscape is extensive, and this platform complements existing resources.
The Internet Shakespeare Editions (Best, 2008) provide modern, peer-reviewed, open-access editions
withcriticalapparatus. OpenSourceShakespeare(n.d.) offersconcordanceandsearchfunctionalities
across the canon. The New Variorum Shakespeare, now a digital-first project hosted by Texas A&M
University’s Center of Digital Humanities Research (Mandell, 2019), produces new, born-digital
critical editions encoded in TEI, meeting contemporary standards with peer-reviewed apparatus.
As of this writing, two editions have been published—The Winter’s Tale and A Midsummer Night’s
Dream—with further editions in production (New Variorum Shakespeare, 2022). However, this
project has not published digitized versions of the historical Furness volumes.
This project differs in both its stance and scope. While the A&M project re-edits individual plays
through a slow, exacting process (with only two completed), this platform offers comprehensive
access to twenty-two historical pre-1956 editions. It transmits these faithfully rather than re-editing
them. The two projects are complementary: for plays available in both, a reader gains access to
both the historical Variorum record and contemporary editorial work.
Building access infrastructure, rather than a new critical edition, is a deliberate choice that responds
to active discussions surrounding scholarly digital editions. Sahle (2016) distinguishes the digital
edition as a methodological paradigm, not merely text digitization. Pierazzo (2015) thoroughly
explains how editorial models change with the medium. This project takes a clear position in that
debate: it does not claim to produce new editorial judgment. Its authority derives from the faithful
transmission of existing printed apparatus, avoiding fresh critical intervention. Framing the work as
infrastructure with disclosed provenance, rather than as an edition, is a direct response that aligns
with the literature’s standards for what may legitimately be called an edition. The use of large
language models (LLMs), as a rapidly changing and controversial field, has been studied recently by
some researchers in regard to post-correction of poor-quality optical character recognition (OCR)
from historical texts. Boros et al. (2024) and Zhang et al. (2024) demonstrated improvements to
small-type, period typography—an aspect that this project will face.
A considerable body of evidence exists regarding how models tend to generate plausible yet fictitious
citations and unsubstantiated statements. Both Walters and Wilder (2023) and Sun et al. (2024)
have documented this problem.
Additionally, while there are several aspects of the platform’s design architecture that address
the risk of the model generating fictitious citations or unsubstantiated statements, it does so
through deterministically retrieving verbatim historical text; server-side overwrites of generated
commentary with source apparatus; and clearly labeling experimental AI output. Its contribution is
a demonstration of a conservative design pattern for generative models whereby fidelity to sources
is unyielding.
The Scope and Challenge of the New Variorum Corpus
The complete pre-1956 New Variorum Shakespeare comprises twenty-five editions: twenty-three play
editions and two editions of the non-dramatic poetry. The dramatic editions contain approximately
15,000 pages of accumulated scholarship representing over 1,000 critics, editors, and commentators
from 1709 to 1955. This project focuses exclusively on the dramatic works, as they represent the
3

core of the Variorum tradition and present the most complex challenges for line-level annotation
alignment.
This scholarly wealth remains largely inaccessible due to barriers embedded in the editorial tradition.
The Variorum maintains original folio and quarto spellings that impede comprehension for modern
readers. References frequently appear as fragments—“Cap.” for Edward Capell, “Steev.” for
George Steevens, “Clar.” for the Clarendon edition of Clark and Wright—requiring consultation
of bibliographic tables located dozens or hundreds of pages from the commentary itself. More
problematically, many significant figures are mentioned in the extensive prose introductions and
appendices but never appear in the formal bibliographic apparatus, making their identification
nearly impossible even for specialists. It should be noted that complete sets of the New Variorum
Shakespeare are scarce, with individual volumes often restricted to special collections.
Methodology and System Development
Corpus Acquisition
Digital surrogates were sourced from Internet Archive and HathiTrust for twenty-two of the twenty-
three pre-1956 NVS dramatic editions. The remaining edition, Richard II (1955), does not appear
to have been digitized by either repository; its digitization is a project the author is currently
undertaking. Thus, while twenty-three editions exist from the pre-1956 series, only twenty-two
are currently available digitally. We believe all volumes in the corpus are in the public domain in
the United States. The Folger Digital Texts, used for line alignment, are licensed under Creative
Commons Attribution-NonCommercial terms (CC BY-NC 3.0).
The twenty-two sourced editions yielded page-level scans at 300–400 dots per inch (DPI), sufficient
for optical character recognition. Each volume was triaged by scan quality: character-level clarity
in footnote regions, preservation of marginal line numbers, and presence of bleed-through or foxing.
Low-tier volumes, notably the 1877 Hamlet and the 1907 Antony and Cleopatra, received additional
manual correction passes after OCR. Where both the Internet Archive and HathiTrust had copies
of the same book, we used our discretion based upon scan quality to select the better source.
Optical Character Recognition (OCR)
While standard OCR was sufficient for the main body of text in the Variorum’s plays, it performed
poorly when applied to the footnotes. The use of abbreviated citation types at 7-point size led to
unacceptable error rates. While there were many different ways in which the OCR process went
wrong, the most common problems were: confounding of abbreviations ending with periods (e.g., “a.”
or “b.”) with sentences ending with periods; reading of italic lemma markers (the words preceding
citations) as roman; and replacing “rn” with “m” in all small type.
Processing Pipeline
There are three stages to the processing pipeline.
In stage one, raw UTF-8 text is read out of each page image to allow the pipeline to maintain some
level of spatial arrangement.
Stage two uses Google Gemini due to its one-million-token context window allowing for parallel
processing of the entire bibliography for a volume and the current page. This stage performs
4

character-levelerrorcorrection,repairstruncatedabbreviations,reunitessplitcitations,andpreserves
distinctions between italic and roman typography.
Stage three parses the processed text into act/scene boundaries, line numbers, speaker attribution,
stage direction, and distinct commentary entry using regular expressions created specifically to
conform to the Variorum’s style.
Architecture: JSON over TEI
We examined TEI and developed a working prototype of TEI-encoded Macbeth, Act 1, before
deciding on JSON. Three factors contributed to this decision.
First, since the platform requires zero-dependency static hosting—that is, the application must
run without an XML database back-end—the choice of data structure was limited by storage
space requirements. The prototype TEI document for a well-annotated version of Macbeth was
approximately 50 megabytes and simply could not be loaded quickly enough into the browser.
Second, the platform requires fast O(1) lookups at the line level. For this purpose, we chose to
represent the annotation information in a flat JSON object so that JavaScript’s native property
access could be used.
Third, the platform integrates an artificial intelligence system, and this system expects data
represented as JSON. As such, we did not want to incur additional overhead associated with
serializing and deserializing TEI documents for every API call.
There is a standard objection to this choice. Prevailing practice in digital scholarly editing treats
TEI as the archival format of record, with JSON or HTML generated downstream as delivery
formats (Sahle, 2016); on that model, the platform could have maintained TEI masters and derived
its JSON corpus from them. For a project producing a new critical edition, that hybrid architecture
is clearly correct: the TEI layer captures editorial decisions in an interchangeable, richly documented
form. But this platform introduces no new editorial content. The scholarly record it transmits
lives in the original page images and in the verbatim transcription of Furness’s apparatus, both
of which are preserved and published; a TEI intermediary would document no editorial judgment
that the transcription does not already capture, while adding an encoding and maintenance layer
with real costs and no additional scholarly yield. This is a concrete instance of the paper’s central
distinction: infrastructure for accessing historical editions is a different undertaking from creating
critical editions, and the two warrant different architectures.
Editorial Alignment
The platform uses two lineation regimes, reflecting the current state of an ongoing migration.
The Folger Digital Texts TEI serves as the alignment spine for Othello: the alignment pipeline
(scripts/folger tei/align nv to folger.py)isaversion-controlled,deterministiccomputational
task that ingests the Folger TEI source to build a linear spine of reference points—where “reference
point” refers to both the Folger act.scene.line anchors for dialogue lines and the SD * identifiers for
stage directions (SDs). Using Python’s SequenceMatcher with normalized text, each Variorum line
reference is matched against that spine, with per-play rule sets handling merged-scene edge cases.
Because the pipeline can be re-run against new or revised versions of the Folger TEI source files,
alignment errors are corrected by regeneration rather than by hand.
For the remaining plays, reading text and line keys derive from the New Variorum ingest pipeline
5

(OCR,structuredintermediatedocuments, JSON),usingeachedition’sownlineation; commentaryis
attached by scene and line number rather than by Folger anchors. The design rationale for Folger as
the alignment target—stable act-scene-line referencing, modernized spelling, open licensing—applies
corpus-wide, andextendingtheOthello-stylealignmenttotheremainingplaysisongoingengineering
work rather than current production behavior.
To address the need for a uniform editorial procedure regarding stage directions, the frontend
classifies a line as a stage direction if and only if its string representation contains an opening and
closing square bracket. That classification affects how the line is processed downstream, determining
both how speakers’ names are displayed across all twenty-two plays and how the line itself is
rendered.
Alignment Success
In the Othello alignment, matching succeeded for over 95% of line references. The residual failures
concentrated in stage directions, where the primary difficulty was determining whether an SD -
referenced item belonged to the previous or subsequent line; passages dense with stage directions
therefore aligned at lower rates than dialogue.
Fidelity
Fidelity was assessed at two levels, which should not be conflated. Structural completeness asks
whether each note in the corpus is a complete apparatus entry rather than a fragment clipped during
automated ingestion. Across the 22 plays and 23,712 notes, an exhaustive audit initially flagged
927 truncated entries (3.9% of the corpus). After repair and automated re-audit, all 927 flagged
notes were restored to complete endings, and the post-repair structural audit reported zero clipped
notes (0.0%) and no synthetic or paraphrase-style replacements. At this level the corpus is 23,712
of 23,712 structurally complete (100%): no structurally truncated entries relative to the printed
New Variorum edition.
Print fidelity is reported separately, with the printed New Variorum page—not the Internet Archive
OCR text layer used for automated witness checks—as ground truth. On stratified sampling of 35
notes per play (770 notes total), 752 scored exact or high against the witness (97.7%), 14 scored
partial(1.8%),and4failedautomatedtraceability(0.5%). Manualreviewofthose18non-exactcases
against the page images found that 16 reflected minor OCR or scan noise—for example, Capell
read as Capett, or an f/s confusion in a critic’s name—while 2 involved substantive transcription
issues, which were corrected before release. Print fidelity on the sample was therefore 768 of 770
(99.7%)afterimageadjudication, withresidualdisagreementconfinedtoexpectednineteenth-century
digitization noise rather than truncation or editorial invention. Because this figure derives from a
sample rather than an exhaustive pass, it is an estimate of corpus-wide print fidelity rather than
a census. Perfect character-for-character agreement with machine-readable witnesses is neither
achievable nor the appropriate standard for a project whose authority is the printed variorum;
reported accuracy follows print, not OCR. Residual errors are corrected as they are identified, and
because the platform serves its JSON corpus with a strict no-cache policy, corrections propagate to
users immediately.
Analysis Tier Structure
The platform provides users with three different levels of analysis: Basic (a short definition or gloss),
Expert (an extended essay, typically multi-paragraph), and Full Fathom Five (a variorum-style
6

annotation of approximately 800 to 1,200 words). Each level is serviced by a Netlify serverless
function routing to OpenAI’s API, although a parallel Deno Edge Function utilizes Anthropic’s
Claude agents as both a fallback and for purposes of A/B testing.
The platform’s AI tiers also use three public-domain works that provide lexical explanations for,
and biblical allusions behind, obscure words or phrases. For Key Words and Glosses, the system
retrieves entries from C. T. Onions’s A Shakespeare Glossary (1911; rev. ed. 1919). This standard
lexicon, compiled by an Oxford English Dictionary co-editor, focuses on obsolete words, idioms, and
Early Modern forms that may impede modern readers. Alexander Schmidt’s Shakespeare-Lexicon
(3rd ed., 1902), a classic lexicon offering broader coverage of the dramatic vocabulary, is retrieved in
parallel with Onions for the same passage lemmas; Onions remains the primary glossary in prompts
and citations, while Schmidt appears when it adds coverage or a more complete entry. Retrieved
glossary text is injected into the analysis prompt prior to the model’s invocation, ensuring that
glosses are traceable to named sources rather than undocumented model memory.
For the Sources section, the platform relies on the 1599 Geneva Bible. This English translation was
widely familiar to Shakespeare’s Protestant contemporaries.
To broaden the lexical scope beyond Shakespeare-specific reference works, we integrated materials
from the University of Toronto’s Lexicons of Early Modern English (LEME), whose transcriptions
are distributed publicly under a Creative Commons Attribution 4.0 license. Plain-text exports from
LEME were indexed server-side and are deterministically queried when a user selects a passage for
analysis. The retrieved entries are then incorporated into the model prompt and displayed in the
interface exactly as transcribed in the server-side indices, alongside matches from Onions, Schmidt,
and Geneva; the retrieved text is reproduced without LLM paraphrase at retrieval time, while the
surrounding analysis prose remains model-generated and may paraphrase. The primary objective of
this integration is not to supplant existing Shakespeare glossaries but to contextualize challenging or
historically significant diction within the contemporary lexicographical record. This approach aims
to illuminate what constituted a “hard word” in Shakespeare’s era, how such words were defined
around that time, and the semantic fields a Jacobean reader might have recognized. The indexed
English hard-word lexicons include:
(cid:136) Robert Cawdrey, A Table Alphabeticall (1604)
(cid:136) John Bullokar, An English Expositor (1616)
(cid:136) Henry Cockeram, The English Dictionarie (1623)
We also incorporated:
(cid:136) John Florio, A Worlde of Wordes (1598)
(cid:136) Randle Cotgrave, A Dictionarie of the French and English Tongues (1611)
These bilingual dictionaries were indexed by English gloss terms extracted from their entries,
particularly verbal definitions of the form “to ...”. This methodology allows a Shakespearean
lemma like abandon to retrieve contemporary Italian and French equivalents, even if it is not
a headword in an English-only lexicon. When such matches occur, the interface labels them as
“English-glossmatches”andrequirescitationbyforeignlemmaanddictionaryyear(e.g.,underItalian
Abbandonare in Florio (1598)), rather than treating them as direct English headword equivalences.
Operationally, Onions, Schmidt, and LEME are all queried in parallel for a selected passage. Onions
remains the primary Shakespeare glossary, Schmidt adds coverage and fuller entries, and LEME
7

provides period lexical context when a contemporary dictionary entry exists. In Full Fathom Five
analysis, LEME is a particularly valuable resource for the website’s sections on Key Words and
Glosses, Language and Rhetoric, and Historical Context.
As with other lexical sources, the model does not directly query LEME. Instead, matches are
computed on the server, and only the supplied text is quoted or paraphrased in the analysis. This
design ensures the scholarly record remains inspectable, allowing a curious reader to compare the
generated commentary against the exact retrieved entry.
LEME primarily contributes lemmas attested in indexed hard-word lexicons or Florio/Cotgrave
English glosses. As a result, Shakespeare-specific coinages, proper names, and many noun senses
found in bilingual dictionaries may be absent. Nevertheless, LEME provides a contemporaneous
lexical stratum that Onions and Schmidt alone cannot offer, packaged in a citable and verifiable
form.
On the website, lexical entries are deterministically retrieved from server-side indices and displayed
as transcribed in those indices, not as re-keyed facsimiles of printed pages. Onions is primarily
ingested from an Internet Archive OCR transcription, merged with the Perseus Digital Library’s
professionally keyed text where available and more complete. Schmidt is ingested from Internet
Archive OCR, with regex corrections for systematic errors (e.g., “Yen.” for “Ven.,” the abbreviation
for Venus and Adonis) and manual overrides for frequently retrieved lemmas, all applied at index-
build time. The Geneva Bible was ingested from eBible.org’s USFM edition of the 1599 text. For
its part, LEME materials use the project’s publicly distributed plain-text exports.
Of course, it is entirely possible that displayed entries may still inherit OCR or parsing artifacts.
We disclose the digital witness used, and we treat the “Retrieved Sources” panel as the citable
record of what the system actually retrieved rather than as a guaranteed diplomatic transcription
of the original edition.
Figure 1: Retrieved lexical sources before LEME integration, for Twelfth Night 1.4 (“If she be so abandon’d
to her sorrow / As it is spoke, she never will admit me”). The Retrieved Sources panel displays the entries
injectedintotheanalysisprompt,astranscribedintheplatform’sindices: sorrow fromOnions’sAShakespeare
Glossary and never and admit from Schmidt’s Shakespeare-Lexicon, each under its full bibliographic citation.
Compare Figure 2, which shows the same passage after LEME retrieval.
8

Figure 2: The same Twelfth Night passage after LEME retrieval. The Period Lexicons panel returns the
lemma abandon from two of the indexed English hard-word dictionaries—Cawdrey’s A Table Alphabeticall
(1604),glossingit“castaway,oryeeldevp,to,”andCockeram’sTheEnglishDictionarie (1623),“Toforsakeor
cast off”—together with two bilingual matches: Italian Abbandonare and French Abandonner, each explicitly
labeled as matched via the English gloss for “abandon” rather than as an English headword, and each cited
by foreign lemma and dictionary. The panel header carries the LEME attribution. The pair of figures thus
realizes the retrieval architecture described above: Onions and Schmidt supply the Shakespeare-specific
glosses (Figure 1), while LEME adds the contemporaneous lexicographical stratum, showing how the word
was defined for readers in Shakespeare’s own era.
9

While variorum notes remain the authoritative historical apparatus where available, these additional
sources provide essential lexical and scriptural grounding that the experimental AI tiers would
otherwise lack.
Full Fathom Five Prompt Requirements
The Full Fathom Five prompt requires ten specific sections of analysis in a particular order: Plain-
LanguageParaphrase; LanguageandRhetoric; Synopsis; KeyWordsandGlosses; HistoricalContext;
Sources; Literary Analysis; Critical Reception; Similar Phrases in Other Plays; and New Variorum
Analysis.
Two design decisions shaped this prompt. First, the citation requirements mandate inclusion of
at least one critic per century from the eighteenth through the twenty-first; at least one Marxist
critic; and two to three critics representing multiple critical traditions, including New Historicism,
psychoanalysis, formalism, queer theory, biography, post-colonial theory, and ecocriticism. This is a
deliberate editorial policy. While Shakespeare scholarship dominates large language models’ training
datasets, those representations are historically skewed. By requiring critics spanning centuries,
the model is pushed toward an assessment that balances historically across critics included in the
training dataset rather than relying on those most well represented in those datasets.
Second, the New Variorum Analysis section of the model’s output is unconditionally overwritten
by the backend server with verbatim historical notes retrieved from the JSON corpus, with the
overwrite occurring after completion of the LLM call and during server-side construction of the final
analysis object. Historical commentary is therefore always delivered verbatim from the corpus and
never passes through the model; it is never summarized or paraphrased.
Citation Accuracy
Because the documented risk of large language models in scholarly settings is the fabrication of
plausible but nonexistent citations (Walters and Wilder, 2023; Sun et al., 2024), we assessed citation
accuracy by layer. Named, citable references in the platform derive from the grounded retrieval
layers—the injected New Variorum apparatus, Onions, and Schmidt—where citations are drawn
from source text placed in the prompt. Across a stratified audit sample of 50 passages, the citations
traceable to these layers (162 in total) verified at 100% against the retrieved source text, with
none fabricated. This confirms the retrieval layer behaves as designed; because these citations are
grounded by construction, the result is expected rather than surprising.
The consequential question is what happens in the model-generated critical sections—Literary
Analysis, Critical Reception, and Historical Context—where the model is not quoting an injected
source. Here the Full Fathom Five prompt prohibits attribution to individual critics or works:
these sections are constrained to characterize interpretive traditions (“a Marxist reading would
emphasize ...”) rather than to cite named scholars. Across the audit sample, no named critic or
work attributions appeared in these sections, consistent with that constraint. The tier therefore
makes no verifiable bibliographic claims of its own, and the citation-fabrication failure mode is
structurally absent by design rather than merely infrequent in measurement—a stronger guarantee
than a low observed error rate, since the output form makes the fabrication of a citation impossible
rather than uncommon.
Two qualifications follow. First, prohibiting named attribution removes the risk of a false citation
but not the possibility that a generated characterization of a critical tradition is itself inaccurate;
10

the tier’s claim to reliability is that it invents no sources, not that its interpretive summaries are
authoritative, anditremainslabeledexperimentalforthatreason. Second, biblicalallusionssurfaced
in the Sources section are retrieved from the 1599 Geneva Bible text rather than generated, and so
fall under the grounded-layer guarantee rather than the model-generated one.
When running GPT-4o at a temperature of 0.7, we found hallucinations of critic names and
publication dates unacceptable. Reducing that temperature to 0.3 resulted in substantial reductions
in hallucinations. As part of the deployment strategy, the platform dynamically assigns gpt-4o for
the Full Fathom Five tier and gpt-4o-mini for all other tiers. Additionally, both functions enforce
a ninety-second timeout and provide structured error handling, ensuring that slow API responses
result in clean error messages rather than an indeterminate loading state.
Deterministic Text Matching in the Retrieval Layer
Unlikesemanticsimilarityretrievalmethodsthatproducethematicallysimilarbuttextuallydissimilar
commentary, the platform employs deterministic text matching rather than vector embedding to
determine which commentary is relevant to which piece of text. For a scholarly platform, false
positives are far worse than false negatives. Thus, rather than receiving potentially misleading
commentary from adjacent lines, users who select incorrect lines receive no commentary.
Monolithic Single-File SPA Platform Design
The platform is designed as a monolithic single-file SPA (Single Page Application) instead of a
component-based framework. A single-file SPA has zero dependency issues resulting from deprecated
dependencies and therefore does not introduce a maintenance burden that cannot be sustained
for long-term preservation. Given that a monolithic HTML/CSS/JS file can be hosted statically
anywhere indefinitely, compared to a React application that requires a build step that will fail as
dependencies become outdated, this design choice maximizes preservation options.
In addition, because everything about the application is contained within a single file, a developer
can easily view the contents of the application’s architecture through a single “View Source.” In
keeping with its open, inspection-oriented goals, this design decision helps preserve transparency.
No-Cache Policy Across Three Layers
JSON files are served with strict no-cache directives. The frontend appends cache-breaking query
parameterstoeveryJSONfetch, andtheserverlessfunctionfetchesplayJSONwithexplicitno-cache
directives for every invocation. Although this results in suboptimal delivery speed, this three-layer
no-cache policy prioritizes scholarly accuracy over delivery speed. Corrections made to erroneous
annotations should be instantly observable to subsequent users accessing content containing those
corrections.
Code Repository Design
As previously stated, all code resides in a single Git repository. Upon pushing updates to Netlify’s
main branch, Netlify triggers automatic builds for all components. Additionally, API keys are stored
within Netlify’s environment variables system and are encrypted accordingly.
11

Results and Implementation
Corpus Coverage
Table 1: New Variorum Shakespeare Digital Coverage
# Play Year Editor Status
1 Romeo and Juliet 1871 H. H. Furness Complete
2 Macbeth 1873 H. H. Furness Complete
3 Hamlet 1877 H. H. Furness Complete
4 King Lear 1880 H. H. Furness Complete
5 Othello 1886 H. H. Furness Complete
6 The Merchant of Venice 1888 H. H. Furness Complete
7 As You Like It 1890 H. H. Furness Complete
8 The Tempest 1892 H. H. Furness Complete
9 A Midsummer Night’s Dream 1895 H. H. Furness Complete
10 The Winter’s Tale 1898 H. H. Furness Complete
11 Much Ado About Nothing 1899 H. H. Furness Complete
12 Twelfth Night 1901 H. H. Furness Complete
13 Love’s Labour’s Lost 1904 H. H. Furness Complete
14 Antony and Cleopatra 1907 H. H. Furness Complete
15 Richard III 1908 H. H. Furness Jr. Complete
16 Julius Caesar 1913 H. H. Furness Jr. Complete
17 Cymbeline 1913 H. H. Furness Complete
18 King John 1919 H. H. Furness Jr. Complete
19 Coriolanus 1928 H. H. Furness Jr. Complete
20 Henry IV, Part 1 1936 S. B. Hemingway Complete
21 Henry IV, Part 2 1940 M. A. Shaaber Complete
22 Troilus and Cressida 1953 H. N. Hillebrand and T. W. Baldwin Complete
23 Richard II 1955 M. W. Black Forthcoming
The platform covers twenty-two of the twenty-three pre-1956 dramatic editions (96%), spanning
1871 to 1953.
Corpus-Wide Annotation Search
Beyond line-by-line consultation, the platform provides a search interface spanning every annotation
in the digitized corpus. In print, the Variorum functions as twenty-three separate reference works.
A scholar wishing to survey, say, Samuel Johnson’s critical activity across the canon must consult
each volume’s apparatus in turn, navigating the idiosyncratic abbreviations and eccentric index
conventions of each. The corpus-wide search collapses that labor into a single query. A user
can search all annotations by natural-language question (“What do critics say about Hamlet’s
madness?”),filterbyannotatortoretrieveeverynoteattributedtoagivencritic—Johnson,Coleridge,
Steevens, Malone, Theobald—regardless of play, or search by topic or word (“ghost,” “emendation,”
“quarto”). Each result displays the annotator, play, line, and full note text. This transforms the
New Variorum’s impenetrable apparatus into a single, queryable database of critical tradition.
This database permits a practical exploration of reception-history questions (e.g., distribution of
an editor’s attention, migration of a textual crux’s vocabulary). These inquiries were heretofore
prohibitively tedious. The search operates over the complete set of annotations in the corpus, so
results are exhaustive with respect to the digitized volumes rather than drawn from a sample or
index.
12

Figure 3: The corpus-wide annotation search interface. A query may be posed in natural language, filtered
by annotator (with one-click filters for frequently sought critics such as Johnson, Coleridge, Steevens, Malone,
and Theobald), or directed at a topic or word. Each result reports the annotator, the play and line to which
the note is attached, and the full note text.
13

Worked Example: From Line to Annotation to Analysis
Consider Hamlet 3.1.56, “To be, or not to be, that is the question.” The platform retrieves and
displays the Variorum annotation verbatim from Furness (1877):
No model summarization or paraphrase occurs for this section. The Full Fathom Five tier then
supplements this with generated literary analysis, explicitly labeled as an experimental AI feature
and requiring independent citation verification before scholarly use. The epistemological distinction
between the two outputs is enforced at both the server and display layers.
Limitations
Alignment fragility. Editorial differences between Variorum and Folger texts occasionally prevent
successfullinematching,particularlyinpassagesdensewithstagedirections. Folger-spinedalignment
is currently in production for Othello only; the remaining plays use the New Variorum editions’ own
lineation, and extending Folger alignment corpus-wide is ongoing work.
Fidelity verification. Structural completeness has been audited exhaustively across all 23,712 notes;
print fidelity, by contrast, is estimated from a stratified sample of 770 entries (99.7% print-faithful
afterimageadjudication),soasmallresidualerrorrateoutsidethesamplednotescannotbeexcluded.
The residual disagreement observed is character-level OCR or scan noise rather than truncation or
editorial invention.
AI analysis tier reliability. The lexical glosses, grounded in the Onions and Schmidt lexica, and
the plain-language summaries are the most reliable components of the AI tiers, performing well on
a task—historical lexical explanation—for which these models are well suited. The Full Fathom
Five analytical tier, which generates variorum-style commentary with full citations, requires more
caution. Readers should verify all citations in the AI analysis sections independently before scholarly
use. The in-platform label “experimental feature, verify citations before scholarly use” conveys this,
and we restate it here because formatted citations carry persuasive weight even under uncertainty
disclaimers.
Lexical witness quality. TheOnionsandSchmidtindicesderivefromOCRtranscriptionsand, despite
parser improvements and build-time corrections, can still contain character errors or fragmentary
entries. The merge of Perseus keyed text into the Onions index is populated incrementally, so
coverage of the keyed witness is currently partial.
Coverage. One volume (Richard II, 1955) has not previously been digitized; its digitization by the
author is in progress.
Sustainability. The platform incurs API costs for each Full Fathom Five request. Three structural
features mitigate long-term risk: the monolithic architecture requires no build dependencies, and the
static components will remain accessible even if AI API access is discontinued; the JSON corpus is
fully portable to any static host; and the deterministic retrieval of historical notes bypasses the LLM
entirely for the portion of the platform with the greatest scholarly reliability. The experimental
tiers are enhancements to access, not the scholarly foundation.
14

seirrac
egap
tfel
ehT
.)502–402
.pp
,7781
,ssenruF(
telmaH
muroiraV
weN
eht
ni
nwohs
sa
,1
enecS
,3
tcA
ni
telmaH
fo
yuqolilos
suomaf
ehT
:4
erugiF
,nosnhoJgnirehtag,yratnemmocehtseunitnocegapthgireht
;65eniltagninepos’yuqolilosehtgnidulcni,wolebsutarappalautxetehthtiwtxetyalpeht
.kahs11itidemuroiravwen
refiitnedi
,noitazitigid
evihcrA
tenretnI
eht
morf
segamI
.esrev
fo
enil
elgnis
a
no
ttocedlaC
dna
,bmaL
,egdireloC
,enolaM
15

Figure 5: The platform interface for Hamlet 3.1.56. The left panel displays the modernized reading text
alongside the verbatim Variorum commentary from Furness (1877), with critic abbreviations expanded.
The right panel displays the Full Fathom Five AI-generated analysis, distinguished by visual labels and a
prominent disclaimer. The New Variorum Analysis section of the AI output is replaced on the server side
with the verbatim historical notes, ensuring that the most authoritative content is always drawn directly
from the source.
Future Directions
Completing Richard II will achieve full coverage of the pre-1956 dramatic corpus. The structural
and print-fidelity audit reported above could be extended by independent human readers and by
widening the print-fidelity sample beyond 35 notes per play, tightening the estimate of corpus-wide
accuracy. Integration of the Texas A&M digital editions of the two overlapping plays would create
a complete scholarly record spanning from 1871 to the present. More systematic evaluation of Full
Fathom Five citation accuracy, across a representative sample of plays and passage types, would
establish the residual error rate and inform prompt refinement. Informal feedback from five readers
with English literature degrees indicated the platform’s lexical glosses were useful and accurate; a
structured user study would allow this finding to be assessed more rigorously.
Conclusion
When Horace Howard Furness began the New Variorum Shakespeare in 1871, he sought to democra-
tize access to centuries of accumulated scholarship. A century and a half later, complete sets of
his editions are scarce; the abbreviations he used to save space on the page have become nearly
unreadable; and the scholarship he gathered has been inaccessible not just to the humble students
he had in mind but to most researchers as well.
The platform described here makes twenty-two of those volumes findable by line number in under
a second. The historical commentary is delivered verbatim from the source. The AI features
layered on top serve a different purpose: helping a non-specialist begin to interpret 150 years of
compressed critical argument about a single line of Shakespeare. The lexical glosses, grounded
in Onions’s glossary and Schmidt’s lexicon, perform this function reliably. The Full Fathom Five
16

analytical tier, with its century-spanning citation requirement and provision for diverse critical
approaches, attempts something more ambitious, namely a historically balanced critical orientation
rather than a rehearsal of whatever critics happen to dominate the model’s training distribution.
This is a principled design goal, even as we acknowledge that citation accuracy in this tier requires
independent verification before scholarly use. Most fundamentally, we have attempted to create
infrastructure that expands rather than replaces human engagement with literary texts. The goal
is not to automate scholarship but to provide tools that enable more people to participate in the
ongoing conversation about Shakespeare that Furness began over 150 years ago.
Data and Code Availability
The platform is publicly accessible at https://newvariorum.com. The JSON corpus, alignment
scripts, and OCR pipeline are available in the project’s public GitHub repository. A citable
archival deposit of the JSON corpus and pipeline code is maintained at Zenodo (DOI: 10.5281/zen-
odo.21126208). The platform’s codebase is released under the MIT License. The JSON corpus
is released under a Creative Commons Attribution 4.0 International License (CC BY 4.0), with
one exception: the play-text fields of the Othello corpus file reproduce Folger Digital Texts and
remain subject to the Folger Shakespeare Library’s Creative Commons Attribution-NonCommercial
(CC BY-NC 3.0) license. All other play-line strings derive from New Variorum edition OCR and
are in the public domain. Folger-derived text is served on the live platform under the Folger’s
non-commercial terms.
References
Best, Michael. (2008) ‘The Internet Shakespeare Editions: Scholarly Shakespeare on the Web’,
Shakespeare, 4(3), pp. 221–233. doi:10.1080/17450910802295096.
Boros, Emanuela, Ehrmann, Maud, Romanello, Matteo, Najem-Meyer, Sven and Kaplan, Fr´ed´eric.
(2024) ‘Post-Correction of Historical Text Transcripts with Large Language Models: An
Exploratory Study’ in Bizzoni, Y., Degaetano-Ortlieb, S., Kazantseva, A. and Szpakowicz, S.
(eds)Proceedings of the 8th Joint SIGHUM Workshop on Computational Linguistics for Cultural
Heritage, Social Sciences, Humanities and Literature (LaTeCH-CLfL 2024). St. Julians, Malta:
Association for Computational Linguistics, pp. 133–159. doi:10.18653/v1/2024.latechclfl-1.14.
Bullokar, John. (1616) An English Expositor. London: John Legatt.
Cawdrey, Robert. (1604) A Table Alphabeticall. London: Edmund Weaver.
Cockeram, Henry. (1623) The English Dictionarie. London: Edmund Weaver.
Cotgrave, Randle. (1611) A Dictionarie of the French and English Tongues. London: Adam Islip.
Florio, John. (1598) A Worlde of Wordes, or Most Copious, and Exact Dictionarie in Italian and
English. London: Arnold Hatfield for Edward Blount.
Folger Shakespeare Library. (2023) Folger Digital Texts. Available at: https://www.folgerdigi
taltexts.org (Accessed: 15 March 2025).
Furness, Horace Howard. (1871) A New Variorum Edition of Shakespeare: Romeo and Juliet.
Philadelphia: J. B. Lippincott.
Furness, Horace Howard. (1877) A New Variorum Edition of Shakespeare: Hamlet. 2 vols.
Philadelphia: J. B. Lippincott.
17

Furness, Horace Howard. (1886) A New Variorum Edition of Shakespeare: Othello. Philadelphia: J.
B. Lippincott.
Furness, Horace Howard. (1901) A New Variorum Edition of Shakespeare: Twelfe Night, or What
You Will. Philadelphia: J. B. Lippincott.
The Geneva Bible. (1599) London: Deputies of Christopher Barker.
HathiTrust Digital Library. (n.d.) Digital Preservation and Access. Available at: https://www.ha
thitrust.org (Accessed: 15 March 2025).
Internet Archive. (n.d.) Digital Library of Free and Borrowable Books. Available at: https:
//archive.org (Accessed: 15 March 2025).
Knowles, Richard. (ed.) (2020) A New Variorum Edition of Shakespeare: King Lear. 2 vols. New
York: Modern Language Association.
Lancashire, Ian. (ed.) (2026) Lexicons of Early Modern English. Toronto: University of Toronto
Library and University of Toronto Press. Available at: https://leme.library.utoronto.ca
(Accessed: 15 March 2025).
Mandell, Laura. (2019) ‘Digital Future for the New Variorum Edition of Shakespeare’, MLA News,
7 November. Available at:
https://news.mla.hcommons.org/2019/11/07/new-variorum-edition-of-shakespeare
-going-digital-at-texas-am/ (Accessed: 15 March 2025).
New Variorum Shakespeare (2022) Center of Digital Humanities Research, Texas A&M University.
Available at: https://newvariorumshakespeare.org (Accessed: 15 June 2026).
Onions, C. T. (1911) A Shakespeare Glossary. 2nd edn. Oxford: Clarendon Press.
Open Source Shakespeare. (n.d.) Available at: https://www.opensourceshakespeare.org
(Accessed: 15 June 2026).
Pierazzo,Elena. (2015)Digital Scholarly Editing: Theories, Models and Methods. Farnham: Ashgate.
doi:10.4324/9781315577227.
Sahle, Patrick. (2016) ‘What Is a Scholarly Digital Edition?’ in Driscoll, M. J. and Pierazzo, E.
(eds.) Digital Scholarly Editing: Theories and Practices. Cambridge: Open Book Publishers,
pp. 19–40.
Schmidt, Alexander. (1902) Shakespeare-Lexicon: A Complete Dictionary of All the English Words,
Phrases and Constructions in the Works of the Poet. 3rd edn. Revised by Gregor Sarrazin. 2
vols. Berlin: Georg Reimer.
Spevack, Marvin. (ed.) (1990) A New Variorum Edition of Shakespeare: Antony and Cleopatra.
New York: Modern Language Association.
Sun, Yujie, Sheng, Dongfang, Zhou, Zihan and Wu, Yifei. (2024) ‘AI Hallucination: Towards
a Comprehensive Classification of Distorted Information in Artificial Intelligence-Generated
Content’,Humanities and Social Sciences Communications,11,article1278. doi:10.1057/s41599-
024-03811-x.
Turner, Robert K. (1986) ‘The New Variorum Shakespeare’, MLA Newsletter, Winter, p. 10.
Walters, W. H. and Wilder, E. I. (2023) ‘Fabrication and Errors in the Bibliographic Citations
Generated by ChatGPT’, Scientific Reports, 13, article 14045. doi:10.1038/s41598-023-41032-5.
Zhang, James, Haverals, Wouter, Naydan, Mary and Kernighan, Brian W. (2024) ‘Post-OCR
Correction with OpenAI’s GPT Models on Challenging English Prosody Texts’ in DocEng ’24:
18

Proceedings of the 2024 ACM Symposium on Document Engineering. New York: Association
for Computing Machinery, article 9, pp. 9:1–9:4. doi:10.1145/3685650.3685669.
19