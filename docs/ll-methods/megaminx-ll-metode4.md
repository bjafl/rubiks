# Megaminx LL – Metode 4

> Full 1-look CO (OCLL) + EP + CP med Niklas
> Rekkefølge: **OCLL → EP → CP**

---

## Algoritmer — oversikt

| Steg | Antall | Kilde |
|------|--------|-------|
| OCLL | 16 | SpeedCubeDB (R=R høyre flate, U2=U++, U2'=U--) |
| EP | 5 | SpeedCubeDB / sim-verifisert |
| CP | 1 + invers | Niklas, verifisert |

---

## OCLL – Orienter alle LL-hjørner (1-look)

> **Gjenkjenning:** se på sideflater til topp-hjørnene. Tell U-farger synlig per hjørne.
> Mål: finn riktig OCLL-case → 1 app → alle 5 orientert.

Notasjon brukt her: `R` = høyre flate, `U` = topp, `++` = 144° CW.

### Sune-familien (enkle, 7 trekk)

```
CO 5  Sune       R U R- U R U-- R-
CO 6  Anti-Sune  R- U- R U- R- U++ R
CO 7             R U++ R- U- R U- R-
CO 8             R U R- U++ R U++ R-
CO 3             R U++ R- U R U++ R-
```

### Medium (9 trekk)

```
CO 2   F R U++ R- U- R U- R- F-
CO 4   R U R- U R U R- U-- R U- R-    (se: det er CO 1 alternativ form)
CO 13  R U++ R-- U- R++ U- R-- U++ R
CO 14  R- U-- R++ U R-- U R++ U-- R-
```

> CO 13/14: legg merke til `R++`/`R--` (double front-right) — beholder CO-effekten med færre U-trekk.

### Lange (11 trekk)

```
CO 1   R U R- U R U R- U-- R U- R-
CO 9   R U++ R- U- R U R- U- R U- R-
CO 10  R U R- U R U- R- U R U-- R-
CO 11  R U R- U R U R- U- R U-- R-
CO 12  R U-- R- U-- R U++ R- U-- R U- R-
CO 15  R U R- U++ R U-- R- U R U-- R-
CO 16  R U++ R- U- R U++ R- U-- R U- R-
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
EP 1  R++ U-- R-- U- R++ U-- R--          (7 trekk, verifisert: 3-sykel mot klokken)
EP 2  R++ U++ R-- U  R++ U++ R--           (7 trekk, invers av EP 1)
EP 3  R U R- F- R U R- U- R- F R++ U- R-          (13 trekk)
EP 4  R U R- U R- U- R++ U- R- U R- U R U++        (14 trekk)
```
> ⚠️ EP 5 (`UL R U++ UL- U R- UL U- R U++ UL- U++ R-`) er UGYLDIG — beveger ikke-top-brikker. Bruk bankingstrategi med EP 1/2 for å nå alle EP-tilfeller.

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
Niklas    R U- UL- U R- U- UL U    (sykler: UL-hjørne → R-hjørne → front-hjørne)
Niklas⁻¹  U- UL- U R U- UL U R-   (invers sykel)
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
| `R` | Høyre flate, 72° CW |
| `R-` | Høyre flate, 72° CCW |
| `R++` | Høyre flate, 144° CW |
| `R--` | Høyre flate, 144° CCW |
| `U` | Topp, 72° CW |
| `U++` | Topp, 144° CW (= U2 i 3×3-notasjon) |
| `U--` | Topp, 144° CCW (= U2' i 3×3-notasjon) |
| `F` | Fremre flate |
| `UL` | Øvre-venstre flate (bak-venstre) |

---

*Algoritmer verifisert i Python-simulator. CO 5/6 (Sune/Anti-Sune): U-/U++ tegn korrigert (U++ og U-- er ikke ekvivalente på Megaminx slik de er på 3×3). EP 5 ugyldig (beveger ikke-top-brikker). Niklas⁻¹ korrigert. CO 9 og CO 10 er de eneste OCLL-algoritmene som holder hjørneposisjoner uendret — de andre OCLL-algoritmene er gyldige men beveger hjørner og kanter som del av orienteringskorreksjon.*
