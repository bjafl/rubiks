# Metode C — CO9/CO10 + EP + Niklas

> Rekkefølge: **CO → EP → CP → CO-fix → EP-fix**
> Nøkkelegenskap: CO9/CO10 bevarer hjørneposisjoner → CP-gjenkjenning er stabil.

---

## Referansediagram

```
            [4]          Slot   Flater
    e4  ╱       ╲  e3    0      U + F + R
      [2]         [3]    1      U + F + L
    e1  ╲       ╱  e2    2      U + R + UR
            [0]─[1]      3      U + L + UL
                e0        4      U + UL + UR

Kanter:  e0=U|F   e1=U|R   e2=U|L   e3=U|UL   e4=U|UR
Sett ovenfra — R-flaten er langs venstre kant (mellom slot 0 og 2)
```

```
Symbol  Betyr
○       uendret
+1      vridning CW 120°
+2      vridning CCW 120°
→↑↙     retning brikken beveger seg
```

---

## CO9   `R U++ R- U- R U R- U- R U- R-`

```
        +1[4]
←e4  ╱       ╲ ↙e3      Hjørner: pos uendret
 +2[2]       +2[3]       Vridning: [+1, ○, +2, +2, +1]
↑e1  ╲       ╱ ○e2       Slot 1 frosset (anker)
      +1[0]──○[1]
              ○e0        Kanter: e1→e3→e4→e1  (e0, e2 urørt)
```

---

## CO10   `R U R- U R U- R- U R U-- R-`

```
        +2[4]
→e4  ╱       ╲ ↑e3       Hjørner: pos uendret
 +1[2]       +1[3]        Vridning: [+2, ○, +1, +1, +2]
↑e1  ╲       ╱ ○e2        Slot 1 frosset (anker)
      +2[0]──○[1]
              ○e0         Kanter: e1→e4→e3→e1  (e0, e2 urørt)
```

> CO9 og CO10 er hverandres inverse. Samme fryspunkt (slot 1), samme frosne kanter (e0, e2), kantbevegelse i motsatte retninger.

---

## EP1   `R++ U-- R-- U- R++ U-- R--`

```
        [4]←────╮
     ╱           │         Hjørner: 5-sykkel  0→2→1→3→4→0
○e4[2]   [3]    │                  (ingen vridning — bieffekt)
    ↑  ↙    ↖  │
   [0]→→[1]     │         Kanter: e1→e3→e2→e1  (e0, e4 urørt)
    ╰───────────╯
```

```
         [4]
 ○e4  ╱       ╲ ↙e3
     [2]         [3]
 ↑e1  ╲       ╱ ↓e2
         [0]─[1]
             ○e0
```

---

## EP2   `R++ U++ R-- U R++ U++ R--`

Invers av EP1.

```
Hjørner: 5-sykkel  0→4→3→1→2→0  (ingen vridning)
Kanter:  e1→e2→e3→e1  (e0, e4 urørt)
```

```
         [4]
 ○e4  ╱       ╲ →e3
     [2]         [3]
 ↓e1  ╲       ╱ ↑e2
         [0]─[1]
             ○e0
```

---

## Niklas   `R- U L U- R U L- U-`

```
            ○[4]

        [2]   ○[3]      Hjørner: 0→1→2→0 (fremre tre sykler)
       ↗   ↘            Slot 3 og 4 frosset (BL-siden)
        [0]→[1]         Kanter: INGEN endring ← nøkkelegenskap

         [4]
 ○e4  ╱       ╲ ○e3
     [2]         [3]
 ○e1  ╲       ╱ ○e2
         [0]─[1]
             ○e0
```

---

## Niklas⁻¹   `U L U- R- U L- U- R`

```
Hjørner: 0→2→1→0 (invers sykkel)
Slot 3 og 4 frosset

Kanter: INGEN endring
```

---

## Sammenligning

| Algoritme | Hjørner | Vridning | Kantssykkel | Urørt |
|-----------|---------|----------|-------------|-------|
| CO9  | pos uendret | +1,○,+2,+2,+1 | e1→e3→e4→e1 | e0, e2 |
| CO10 | pos uendret | +2,○,+1,+1,+2 | e1→e4→e3→e1 | e0, e2 |
| EP1  | 5-sykkel    | ingen         | e1→e3→e2→e1 | e0, e4 |
| EP2  | 5-sykkel⁻¹  | ingen         | e1→e2→e3→e1 | e0, e4 |
| Niklas   | 0→1→2→0 | +0,+2,+1 | **ingen**   | alle  |
| Niklas⁻¹ | 0→2→1→0 | +2,+1,+0 | **ingen**   | alle  |

---

## CO-gjenkjenning

Bruk **konjugat-form**: `AUF_n  CO9/CO10  AUF_(5-n)`
AUF roterer topplaget n hakk CW før og (5-n) hakk etter — effekten forskyves n plasser uten å endre hjørneposisjoner.

| n | AUF foran | AUF bak |
|---|-----------|---------|
| 0 | –         | –       |
| 1 | U         | U-      |
| 2 | U++       | U--     |
| 3 | U--       | U++     |
| 4 | U-        | U       |

**1-kall (10 av 80 tilfeller):** Finn hjørne med rett orientering (ori=0) — det er ankeret.
1. AUF ankeret til slot 1 (én hakk CW fra R, sett ovenfra)
2. Naboene (slot 0 og 4) trenger **+1** → bruk `CO10` / trenger **+2** → bruk `CO9`
3. Utfør konjugat: `AUF_n  alg  AUF_(5-n)`

**2–3 kall (70 av 80 tilfeller):** Alle hjørner feil orientert → ingen anker.
→ Kjør CO9 (n=0), se om anker dukker opp → 1 kall til.

```
1 kall:  10 tilfeller (12.5 %)
2 kall:  40 tilfeller (50.0 %)
3 kall:  30 tilfeller (37.5 %)
Snitt:   2.25 kall
```

---

## CO-fix etter standard Niklas

Etter Niklas (uten AUF) er tilstanden: `[+1, ○, +1, ○, +1]`

```
U  CO9  U-      → fjerner twist fra 3 slots
U-- CO10 U++    → fikser gjenværende
```

Deretter: **EP-fix** (5 kanter forstyrret — 1 EP1/EP2-kall).

---

## Komplett flyt

```
[CO]     Finn anker → konjugat CO9/CO10 × 1–3
            ↓
[EP]     Bank 2 nabo-kanter → EP1/EP2 × 1–2
            ↓
[CP]     Niklas × 1–3  (CP stabil: CO røret ikke posisjoner)
            ↓
[CO-fix] U CO9 U-  →  U-- CO10 U++  (fast sekvens for std Niklas)
            ↓
[EP-fix] EP1/EP2 × 1
            ↓
         Ferdig  (~7–12 alg-kall totalt)
```

---

## Notasjon

| Symbol | Megaminx |
|--------|----------|
| `R` / `R-` | Høyre flate, 72° CW/CCW |
| `R++` / `R--` | Høyre flate, 144° CW/CCW |
| `L` / `L-` | Venstre flate, 72° CW/CCW |
| `U` / `U-` | Topp, 72° CW/CCW |
| `U++` / `U--` | Topp, 144° CW/CCW |
| `AUF_n` | n × U — konjugat-setup |

*Alle algoritmer verifisert i Python-simulator.*
