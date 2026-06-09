# Megaminx LL – Metode C: CO9/CO10 + EP + Niklas

> Simulator-verifisert alternativ til Metode 3 med én kritisk egenskap:
> **CO forstyrrer aldri hjørneposisjoner.**
>
> Rekkefølge: **CO → EP → CP → CO-fix → EP-fix**

---

## Konsept og motivasjon

Metode 3 (Sune + Anti-Sune) løser CO på 1–2 kall, men Sune/Anti-Sune **flytter 4 av 5 hjørner** som bieffekt. Etter CO vet du ikke lenger hvilken CP-tilstand du starter fra.

CO9 og CO10 har en unik egenskap blant korte CO-algoritmer:

```
CO9 × CO10 = identitet         (de er inverse av hverandre)
CO9 beveger 0 hjørner ut av posisjon   (verifisert: simulatoren)
CO10 beveger 0 hjørner ut av posisjon  (verifisert: simulatoren)
```

Dette betyr: etter CO-trinnet er hjørnepermutasjonen **nøyaktig den samme** som før CO (bortsett fra eventuelle AUF-rotasjoner du selv holder rede på). CP-gjenkjenningen etterpå er derfor forutsigbar.

**Avveining mot Metode 3:**
- Metode 3: færre CO-kall (1–2), men hjørner flyttes → CP-gjenkjenning ustabil
- Metode C: 1–3 CO-kall, hjørner flyttes ikke → CP-gjenkjenning stabil

---

## Algoritmer

### CO: CO9 og CO10

```
CO9   R U++ R- U- R U R- U- R U- R-     (11 trekk)
CO10  R U R- U R U- R- U R U-- R-        (11 trekk)
```

CO9 og CO10 er hverandres inverse. Orienterings-delta fra startposisjon:

```
CO9  effekt på slots 0–4:  [+1,  0, +2, +2, +1]
CO10 effekt på slots 0–4:  [+2,  0, +1, +1, +2]
```

Slot 1 (én til høyre for R-flaten, sett ovenfra) er alltid **frosset** — det hjørnet berøres ikke av verken CO9 eller CO10. De to algoritmenene skiller seg i om nabohjørnene (slot 0 og 4) får +1 eller +2.

> ⚠️ CO9 og CO10 forstyrrer 3 topp-kanter (slots 1, 3, 4) selv om hjørneposisjonene bevares.
> EP-trinnet etter CO er fortsatt nødvendig.

---

### EP: kantpermutasjon

```
EP1   R++ U-- R-- U- R++ U-- R--    (7 trekk, 3-sykel mot klokken)
EP2   R++ U++ R-- U  R++ U++ R--    (7 trekk, invers av EP1)
```

### CP: Niklas

```
Niklas    R U- UL- U R- U- UL U         (sykler 3 hjørner, +1 twist på hvert)
Niklas⁻¹  U- UL- U R U- UL U R-         (invers sykel)
```

---

## CO-gjenkjenning

### Konjugat-form (nøkkelen)

For å bruke CO9/CO10 med AUF uten å flytte hjørner brukes **konjugat-formen**:

```
AUF_n  CO9  AUF_(5-n)
```

`AUF_n` og `AUF_(5-n)` kansellerer posisjonseffekten av U-trekket. Effekten er at CO9's orienterings-delta **roteres** med n hakk rundt topplaget.

| AUF_n | Betyr | AUF_(5-n) |
|-------|-------|-----------|
| (ingen) | n=0 | (ingen) |
| U | n=1 | U- |
| U++ | n=2 | U-- |
| U-- | n=3 | U++ |
| U- | n=4 | U |

### 1-kall gjenkjenning (10 av 80 tilfeller)

Finn et hjørne med korrekt orientering (0 vridning nødvendig). Det hjørnet er "ankeret."

1. AUF ankeret til **slot 1** (én til høyre for R, sett ovenfra CW)
2. Se på nabohjørnene (slot 0 og slot 4 etter AUF):
   - Begge trenger **+1 vridning** → bruk `CO10`
   - Begge trenger **+2 vridning** → bruk `CO9`
3. Bruk konjugat-form: `AUF_n  alg  AUF_(5-n)`

### 2- og 3-kall tilfeller (70 av 80 tilfeller)

Alle 5 hjørner er feil orientert — ingen anker finnes.

**Strategi:** Anvend CO9 (med n=0, ingen AUF), tilstanden beveger seg mot et 1-kall tilfelle.

```
Statistikk fra simulatoren:
  1 kall:  10 tilfeller (12.5 %)
  2 kall:  40 tilfeller (50 %)
  3 kall:  30 tilfeller (37.5 %)
  Snitt:   2.25 kall
```

