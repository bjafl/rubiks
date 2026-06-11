# LL PLL Exploration — Strukturanalyse

**Dato:** 2026-06-11  
**Verktøy:** `scripts/find_pll_primitives.py`, `scripts/find_pll_catalog.py`  
**Grunnlag:** CO-katalog ferdigstilt (16 tilfeller, 1–11 trekk)

---

## Nøkkelfunn

### PLL-gruppen er A₅ × A₅ = 3600 tilstander

Etter CO er løst (CO=0), kan EP og CP permutasjonene ta alle kombinasjoner av
*jevne* permutasjoner av 5 elementer:

- EP: A₅ med 60 tilstander → 12 AUF-klasser (Burnside: 60/5)
- CP: A₅ med 60 tilstander → 12 AUF-klasser
- Kombinert: **60 × 60 = 3600 tilstander**, **719 AUF-klasser** (minus identitet)

Dette er verifisert beregnet ved gruppeorbit-BFS: alle 3600 tilstander er
nåbar fra SOLVED ved å komponere CO-algoritmer og AUF-trekk.

Sammenlignet med 3×3×3 (21 PLL-tilfeller) er Megaminx PLL dramatisk større.

### co_009 = ren EP 3-syklus (orden 3)

**co_009** (`R- U- R U- R- U R U- R- U++ R`, 11 trekk) har en spesiell dobbeltrolle:

| Eiendel         | Verdi                         |
|-----------------|-------------------------------|
| CO-effekt       | `(0, 2, 1, 1, 2)` (skade)    |
| EP-effekt       | 3-syklus `(27→29→28)`         |
| CP-effekt       | **identitet** (ingenting)     |
| Orden i gruppen | **3** (co_009³ = identitet)   |

**Orden 3 betyr:** co_009 ² = co_009 ⁻¹ (invers 3-syklus), og co_009 ³ = id.

AUF-varianter av co_009 dekker 5 distinkte EP 3-sykler (alle LL-kantpar):
```
AUF(0): 3cyc(27, 28, 29)
AUF(1): 3cyc(8, 27, 29)
AUF(2): 3cyc(4, 8, 29)
AUF(3): 3cyc(4, 8, 28)
AUF(4): 3cyc(4, 27, 28)
```

Alle disse lar CP være uendret (CP=identitet).

### EP og CP er strukturelt koblet

Fra 6936 kommutatorbaserte RL-LL-algoritmer som **endrer CP**:
→ Alle endrer også EP. Ingen ren CP-algoritme finnes med kort ⟨R,F,U⟩.

Fra co_009-familien:
→ EP kan endres uten CP (co_009 er et eksempel).

**Asymmetri**: rene EP-algoritmer eksisterer; rene CP-algoritmer er ikke funnet med korte trekksettet.

### Gruppe-statistikk

Nåbare PLL-tilstander etter type:

| CP-type  | EP-type  | Antall |
|----------|----------|--------|
| id       | id       | 1      |
| id       | 3cyc     | 20     |
| id       | 2x2swap  | 15     |
| id       | 5cyc     | 24     |
| 3cyc     | id       | 20     |
| 3cyc     | 3cyc     | 400    |
| 3cyc     | 2x2swap  | 300    |
| 3cyc     | 5cyc     | 480    |
| 2x2swap  | *        | ...    |
| 5cyc     | *        | ...    |
| **Total** | **Total** | **3600** |

---

## CO-algoritme EP/CP-bivirkninger

Når CO-algoritmene (fra SOLVED) brukes som PLL-byggeklosser:

| Algoritme | EP      | CP     |
|-----------|---------|--------|
| co_003    | 3cyc    | 2x2    |
| co_005    | 3cyc    | 2x2    |
| co_001    | 3cyc    | 2x2    |
| co_004    | 2x2     | 3cyc   |
| co_006    | 5cyc    | 3cyc   |
| co_012    | 5cyc    | 3cyc   |
| co_014    | 5cyc    | 3cyc   |
| co_015    | 5cyc    | 3cyc   |
| **co_009** | **3cyc** | **id** |
| co_000    | 2x2     | 2x2    |
| co_007    | 3cyc    | 5cyc   |
| co_008    | 3cyc    | 5cyc   |
| co_013    | 3cyc    | 5cyc   |

