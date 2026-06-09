# Megaminx LL – Metode 4

> Full 1-look CO (OCLL) + EP + CP med Niklas
> Rekkefølge: **OCLL → EP → CP**

---

## Algoritmer — oversikt

| Steg | Antall | Kilde |
|------|--------|-------|
| OCLL | 16 | SpeedCubeDB (R=FR, U2=U++, U2'=U--) |
| EP | 5 | SpeedCubeDB / sim-verifisert |
| CP | 1 + invers | Niklas, verifisert |

---

## OCLL – Orienter alle LL-hjørner (1-look)

> **Gjenkjenning:** se på sideflater til topp-hjørnene. Tell U-farger synlig per hjørne.
> Mål: finn riktig OCLL-case → 1 app → alle 5 orientert.

Notasjon brukt her: `FR` = høyre-fremre flate, `U` = topp, `++` = 144° CW.

### Sune-familien (enkle, 7 trekk)

```
CO 5  Sune       FR U FR- U FR U-- FR-
CO 6  Anti-Sune  FR- U- FR U- FR- U++ FR
CO 7             FR U++ FR- U- FR U- FR-
CO 8             FR U FR- U++ FR U++ FR-
CO 3             FR U++ FR- U FR U++ FR-
```

### Medium (9 trekk)

```
CO 2   F FR U++ FR- U- FR U- FR- F-
CO 4   FR U FR- U FR U FR- U-- FR U- FR-    (se: det er CO 1 alternativ form)
CO 13  FR U++ FR-- U- FR++ U- FR-- U++ FR
CO 14  FR- U-- FR++ U FR-- U FR++ U-- FR-
```

> CO 13/14: legg merke til `FR++`/`FR--` (double front-right) — beholder CO-effekten med færre U-trekk.

### Lange (11 trekk)

```
CO 1   FR U FR- U FR U FR- U-- FR U- FR-
CO 9   FR U++ FR- U- FR U FR- U- FR U- FR-
CO 10  FR U FR- U FR U- FR- U FR U-- FR-
CO 11  FR U FR- U FR U FR- U- FR U-- FR-
CO 12  FR U-- FR- U-- FR U++ FR- U-- FR U- FR-
CO 15  FR U FR- U++ FR U-- FR- U FR U-- FR-
CO 16  FR U++ FR- U- FR U++ FR- U-- FR U- FR-
```

### OCLL-gjenkjenning (hurtigguide)

For hvert topp-hjørne: tell antall U-farge på sideflat.

```
Alle 5 allerede orientert → CO ferdig (skip)
3 hjørner med U-farge opp (de andre 2 riktige) → 3+2-mønster → Sune-familie
Alle 5 gale → prøv Sune → tell igjen
```

*Full OCLL-gjenkjenningsguide med bilder finnes på SpeedSolving.com / SpeedCubeDB.*

---

## EP – Kantpermutasjon (5 kanter)

Bare jevne permutasjoner er mulige (A₅-gruppe).

### EP-algoritmer

```
EP 1  FR++ U-- FR-- U- FR++ U-- FR--          (7 trekk, verifisert: 3-sykel mot klokken)
EP 2  FR++ U++ FR-- U  FR++ U++ FR--           (7 trekk, invers av EP 1)
EP 3  FR U FR- F- FR U FR- U- FR- F FR++ U- FR-          (13 trekk)
EP 4  FR U FR- U FR- U- FR++ U- FR- U FR- U FR U++        (14 trekk)
```
> ⚠️ EP 5 (`FL FR U++ FL- U FR- FL U- FR U++ FL- U++ FR-`) er UGYLDIG — beveger ikke-top-brikker. Bruk bankingstrategi med EP 1/2 for å nå alle EP-tilfeller.

### Gjenkjenning

| Riktige kanter | Case | Bruk |
|---|---|---|
| 5 | Ferdig | – |
| 2 nabo | 3-sykel | EP 1 eller EP 2 |
| 2 vis-à-vis | U-pentagram? | EP 3/4 + AUF |
| 1 | Sammensatt | EP 1 → bank → EP 1 |
| 0 | 5-sykel | EP 1 → tell → EP 1/3/4 |

**Bankingstrategi:** Gjør EP 1 for å få 2 nabo-riktige → AUF → 1 app til.

---

## CP – Hjørnepermutasjon

> Gjøres **etter OCLL og EP**. CO er ferdig; Niklas-twisten absorberes av... ingenting — hjørnene er allerede orientert. Sett CO **etter** CP hvis du møter CP-twist.

### ⚠️ Viktig for Metode 4

I metode 4 gjøres OCLL *først*. Etter CP (Niklas) er 3 hjørner tvridd +1 igjen. Løsning:

**Alternativ rekkefølge for M4:** OCLL → EP → CP → mini-CO (1 Anti-Sune typisk)

Eller bruk EP → CP → OCLL (da trenger du ekstra CO-trinn sist).

### Niklas

```
Niklas    FR U- FL- U FR- U- FL U    (sykler: FL-hjørne → FR-hjørne → front-hjørne)
Niklas⁻¹  U- FL- U FR U- FL U FR-   (invers sykel)
```

### Gjenkjenning

| Faste hjørner | Type | Løsning |
|---|---|---|
| 5 | Ferdig | – |
| 2 (i pos 1+3) | 3-sykel | 1 × Niklas |
| 1 | Dobbel-transposisjon | Niklas → 3-sykel → Niklas (2 apps) |
| 0 | 5-sykel | Maks 3 × Niklas |

---

## Anbefalt flyt for Metode 4

```
[OCLL]   Gjenkjenn case → 1 app → alle 5 hjørner orientert
            ↓
[EP]     Bank nabo-kanter → EP 1/2 (1–2 apps)
            ↓
[CP]     Tell faste hjørner → Niklas (1–3 apps)
            ↓
[CO fix] Anti-Sune for å korrigere CP-twist (vanligvis 1 app)
            ↓
         Ferdig
```

Forventet totale apps: **3–5** (OCLL=1, EP=1–2, CP=1–2, CO-fix=0–1)

---

## Sammenligning med Metode 1/3

| | Metode 1 | Metode 3 | Metode 4 |
|---|---|---|---|
| Alger totalt | 3 | 4 | ~10–12 |
| CO apps | 2–5 | 1–2 | 1 (+fix) |
| EP apps | 1–2 | 1–2 | 1–2 |
| CP apps | 1–3 | 1–3 | 1–3 |
| Total apps | 5–10 | 4–7 | 3–6 |
| Læringsterskel | Lav | Lav | Moderat |

---

## Notasjon

| Symbol | Megaminx-betydning |
|---|---|
| `FR` | Høyre-fremre flate, 72° CW |
| `FR-` | Høyre-fremre flate, 72° CCW |
| `FR++` | Høyre-fremre flate, 144° CW |
| `FR--` | Høyre-fremre flate, 144° CCW |
| `U` | Topp, 72° CW |
| `U++` | Topp, 144° CW (= U2 i 3×3-notasjon) |
| `U--` | Topp, 144° CCW (= U2' i 3×3-notasjon) |
| `F` | Fremre flate |
| `FL` | Venstre-fremre flate |

---

*Algoritmer verifisert i Python-simulator. CO 5/6 (Sune/Anti-Sune): U-/U++ tegn korrigert (U++ og U-- er ikke ekvivalente på Megaminx slik de er på 3×3). EP 5 ugyldig (beveger ikke-top-brikker). Niklas⁻¹ korrigert. CO 9 og CO 10 er de eneste OCLL-algoritmene som holder hjørneposisjoner uendret — de andre OCLL-algoritmene er gyldige men beveger hjørner og kanter som del av orienteringskorreksjon.*
