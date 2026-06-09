# Megaminx – Notasjon

Megaminx har to adskilte notasjonssystemer som **ikke er kompatible**:

| System | Brukes til | Kilde |
|--------|-----------|-------|
| **Algoritmenotasjon** | Beskrive løsningsalgoritmer | speedcubing-fellesskapet |
| **WCA-scramblenotasjon** | Offisielle turneringsscrambler | World Cube Association |

I tillegg finnes **SSE-notasjon** (Randelshofer) – et komplett supersett som dekker alle mulige trekk inkludert lag, snitt og rotasjoner.

---

## Flatenavn

En dodekaedr har **12 femkantede flater** arrangert i to "kroner" rundt topp og bunn.

Standardorientering: **hvit topp (U), grønn front (F)**.

### WCA/algoritmenotasjon – 12 flater

```
          U
        /   \
      UL  F  R
      |         |
      DL       L
        \   /
      B   DR
      |         |
      BL      BR
        \   /
          D
```

**Øvre krone** (U + 5 sideflater):

| Forkortelse | Fullt navn    | Posisjon (sett forfra)       |
|-------------|---------------|------------------------------|
| U           | Up            | Topp                         |
| F           | Front         | Rett foran deg               |
| R           | Right         | Høyre side                   |
| L           | Left          | Venstre side                 |
| DL          | Down-Left     | Fremre venstre (D-nabo)      |
| UL          | Upper-Left    | Bakre venstre (U-nabo)       |

**Nedre krone** (D + 5 sideflater):

| Forkortelse | Fullt navn        | Posisjon (sett forfra)       |
|-------------|-------------------|------------------------------|
| DR          | Down-Right        | Fremre høyre (D-nabo)        |
| UR          | Upper-Right       | Bakre høyre (U-nabo)         |
| BR          | Back-Right        | Bakre høyre                  |
| BL          | Back-Left         | Bakre venstre                |
| B           | Back              | Bakside (bak-bunn)           |
| D           | Down              | Bunn                         |

### SSE-notasjon – 12 flater (Randelshofer)

SSE bruker et annet navnesystem med motsatte par:

| Flate | Motflate | Beskrivelse      |
|-------|----------|------------------|
| U     | D        | Topp ↔ Bunn      |
| R     | BL       | Høyre ↔ Bakre venstre |
| F     | B        | Front ↔ Bak      |
| L     | BR       | Venstre ↔ Bakre høyre |
| UL    | DR       | Øvre venstre ↔ Nedre høyre |
| UR    | DL       | Øvre høyre ↔ Nedre venstre |

---

## Algoritmenotasjon (forenklet, mest brukt)

Brukes i løsningsalgoritmer, tutorialer og speedcubing-fellesskapet.

### Grunnregler

| Symbol | Betyr                        | Grader |
|--------|------------------------------|--------|
| `X`    | Flaten X klokkevis (CW)      | 72°    |
| `X'`   | Flaten X mot klokken (CCW)   | −72°   |
| `X2`   | Flaten X dobbelt CW          | 144°   |
| `X2'`  | Flaten X dobbelt CCW         | −144°  |

> **Merk:** På megaminx er 72° ett trekk (1/5 omdreining), ikke 90° som på 3×3.
> Doble trekk (144°) er svært vanlige siden de gir symmetriske mønstre.

### Eksempler

```
U          – topp CW
R'         – høyre CCW
R++        – høyre dobbelt CW
B-         – bak CCW
```

### Typisk algoritmeeksempel

EP-alg (kantpermutasjon, WCA-orientering):
```
R++ U-- R-- U- R++ U-- R--
```
Her brukes `++` og `--` (se WCA-scramblenotasjon nedenfor) – noen algoritmer blander systemene for nedre-kronn-trekk.

Niklas (CP):
```
R U- UL- U R- U- UL U
```

### Repetisjon og gruppering

- Parentes med tall: `(R U F)3` = sekvensen gjentas 3 ganger
- Hakeparentes brukes av og til for å markere delsekvenser

---

## WCA-scramblenotasjon

Brukes **kun** for offisielle scrambler i WCA-turneringer. Hold puslespillet med **hvit topp, grønn front**.

### Trekningstyper

Tre bevegelsestyper, alltid i par (topp er unntaket):