**co_009 er unik** — eneste CO-algoritme med CP=id.

---

## Metodekonklusjon

### Anbefalt metode: CO → EP → CP (tre stadier) ✓ FULLSTENDIG

```
Stadium 1: CO  — 16 tilfeller, 1–11 trekk (snitt 7,4)   ✓
Stadium 2: EP  — 12 AUF-tilfeller, 0–19 trekk (snitt 16,4) ✓
Stadium 3: CP  — 12 AUF-tilfeller, 0–18 trekk (snitt 16,4) ✓
```

**Totalt antall algoritmer:** 16 + 12 + 12 = **40 algoritmer**  
**Søkemetode:** Bidireksjonell BFS (halvdybde 8–9, fant alle på ≤18 trekk)

**Katalogfiler:** `ll_catalog/ep.json`, `ll_catalog/cp.json`  
**Detaljert katalog:** se `ll-ep-cp-catalog-2026-06-11.md`

### Forventet trekktall

| Stadium    | Tilfeller | Snitt-trekk | Bidrag |
|------------|-----------|-------------|--------|
| CO         | 16        | 7,4         | 7,4    |
| AUF sett   | —         | 1,6         | 1,6    |
| EP         | 12        | 16,4        | 16,4   |
| AUF sett   | —         | 1,6         | 1,6    |
| CP         | 12        | 16,4        | 16,4   |
| AUF sett   | —         | 1,6         | 1,6    |
| **Total**  |           |             | **~45**|

**Spesialtilfellet 5-syklus** (ep_011 / cp_011): løses med AUF alene (0 algoritmetrekk).
EP-3-sykluser er 14–17 trekk; EP-2x2 er 17–19 trekk. CP er tilsvarende.

### Primitiver å lære

**CO-katalog (16 algoritmer):** Fullstendig. Se ll-catalog-exploration-2026-06-11.md.

**EP-katalog (12 algoritmer):** ✓ FULLSTENDIG (14–19 trekk; 2 bruker F som primitiv).

**CP-katalog (12 algoritmer):** ✓ FULLSTENDIG (14–18 trekk; mønster: R-oppsett + F-kjerne).

---

## Algebraiske egenskaper

### co_009 er orden-3 element

```
co_009¹: CO=(0,2,1,1,2), EP=3cyc(27→29→28), CP=id
co_009²: CO=(0,1,2,2,1), EP=inv_3cyc(27→28→29), CP=id
co_009³: CO=0, EP=id, CP=id
```

### CO-skade fra co_009-familien (AUF-skift)

CO-vektoren er en syklisk skift av `(0,2,1,1,2)`:
```
AUF(0): (0, 2, 1, 1, 2)
AUF(1): (2, 0, 2, 1, 1)
AUF(2): (1, 2, 0, 2, 1)
AUF(3): (1, 1, 2, 0, 2)
AUF(4): (2, 1, 1, 2, 0)
```

Ingen kombinasjon av 3 distinkte AUF-varianter gir CO=0 (bevist).

### Praktisk bruk

Til tross for CO-skaden er co_009 nyttig som **EP-primitiv**:
- Brukt som CO-algoritme: fikser co_009-tilfellet og gir EP 3-syklus (kjent bivirkning)
- Brukt direkte: gir ren EP 3-syklus til den som allerede kjenner algoritmen fra CO-stadiet

---

## Neste steg

- [x] Beregn PLL-gruppestørrelse → 3600 (A₅×A₅)
- [x] Finn EP-katalog (12 tilfeller, CO-bevarende) — 14–19 trekk, bidireksjonell BFS
- [x] Finn CP-katalog (12 tilfeller, CO+EP-bevarende) — 14–18 trekk, bidireksjonell BFS
- [x] Beregn eksakt forventet trekktall → ~45 trekk totalt for LL
- [x] Evaluer AUF-kostnad per stadium → ~1,6 per overgang × 3 = ~4,8
