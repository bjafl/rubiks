# LL Catalog Exploration — Funn og metodeanalyse

**Dato:** 2026-06-11  
**Verktøy:** `megaminx/ll_catalog.py`, `scripts/gen_ll_catalog.py`  
**Søkestrategi:** Uttømmende DFS med rene LL-bevarende algoritmer

---

## Nøkkelfunn

### CO-stadiet: fullstendig løst med ⟨R, U⟩

16 AUF-klasser (Burnside: 80 tilstander / 5 = 16), alle løst med rene LL-bevarende sekvenser.  
Middelverdi: **7,4 trekk**. Maks: **11 trekk** (én kanttilfelle).

| Case    | CO-tilstand        | Len | Struktur        | Algoritme                            |
|---------|--------------------|-----|-----------------|--------------------------------------|
| co_002  | [0,0,1,0,2]        | 1   | AUF only        | `U--`                                |
| co_011  | [0,2,1,1,2]        | 1   | AUF only        | `U`                                  |
| co_003  | [0,0,1,1,1]        | 7   | R- [core] R     | `R- U- R U- R- U++ R`               |
| co_008  | [0,1,2,1,2]        | 7   | R- [core] R     | `R- U++ R U++ R- U R`               |
| co_010  | [0,2,0,2,2]        | 7   | R- [core] R     | `R- U++ R U R- U++ R`               |
| co_000  | [0,0,0,1,2]        | 8   | repeat ×2       | `(R U++ R- U) × 2`                  |
| co_005  | [0,0,2,2,2]        | 8   | —               | `R- U- R U-- R- U-- R U--`          |
| co_006  | [0,1,0,1,1]        | 8   | —               | `R U-- R- U-- R U- R- U++`          |
| co_012  | [0,2,1,2,1]        | 8   | —               | `R- U- R U- R- U++ R U--`           |
| co_014  | [1,1,1,1,2]        | 8   | —               | `R- U- R U-- R- U-- R U++`          |
| co_015  | [1,2,2,2,2]        | 8   | —               | `R- U-- R U R- U R U++`             |
| co_001  | [0,0,0,2,1]        | 9   | R- [core] R     | `U R- U-- R U R- U R U-`            |
| co_004  | [0,0,2,0,1]        | 9   | —               | `U- R U R- U R U-- R- U-`           |
| co_007  | [0,1,1,2,2]        | 9   | R- [core] R     | `U R- U++ R U++ R- U R U-`          |
| co_013  | [0,2,2,1,1]        | 9   | —               | `U++ R- U-- R U R- U R U-`          |
| co_009  | [0,1,2,2,1]        | 11  | R- [core] R     | `R- U- R U- R- U R U- R- U++ R`    |

**Lengdefordeling:** {1:2, 7:3, 8:6, 9:4, 11:1}

#### Strukturelle egenskaper

- **Alle algoritmer er strengt LL-bevarende**: ikke-LL-brikker (hjørner og kanter utenfor U-laget) forblir uforstyrret — verifisert ved DFS-konstruksjon.
- **7 selvinferse tilfeller**: co_003, co_007, co_008, co_010, co_011, co_002 (via AUF), og noen 9m-tilfeller — algoritmen er sin egen inverse (brukt to ganger returnerer til løst).
- **2 inverse par**: co_001 ↔ co_012, co_005 ↔ co_015.
- **Konjugat-familien** `R- [U-kjerne] R` dekker co_003, co_007, co_008, co_010 — samme ytre ramme, ulik indre U-sekvens. Lettlært.

#### CO-algoritmer skrambler alltid LL CP og EP

Etter enhver CO-algoritme: CO=0 ✓, ikke-LL intakt ✓, men  
LL-CP og LL-EP er alltid skramblede (ingen CO-algoritme bevarer dem).  
CP-syklustyper etterpå: (3-syklus), (5-syklus), eller (dobbel 2-syklus).  
EP-syklustyper etterpå: tilsvarende.

---

### EP-/CP-stadiene: strukturell begrensning

**Hovedfunn:** Med enkle trekkset ⟨R,U⟩ eller ⟨R,F,U⟩ er det umulig å løse EP eller CP  
*separat* (mens ikke-LL og CO bevares) med ≤12 trekk.

**Årsak:** R-trekket sykler 2 LL-hjørner og 3 ikke-LL-hjørner i samme 5-syklus  
`(6→14→17→19→7)`. For at ikke-LL-brikkene skal komme tilbake, må R- og R  
kansellere nøyaktig — dette begrenser drastisk hvilke LL-permutasjoner som er  
oppnåelige per trekklengde.

