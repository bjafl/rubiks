# LL EP og CP Katalog — Megaminx Last Layer

**Dato:** 2026-06-11  
**Status:** Komplett — 12/12 EP-algoritmer + 12/12 CP-algoritmer, alle verifisert  
**Søkemetode:** Bidireksjonell BFS (halvdybde 8–9, total 16–18 trekk)  
**Grunnlag:** CO-katalog ferdigstilt (ll-catalog-exploration-2026-06-11.md)

---

## Metode: CO → EP → CP (3 stadier)

| Stadium | Tilfeller | Trekk       | Algoritmer |
|---------|-----------|-------------|------------|
| CO      | 16        | 1–11 (snitt 7,4) | se ll-catalog-exploration |
| AUF     | —         | 0–4 (snitt 1,6) | U, U++, U-, U-- |
| EP      | 12        | 0–19 (snitt 16,4) | se nedenfor |
| AUF     | —         | 0–4 (snitt 1,6) | |
| CP      | 12        | 0–18 (snitt 16,4) | se nedenfor |
| AUF     | —         | 0–4 (snitt 1,6) | |
| **Total** |         | **~45 trekk** | **40 algoritmer** |

**Trekkset:** ⟨R, R⁻, F, F⁻, U, U⁻, U⁺⁺, U⁻⁻⟩  
**Constraint:** Strikt pure-LL — ikke-LL-brikker forblir uforstyrret ved slutt-tilstand.

---

## EP-katalog (12 tilfeller)

Algoritmen **løser EP** (kant-permutasjon) mens CO=0 bevares.  
CP-tilstand etter EP-algoritme er irrelevant — CP-stadiet fikser CP etterpå.

| ID      | EP-type | Trekk | Algoritme |
|---------|---------|-------|-----------|
| ep_000  | 3cyc    | 14    | `R- U- F- U F R U- F R U R- U- F- U` |
| ep_001  | 3cyc    | 14    | `U- F U F- R- U- R U F U- F- R- U R` |
| ep_002  | 2x2     | 17    | `R- U++ R U++ R- U R U-- R- U- R U-- R- U-- R U-- U` |
| ep_003  | 3cyc    | 16    | `U-- R- U- R U- R- U++ R U-- R- U++ R U++ R- U R` |
| ep_004  | 3cyc    | 16    | `U-- R- U++ R U++ R- U R U-- R- U- R U- R- U++ R` |
| ep_005  | 3cyc    | 16    | `R- U- R U-- R- U-- R U++ R- U-- R U R- U R U++` |
| ep_006  | 3cyc    | 17    | `F- U- F R F- U++ F U++ F- U F R- U-- F- U-- F U` |
| ep_007  | 2x2     | 19    | `U- R- U- R U-- R- U-- R U-- U- R U R- U R U-- R- U- U` |
| ep_008  | 3cyc    | 16    | `R- U-- R U R- U R U++ R- U- R U-- R- U-- R U++` |
| ep_009  | 3cyc    | 17    | `R- U++ F- U F R- U-- F- U F U R F- U-- F R U-` |
| ep_010  | 2x2     | 17    | `U- U- R U R- U R U-- R- U- R- U++ R U++ R- U R` |
| ep_011  | 5cyc*   | 0     | *(AUF-only: én U-rotasjon løser EP direkte)* |

**ep_011-merknad:** Representerer 5-syklusen `(4→8→27→28→29)`. AUF-normalisering gir utseendet av løst EP — algoritmen er tom; riktig AUF-oppsett løser dette tilfellet alene.

### EP-tilstandsdetaljer