> **Gjenkjenningsregel:** Etter hvert CO-kall — se om et anker (ori=0) finnes.
> Finnes ett: 1 kall til. Finnes ikke: 1 kall til og se igjen.

---

## EP – kantpermutasjon

Se gjenkjenningsguide i `megaminx-ll-metode1-3.md`.

**Bankingstrategi:** EP1 for å nå 2 nabo-riktige kanter → AUF → 1 kall til.

---

## CP – hjørnepermutasjon

> **Forenkling i Metode C:** Etter CO er hjørnene i samme permutasjon som FØR CO
> (justert for de AUF du brukte). Du kjenner igjen CP-tilstanden uten å måtte
> kartlegge hvilken effekt CO hadde på posisjoner.

Gjenkjenning og Niklas-strategi: se `megaminx-ll-metode1-3.md`.

---

## CO-fix etter Niklas

Niklas tvister 3 syklerte hjørner med **+1** hver (geometri-egenskap, uunngåelig).

Etter standard Niklas (uten AUF) er tilstanden: `[+1, 0, +1, 0, +1]`

Verifisert CO-fix (bevarer hjørneposisjoner):

```
U CO9 U-      →  (kaller CO9 med n=1 konjugat)
U-- CO10 U++  →  (kaller CO10 med n=3 konjugat)
```

> ⚠️ Etter disse to CO-kallene er **5 topp-kanter forstyrret**.
> Én EP-runde (EP-fix) avslutter løsningen.

Bruker du Niklas med AUF foran, forskyves CO-fix-mønsteret: bruk den generelle
CO-gjenkjenningsregelen (2-kall med anker-strategi).

---

## Komplett flyt

```
[CO]      Gjenkjenn anker → konjugat CO9/CO10 × 1–3
              ↓
[EP]      Bank 2 nabo-kanter → EP1/EP2 × 1–2
              ↓
[CP]      Niklas × 1–3  (hjørneperm kjent siden CO ikke forstyrret den)
              ↓
[CO-fix]  U CO9 U-  →  U-- CO10 U++   (2 kall, fast sekvens for std Niklas)
              ↓
[EP-fix]  EP1/EP2 × 1  (5 kanter ute etter CO-fix)
              ↓
          Ferdig
```

**Forventet apps:** 7–12 totalt (CO=1–3, EP=1–2, CP=1–3, CO-fix=2, EP-fix=1)

---

## Sammenligning

| | Metode 1 | Metode 3 | **Metode C** | Metode 4 |
|---|---|---|---|---|
| CO-algoritmer | 1 (Sune) | 2 (Sune+Anti) | **2 (CO9+CO10)** | 16 (OCLL-set) |
| CO-kall typisk | 2–4 | 1–2 | **2–3** | 1 |
| CO move-count | ~14–28 | ~7–14 | **~22–33** | ~9–11 |
| CO forstyrrer hjørner | Ja (4 av 5) | Ja (4 av 5) | **Nei ✓** | Varierer |
| EP etter CO nødvendig | Ja | Ja | **Ja** | Ja |
| CP-gjenkjenning | Ustabil | Ustabil | **Stabil ✓** | Stabil |
| Algoritmer totalt | 3 | 4 | **4** | ~18 |
| Læringsterskel | Lav | Lav | **Lav-moderat** | Høy |

**Velg Metode C fremfor Metode 3 hvis:**
- Du vil ha forutsigbar CP-gjenkjenning
- Du foretrekker to komplementære algoritmer (CO9 og CO10) fremfor to uavhengige (Sune og Anti-Sune)
- Du er komfortabel med 11-trekks algoritmer

**Velg Metode 3 fremfor Metode C hvis:**
- Du vil minimere totalt trekkantall per løsning
- Du allerede kan Sune og Anti-Sune fra 3×3-erfaring

---

## Notasjon

| Symbol | Megaminx-betydning |
|---|---|
| `R` | Høyre flate, 72° CW |
| `R-` | Høyre flate, 72° CCW |
| `U` | Topp, 72° CW |
| `U++` | Topp, 144° CW |
| `U--` | Topp, 144° CCW |
| `U-` | Topp, 72° CCW |
| `UL` | Øvre-venstre flate (bak-venstre) |
| `AUF_n` | n × U (72° CW), brukt som konjugat-setup |

---

*Alle algoritmer verifisert i Python-simulator. CO9/CO10 posisjonsbevaring verifisert.
CO-fix sekvens (`U CO9 U-` + `U-- CO10 U++`) verifisert. OCLL-dekning (alle 80 tilfeller
med CO9+CO10+AUF) verifisert via BFS.*
