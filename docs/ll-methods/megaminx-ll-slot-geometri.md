# Megaminx LL – Slot-geometri (topplag)

## Diagram sett ovenfra

```
         Sett ovenfra (du er nedenfor)

               [4]        z=+1.618
              /    \       ← bort fra deg
            [2]    [3]    z=+1.0
              \    /
             [0]──[1]     z=0
                           ← mot deg (F-flaten)

         x–           x+
     (din høyre)  (din venstre)
```

Du holder megaminxen med F-flaten mot deg. Topplagets pentagon har:
- En **fremkant** (mot deg): mellom slot 0 og slot 1
- En **bakre spiss** (bort fra deg): slot 4

## Slottabell

| Slot | Posisjon (sett ovenfra) | Fra solvers perspektiv | Flater |
|------|------------------------|------------------------|--------|
| 0 | fremre-høyre | din fremre høyre hånd | U + F + R |
| 1 | fremre-venstre | din fremre venstre | U + F + L |
| 2 | bakre-høyre | din bakre høyre | U + R + UR |
| 3 | bakre-venstre | din bakre venstre | U + L + UL |
| 4 | bakre spiss | peker bort fra deg | U + UL + UR |

## CW-rekkefølge sett ovenfra

Klokkevis fra øverst høyre: **3 → 4 → 2 → 0 → 1 → (tilbake til 3)**

## Koordinatsystem (kodemodellen)

| Akse | Retning |
|------|---------|
| y+ | opp |
| z+ | bort fra solver (bak) |
| z– | mot solver (foran) |
| x– | solvers høyre (venstre i diagram) |
| x+ | solvers venstre (høyre i diagram) |

> x-aksen er speilet: negativ x = din høyre. Dette er standard "top-down view mirror" —
> når du ser ned ovenfra bytter venstre og høyre i forhold til front-perspektiv.

---

## Algoritmeeffekter på topplag

### Referansediagram

```
            [4]
    e4  ╱       ╲  e3
      [2]         [3]
    e1  ╲       ╱  e2
            [0]─[1]
                e0

Kanter: e0=U|F  e1=U|R  e2=U|L  e3=U|UL  e4=U|UR
Hjørner: se slottabell ovenfor
```

Symbolforklaring:

| Symbol | Betyr |
|--------|-------|
| `○` | uendret |
| `+1` | vridning +1 (CW, 120°) |
| `+2` | vridning +2 (CCW, 120°) |
| `→` / `↑` / `↙` | retning brikken beveger seg |

---

### CO9   `R U++ R- U- R U R- U- R U- R-`

**Hjørner** — ingen posisjonsflytt, kun vridning:

```
           +1[4]
     e4  ╱       ╲  e3
      +2[2]       +2[3]
     e1  ╲       ╱  e2
        +1[0]───○[1]
                e0

Vridninger: [ +1, ○, +2, +2, +1 ]
Slot 1 er frosset (anker).
```

**Kanter** — 3-sykkel (e1 → e3 → e4 → e1):

```
             [4]
    ←e4   ╱       ╲  ↙e3
        [2]         [3]
    ↑e1   ╲       ╱  ○e2
             [0]─[1]
                 ○e0

Sykkel: e1 ──→ e3 ──→ e4 ──→ e1
```

---

### CO10   `R U R- U R U- R- U R U-- R-`

**Hjørner** — kun vridning (invers av CO9):

```
           +2[4]
     e4  ╱       ╲  e3
      +1[2]       +1[3]
     e1  ╲       ╱  e2
        +2[0]───○[1]
                e0

Vridninger: [ +2, ○, +1, +1, +2 ]
Slot 1 frosset.
```

**Kanter** — 3-sykkel invers (e1 → e4 → e3 → e1):

```
             [4]
    →e4   ╱       ╲  ↑e3
        [2]         [3]
    ↑e1   ╲       ╱  ○e2
             [0]─[1]
                 ○e0

Sykkel: e1 ──→ e4 ──→ e3 ──→ e1   (omvendt av CO9)
```

> CO9 og CO10 er hverandres inverse: same hjørnefryspunkt (slot 1),
> same to kanter frosset (e0, e2), men kantbevegelse i motsatte retninger.

---

### EP1   `R++ U-- R-- U- R++ U-- R--`

**Hjørner** — 5-sykkel uten vridning (bieffekt):

```
Sykkel: 0 → 2 → 1 → 3 → 4 → 0  (ingen vridning)

           [4]←──────╮
         ╱            │
       [2]     [3]    │
        ↑    ↙    ↖   │
       [0]───→[1]     │
         ╰─────────────╯

(stjernemønster — alle 5 hjørner roterer)
```

**Kanter** — 3-sykkel (e1 → e3 → e2 → e1):

```
             [4]
    ○e4   ╱       ╲  ↙e3
        [2]         [3]
    ↑e1   ╲       ╱  ↓e2
             [0]─[1]
                 ○e0

Sykkel: e1 ──→ e3 ──→ e2 ──→ e1
```