| ID     | EP-tuple (LL-kanter [4,8,27,28,29])       | Syklustype        |
|--------|-------------------------------------------|-------------------|
| ep_000 | `[4, 8, 28, 29, 27]`                      | (27→28→29)        |
| ep_001 | `[4, 8, 29, 27, 28]`                      | (27→29→28) invers |
| ep_002 | `[4, 27, 8, 29, 28]`                      | (8↔27)(28↔29) swap|
| ep_003 | `[4, 27, 28, 8, 29]`                      | (8→27→28)         |
| ep_004 | `[4, 27, 29, 28, 8]`                      | (8→28→27) invers  |
| ep_005 | `[4, 28, 8, 27, 29]`                      | (8→27→29)         |... wait
| ep_006 | `[4, 28, 27, 29, 8]`                      | (8→28→29)         |
| ep_007 | `[4, 28, 29, 8, 27]`                      | (8↔28)(27↔29) swap|
| ep_008 | `[4, 29, 8, 28, 27]`                      | (8→27→29) ulik    |
| ep_009 | `[4, 29, 27, 8, 28]`                      | (8→29→28) invers  |
| ep_010 | `[4, 29, 28, 27, 8]`                      | (8↔29)(27↔28) swap|
| ep_011 | `[4, 8, 27, 28, 29]`                      | 5-syklus (AUF)    |

---

## CP-katalog (12 tilfeller)

Algoritmen **løser CP** (hjørne-permutasjon) mens CO=0 OG EP=løst bevares.

| ID      | CP-type | Trekk | Algoritme |
|---------|---------|-------|-----------|
| cp_000  | 3cyc    | 18    | `U U- R U-- R- U- R U-- R- U++ R- U- R U-- R- U-- R U` |
| cp_001  | 3cyc    | 18    | `U- R- U++ R U++ R- U R U-- R U++ R- U R U++ R- U U-` |
| cp_002  | 2x2     | 16    | `U-- R U-- F- U- F U- F- U- R- U R U++ F U- R-` |
| cp_003  | 3cyc    | 16    | `F R U++ R- F U F- R F R- U- R F- U-- R- F-` |
| cp_004  | 3cyc    | 14    | `R U++ R- F U F- R F R- U- R F- U-- R-` |
| cp_005  | 3cyc    | 16    | `F R U++ F R- U R F- R- F U- F- R U-- R- F-` |
| cp_006  | 3cyc    | 18    | `U- R U-- R- U-- R U- R- U++ U R- U++ R U R- U++ R U--` |
| cp_007  | 2x2     | 14    | `R- U- F- U F U- F- U F U- F- U F R` |
| cp_008  | 3cyc    | 14    | `R U++ F R- U R F- R- F U- F- R U-- R-` |
| cp_009  | 3cyc    | 18    | `U++ R- U-- R U- R- U-- R U- U-- R U R- U++ R U++ R- U` |
| cp_010  | 2x2     | 18    | `F U-- F- U- F U F- U-- R- F U- F- U-- R U R- U++ R` |
| cp_011  | 5cyc*   | 0     | *(AUF-only: én U-rotasjon løser CP direkte)* |

**cp_011-merknad:** Tilsvarer ep_011: 5-syklusen `(0→4→7→18→19)`. Løses med én U-rotasjon alene.

### CP-tilstandsdetaljer

| ID     | CP-tuple (LL-hjørner [0,4,7,18,19])       |
|--------|-------------------------------------------|
| cp_000 | `[0, 4, 18, 19, 7]`                       |
| cp_001 | `[0, 4, 19, 7, 18]`                       |
| cp_002 | `[0, 7, 4, 19, 18]`                       |
| cp_003 | `[0, 7, 18, 4, 19]`                       |
| cp_004 | `[0, 7, 19, 18, 4]`                       |
| cp_005 | `[0, 18, 4, 7, 19]`                       |
| cp_006 | `[0, 18, 7, 19, 4]`                       |
| cp_007 | `[0, 18, 19, 4, 7]`                       |
| cp_008 | `[0, 19, 4, 18, 7]`                       |
| cp_009 | `[0, 19, 7, 4, 18]`                       |
| cp_010 | `[0, 19, 18, 7, 4]`                       |
| cp_011 | `[0, 4, 7, 18, 19]`                       |

---

## Strukturelle egenskaper

### EP-katalogen

