# Span mismatch adjudication packets (v2 tail-bounded spans)

Human review template: classify each as (a) extraction artifact, (b) witness OCR noise,
(c) genuine span mismatch / paraphrase.

## 1. Othello — ACT 2, SCENE 1 / line 2.1.256 / note 0

- Witness: `/Users/work/Projects/Shakespeare-Variorum/data/ia_cache/newvariorumediti13shak_djvu.txt`
- anchor_method: `lemma_bracket`
- full_ratio: **52.1** | tail_ratio: 57.5
- span_method: `span_estimated:note_len_323_436_tail_tail_below_threshold` | span_len_ratio: 1.09

### Note (electronic)

```
seate] COLERIDGE (Notes, &c., 255): This thought, originally by Iago’s own invention applied to Othello, is here tortuously, but exquisitely and appropriately, reverted to Iago, who is constantly placing himself by imaginative power, as it were, in the position of those with whom he is dealing, and who finally is himself caught as in a springe by the re-action of his own guilt-guided machinations.
```

### Witness span (bounded)

```
seate]  Coleridge  [Notes,  &c,  255) :  This  thought,  originally  by  Iago's  own 


act  ii,  sc.  i.]  THE  MOORE   OF   VENICE  12 1 

Doth  (like  a  poyfonous  Minerall)  gnaw  my  Inwardes  :  330 

And  nothing  can,  or  (hall  content  my  Soule 

Till  I  am  eeuen'd  with  him,  wife,  for  wift. 

Or  fayling  fo,  yet  that  I  put  the  Moore, 

At  leaft  into  a  Ielouzie  fo  ftrong 

That  iudgement  cannot  cur
```

---

## 2. The Tempest — ACT 2 SCENE 2 / line 67 / note 0

- Witness: `/Users/work/Projects/Shakespeare-Variorum/data/ia_cache/tempestnewvarior0009unse_djvu.txt`
- anchor_method: `lemma_bracket`
- full_ratio: **69.9** | tail_ratio: 54.5
- span_method: `span_estimated:note_len_1003_1357_tail_tail_below_threshold` | span_len_ratio: 1.04

### Note (electronic)

```
Saluages] REED: The Folio reads ‘saluages,’ and rightly. It was the spelling and pronunciation of the time.—DYCE: So says worthy Isaac Reed,—who ought to have known that the Folio, like other books of that date, is quite inconsistent in its spelling, e. g. [I, ii, 417, ante] it has ‘sauage’; in Love's Lab. L. IV, iii, it has ‘a rude and sauage man of Inde’; and again in the same play, V, ii: ‘That we (like sauages) may worship it.’ In Shelton's Don Quixote, Part Sec. p. 261, ed. 1620, we find, ‘foure Sauages entred the garden,’ &c., and six lines after, ‘the Saluage replied,’ &c . Not much stress, therefore, can be laid on the fact of ‘savages’ being used in both instances, and the phrase in The Tempest is more probably due to the then current stories of American travellers. Compare the following, quoted by Malone (Var. 1821): ‘Les sauvages de la Nouvelle France sont de grandes tailles, bien combines, forts & robustes, & tous vont nuds, sans se servir d’autre chose pour tout habillement d’vn cuir mal prepare, &c.,’ &c. (Lescarbot, Histoire de la Nouvelle France, Paris, 1612, p. 775); and De Laudonnière, L’histoire notable de la Floride, &c., p. 10, &c., ed. 1586. See also Gorges’s Description of New England, 1627, p. 10: ‘The Saluages are generally tall of stature, strong limbed ...’
```

### Witness span (bounded)

```
Saluages]  Reed  :  The  Folio  reads  '  salvages,'  and  rightly.  It  was  the  spell¬ 
ing  and  pronunciation  of  the  time. — Dyce  :  So  says  worthy  Isaac  Reed, — who  ought 
to  have  known  that  the  Folio,  like  other  books  of  that  date,  is  quite  inconsistent  in  its 
spelling,  e.  g.  [I,  ii,  417,  ante ]  it  has  '  sauage  ' ;  in  Love's  Lab.  L.  IV,  iii,  it  has  'a 
rude  and  sauage  man  of  Inde  ' ;  and  again  in  the  same  play,  V,  ii :  '  That  we  (like 
sauages)  may  worship  it.'  In  Shelton's  Don  Quixote,  Part  Sec.  p.  261,  ed.  1620,  we 
find,  '  foure  Sauages  entred  the  garden,'  &c.,  and  six  lines  after,  '  the  Saluage  replied,' 
&c 


ACT  II,  sc.  ii.] 


THE  TEMPEST 


13* 

Inde ?  ha?  I  haue  not  fcap'd  drowning,  to  be  afeard 
now  of  your  foure  legges :  for  it  hath  bin  faid ;  as  pro-  65 
per  a  man  as  euer  went  on  foure  legs,  cannot  make  him 
giue  ground:  and  it  fhall  be  faid  fo  againe,  while  Ste- 
phano  breathes  at'  noftrils. 

Cal.  The  Spirit  torments  me:  oh. 

Ste.  This  is  fome  Monfter  of  the  Ifle,  with  foure  legs  ;  70 

who  hath  got  (as  I  take  it)  an  Ague :  where  the  diuell 
fhould  he  leame  our  language  ?  I  will  giue  him  fome  re- 
liefe  if  it  be  but  for  that :  
```

---

## 3. Troilus and Cressida — ACT 4, SCENE 4 / line 122 / note 0

- Witness: `/Users/work/Projects/Shakespeare-Variorum/data/troilus_nv_witness.txt`
- anchor_method: `lemma_bracket`
- full_ratio: **41.2** | tail_ratio: 57.6
- span_method: `span_estimated:note_len_225_304_tail_tail_below_threshold` | span_len_ratio: 1.0

### Note (electronic)

```
morall] JOHNSON (ed. 1765): That is, the “governing principle of my understanding,” but I rather think we should read ... “motto.”—[“Moral” here may mean “a doctrine, a maxim” (SCHMIDT, 1875), or “meaning, signification.” In the latter sense, “the moral of my wit” would mean “the gist of my analysis.”]
```

### Witness span (bounded)

```
morall] motto Johns. conj.
seq.
I14. plaine and true}As quotation,
123. Faire] Om. Pope-Warb.
Johns., Var.'73,Cam.,Ktly.,Dyce
126. Pleades] Plead Han.
ii-ii, Coll. ii, Huds. ii, Wh. ii, Ard.,
[26. your] you Warb.
Kit.
126. visage] F:. vsage Q. usage Fs
After II4.l Scene VII. Pope,
et seq.
understanding,
```

---