---

### EP2   `R++ U++ R-- U R++ U++ R--`

Invers av EP1.

**Hjørner** — 5-sykkel invers uten vridning:
```
Sykkel: 0 → 4 → 3 → 1 → 2 → 0
```

**Kanter** — 3-sykkel invers (e1 → e2 → e3 → e1):

```
             [4]
    ○e4   ╱       ╲  →e3
        [2]         [3]
    ↓e1   ╲       ╱  ↑e2
             [0]─[1]
                 ○e0

Sykkel: e1 ──→ e2 ──→ e3 ──→ e1
```

---

### Sune   `R U R- U R U-- R-`

**Hjørner** — dobbel bytte med vridning:

```
         +1[4]
         ↕          ← [0]↔[4]: bytte med +1 twist
      +0[2]↔+1[3]   ← [2]↔[3]: bytte, slot2 beholder ori
         ↕
      +1[0]───○[1]

Bytte: (0 ↔ 4)  og  (2 ↔ 3)
Vridninger etter bytte: slot0=+1, slot2=+0, slot3=+1, slot4=+1
Slot 1 frosset.
```

**Kanter** — identisk 3-sykkel som CO9 (e1 → e3 → e4 → e1):

```
             [4]
    ←e4   ╱       ╲  ↙e3
        [2]         [3]
    ↑e1   ╲       ╱  ○e2
             [0]─[1]
                 ○e0

Sykkel: e1 ──→ e3 ──→ e4 ──→ e1   (same som CO9)
```

---

### Niklas   `R- U L U- R U L- U-`

**Hjørner** — ren 3-sykkel av de tre fremre slotene:

```
            ○[4]
             
        [2]   ○[3]
       ↗   ↘
        [0]→[1]

Sykkel: 0 → 1 → 2 → 0
Slot 3 og 4 frosset (BL-siden).
Vridning per steg: 0→1: +0, 1→2: +2, 2→0: +1
```

**Kanter** — ingen endring:

```
             [4]
    ○e4   ╱       ╲  ○e3
        [2]         [3]
    ○e1   ╲       ╱  ○e2
             [0]─[1]
                 ○e0

Alle kanter uendret. ← nøkkelegenskap
```

---

### Niklas⁻¹   `U L U- R- U L- U- R`

**Hjørner** — invers sykkel (0 → 2 → 1 → 0):

```
Sykkel: 0 → 2 → 1 → 0
Slot 3 og 4 frosset.
Vridning per steg: 0→2: +2, 2→1: +1, 1→0: +0
```

**Kanter** — ingen endring (identisk med Niklas).

---

### Sammenligning

| Algoritme | Hjørner påvirket | Vridning | Kanter sykkel | Kanter upåvirket |
|-----------|-----------------|----------|---------------|-----------------|
| CO9 | 0, 2, 3, 4 (pos uendret) | +1, +2, +2, +1 | e1→e3→e4→e1 | e0, e2 |
| CO10 | 0, 2, 3, 4 (pos uendret) | +2, +1, +1, +2 | e1→e4→e3→e1 | e0, e2 |
| Sune | 0, 2, 3, 4 (dobbel bytte) | +1, 0, +1, +1 | e1→e3→e4→e1 | e0, e2 |
| Niklas | 0, 1, 2 (3-sykkel) | +0, +2, +1 | **ingen** | alle |
| Niklas⁻¹ | 0, 2, 1 (3-sykkel) | +2, +1, +0 | **ingen** | alle |
| EP1 | alle 5 (5-sykkel) | ingen | e1→e3→e2→e1 | e0, e4 |
| EP2 | alle 5 (5-sykkel) | ingen | e1→e2→e3→e1 | e0, e4 |

> **Viktigste observasjoner:**
> - Niklas er eneste algoritme som ikke rører kanter — ren CP-operasjon
> - CO9 og CO10 rører aldri hjørneposisjoner — stabil CP gjennom CO-trinnet
> - Sune og CO9 har identisk kanteffekt (e1→e3→e4→e1)
> - EP1/EP2 beveger alle 5 hjørner som bieffekt — CP-sporing nødvendig
> - e0 (fremkanten, U|F) og e2 (U|L) er aldri berørt av CO9/CO10/Sune

---

## Relevans for CO-gjenkjenning (Metode C)

- **R-flaten** ligger langs venstre kant i diagrammet (mellom slot 0 og slot 2)
- **Slot 0** er R-hjørnet (fremre, din høyre)
- **Slot 1** er ett hakk CW fra slot 0 sett ovenfra → frozen av CO9 og CO10
- **Slot 4** (bakre spiss) er IKKE slot 1 — slot 1 er en fremkant-slot

Se `megaminx-ll-metode-c.md` for CO9/CO10-bruk med AUF-konjugat.