| Symbol | Bevegelse                                | Grader |
|--------|------------------------------------------|--------|
| `R++`  | Right: fremre-høyre sideflate CW        | 72°    |
| `R--`  | Right: fremre-høyre sideflate CCW       | −72°   |
| `D++`  | Down: nedre-venstre hjørneflate CW      | 72°    |
| `D--`  | Down: nedre-venstre hjørneflate CCW     | −72°   |
| `U`    | Up: topplaget CW                        | 72°    |
| `U'`   | Up: topplaget CCW                       | −72°   |

> `++` = med klokken, `--` = mot klokken

### Scramble-struktur

En full WCA-scramble har **7 linjer** (6 lag + rotasjon):

```
R++ D-- R++ D-- R++ D-- R++ D-- R++ D-- U
R++ D-- R++ D-- R++ D-- R++ D-- R++ D-- U
R++ D-- R++ D-- R++ D-- R++ D-- R++ D-- U
R++ D-- R++ D-- R++ D-- R++ D-- R++ D-- U
R++ D-- R++ D-- R++ D-- R++ D-- R++ D-- U
R++ D-- R++ D-- R++ D-- R++ D-- R++ D-- U'
```

Hver linje har 10 trekk + ett U/U'-trekk. Etter hvert U-trekk roterer puzzlet.

---

## SSE-notasjon (Randelshofer – komplett)

SSE (Superset English) er et komplett notasjonssystem for alle mulige trekk på megaminx. Basert på Randelshofers referanse.

### Enkeltflate-trekk

Samme regler som algoritmenotasjon, men med SSE-flatenavn (U, R, F, L, UL, UR, DR, DL, BL, B, BR, D):

```
R      – høyre CW 72°
R'     – høyre CCW 72°
R2     – høyre CW 144°
R2'    – høyre CCW 144°
```

### Lagstrekk (Tier Twists) – prefiks `T`

Roterer **to lag** (ytterste + neste) simultaneously:

```
TR     – to lag rundt høyre-aksen CW
TU'    – to lag rundt topp-aksen CCW
TF2    – to lag rundt front-aksen 144° CW
```

### Midtlag (Mid-Layer Twists) – prefiks `M`

Roterer **kun midtlaget** (ikke ytterste):

```
MR     – midtlag rundt høyre-aksen CW
MU'    – midtlag rundt topp-aksen CCW
MF2    – midtlag rundt front-aksen 144° CW
```

### Snittrotasjoner (Slice Twists) – prefiks `S`

Roterer **to motstående flater** simultaneously:

```
SR     – R + BL roterer mot hverandre CW
SF'    – F + B snitt CCW
SU2    – U + D snitt 144° CW
```

### Helrotasjoner (Puzzle Rotations) – prefiks `C`

Roterer **hele puslespillet** (ingen stykker flyttes relativt):

```
CR     – hele puzzlet roterer rundt høyre-aksen CW
CF'    – hele puzzlet roterer rundt front-aksen CCW
CU2    – hele puzzlet roterer rundt topp-aksen 144° CW
```

### Oppsummering av prefikser

| Prefiks | Bevegelse        | Eksempel |
|---------|------------------|---------|
| (ingen) | Enkeltflate      | `R`, `F'`, `U2` |
| `T`     | To lag (wide)    | `TR`, `TF'` |
| `M`     | Midtlag          | `MR`, `MU2` |
| `S`     | Snitt (slice)    | `SR`, `SF'` |
| `C`     | Helrotasjon      | `CR`, `CF2` |

---

## Kodeimplementasjon

I dette prosjektet brukes **WCA algoritmenotasjon** for flatnavn.

`FACE_NAMES` i `megaminx/moves.py`:
```python
["U", "F", "R", "L", "DL", "UL", "DR", "UR", "BR", "BL", "B", "D"]
```

Tilgjengelige trekk: `<flate>` (CW) og `<flate>-` (CCW), f.eks. `U`, `U-`, `R`, `R-`.

---

## Referanser

- [SSE 3×3 Megaminx Notation (Randelshofer)](https://www.randelshofer.ch/rubik/megaminx/doc/supersetENG_3x3_megaminx.html)
- [Megaminx Notation Guide (speedcube.com.au)](https://www.speedcube.com.au/blogs/notation-guides/megaminx-notation)