**Viktig: EP og CP er sammenvevd.** Av 6936 kommutatorbaserte algoritmer som endrer CP  
(rene LL, ikke-LL intakt) i søkerommet ⟨R,F,U⟩, endret *alle* også EP.  
Det finnes ingen korte «rene CP»- eller «rene EP»-algoritmer med enkle trekkset.

---

### Fc1 / Fc2: rene LL-kant-3-sykler (6 trekk)

```
Fc1 = F R U R- U- F-   (6 trekk)
Fc2 = F U R U- R- F-   (6 trekk, invers av Fc1)
```

**Effekt av Fc1:**
- EP: sykler LL-kanter: plass 8 → 29 → 27 (3-syklus, to andre kanter uberørt)
- Ikke-LL-kanter: **ingen endring** ✓
- Ikke-LL-hjørner: **ingen endring** ✓
- CO-skade: `[0, 0, 2, 1, 0]` ved LL-plasser → tilsvarer CO-tilfelle **co_001**

**Nøkkelegenskap:** Fc1-CO-skaden tilsvarer alltid co_001 (etter AUF-normalisering).  
Det betyr: etter én Fc1-sekvens, fix CO med co_001-algoritmen (9 trekk).  
Fc1 + CO-fix = ~15 trekk per EP-steg.

---

## Metodeanbefalinger

### A) Streng ren-LL-metode (CO→EP→CP med tre rene stadier)
- CO: fullt løst ✓  
- EP: krever >12 trekk med ⟨R,F,U⟩ ✗  
- CP: krever >11 trekk med ⟨R,U⟩ ✗  
**→ Ikke gjennomførbart med enkle trekkset.**

### B) Fc1 + CO-fix-syklus
1. CO: katalogalgoritme (7–11 trekk)
2. EP: Fc1/Fc2 (6 trekk, aksepterer CO-forstyrrelse) + CO-fix etterpå (~9 trekk)
3. CP: hjørne-3-syklus (TBD) + CO/EP-fix

Totalt LL: ~30–45 trekk. Systematisk men langt.

### C) Anbefalt: CO-katalog + semi-intuitiv PLL

```
Fase 1: CO  — 16 katalogtilfeller, 1–11 trekk (snitt 7,4)
Fase 2: PLL — primitiv-sett:
    • Fc1/Fc2: kant-3-syklus (6 trekk)
    • Hjørne-3-syklus: [mangler fortsatt, ~8–12 trekk]
    • AUF-oppsett + utfør + AUF-avslutning
```

**Primitivt sett å lære (~12 algoritmer totalt):**
1. `R- U- R U- R- U++ R` — co_003, 7 trekk (Anti-Sune-konjugat)
2. `R- U++ R U++ R- U R` — co_008, 7 trekk
3. `R- U++ R U R- U++ R` — co_010, 7 trekk
4. `(R U++ R- U) × 2`    — co_000, 8 trekk (repetisjonsmønster)
5. co_001-alg (+ brukes som Fc1-CO-fix): `U R- U-- R U R- U R U-`
6–10. Resterende CO-algoritmer (co_004, co_005, co_006, co_007, co_009 m.fl.)
11. `F R U R- U- F-` — Fc1, kant-3-syklus
12. `F U R U- R- F-` — Fc2, invers kant-3-syklus
13. [Hjørne-3-syklus, TBD]

---

## Neste steg

- [ ] Finn en kort, minneverdig **hjørne-3-syklus** (ren LL, ikke-LL intakt)
- [ ] Evaluer om kombinert EP+CP (etter CO) kan gjøres med ~2 primitiver
- [ ] Beregn forventet totalt trekktall for anbefalt metode
- [ ] Vurder om noen CO-algoritmer kan doble som PLL-hjelpemiddel

---

## Teknisk notis: Sune vs. katalogalgoritmer

Sune (`R U R- U R U++ R-`, 7 trekk) bryter med katalogkravet: den  
**forflyttes ikke-LL-brikker** (hjørne 18 og 17 bytter plass over LL-grensen).  
Katalogalgoritmen `R- U- R U- R- U++ R` (co_003) løser den nærmeste CO-klassen  
uten noen ikke-LL-forstyrrelse. Disse er *ikke* samme algoritme — katalogversjonene  
er strengere og verifisert korrekte for rent LL-arbeid.