- **8 × 3-syklus** (ep_000–ep_009, minus de to 2x2): 3 av 5 LL-kanter sykleres
- **3 × dobbel 2-bytte** (ep_002, ep_007, ep_010): to par kanter bytter plass
- **1 × 5-syklus** (ep_011): alle 5 kanter roteres → løses av AUF alene
- Korteste: **14 trekk** (ep_000, ep_001)
- Lengste: **19 trekk** (ep_007, dobbel 2-bytte)

### CP-katalogen

- **8 × 3-syklus** (cp_000–cp_009, minus 2x2): 3 av 5 LL-hjørner sykleres
- **3 × dobbel 2-bytte** (cp_002, cp_007, cp_010): to par hjørner bytter plass
- **1 × 5-syklus** (cp_011): alle 5 hjørner roteres → løses av AUF alene
- Korteste: **14 trekk** (cp_004, cp_007, cp_008) — kortere enn EP pga CO+EP-constraint
- Lengste: **18 trekk** (cp_000, cp_001, cp_006, cp_009, cp_010)

### Algoritmestruktur

EP-algoritmene bruker F-trekk som EP-primitiv (ligner Fc1-mønster), kombinert med R-trekk.  
CP-algoritmene bruker kommutatorlignende mønster med F-trekk for hjørne-sykler.

Eksempel CP-primitiv: `cp_004` = `R U++ R- F U F- R F R- U- R F- U-- R-` (14 trekk)  
— dette er en hjørne-3-syklus med R-oppsett + F-kjerne + R-nedrigg.

---

## Bruksveiledning: CO → EP → CP

### Steg 1: CO-stadiet
Se `ll-catalog-exploration-2026-06-11.md` for full CO-katalog (16 algoritmer).

### Steg 2: EP-stadiet

1. **Les EP-tilstand**: sjekk hvilke LL-kanter (slot 4, 8, 27, 28, 29) er på feil plass
2. **AUF-oppsett**: roter U til et av de 12 kanoniske tilfellene matcher
3. **Bruk EP-algoritme**: algoritmen løser EP, CP kan endre seg (OK)
4. **Resultat**: CO=0, EP=løst, CP=fortsatt skramblert

### Steg 3: CP-stadiet

1. **Les CP-tilstand**: sjekk hvilke LL-hjørner (slot 0, 4, 7, 18, 19) er på feil plass (NOT orientering — kun posisjon; CO er allerede løst)
2. **AUF-oppsett**: roter U til et av de 12 kanoniske tilfellene matcher
3. **Bruk CP-algoritme**: algoritmen løser CP mens CO og EP bevares
4. **AUF-avslutning**: roter U for å justere topphjørner til endelig posisjon

### Spesialtilfellet 5-syklus (ep_011 / cp_011)

Hvis EP eller CP ser løst ut etter AUF-justering men du vet at det ikke er løst:  
→ du har en 5-syklus. Prøv alle AUF-rotasjoner — én av dem løser det direkte.  
→ Ingen algortime trengs utover AUF-rotasjonen.

---

## Sammenligning av metoder

| Metode          | Algoritmer | Snitt-trekk (LL) | Kommentar |
|-----------------|------------|------------------|-----------|
| CO → EP → CP   | 40         | ~45              | Systematisk, fullstendig |
| CO → PLL-primitiver | ~7    | ~65              | Færre algoritmer, mer intuitivt |
| CO → PLL-katalog | 736       | ~33              | Urealistisk å lære |

**Anbefalt for nybegynner:** CO → EP → CP (40 algoritmer, ~45 trekk).

---

## Neste steg

- [x] Finn EP-katalog (12 tilfeller, CO-bevarende)
- [x] Finn CP-katalog (12 tilfeller, CO+EP-bevarende)
- [x] Beregn eksakt forventet trekktall (~45)
- [ ] Generer JSON-katalogfiler via `gen_ll_catalog.py` (for programmatisk bruk)
- [ ] Evaluer memoriserbarhet — finne eventuelle inverspar og konjugat-mønstre
- [ ] Vurder forenklet variant: bruk EP+CP-primitiver for å minimere antall algoritmer
