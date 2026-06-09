# Megaminx LL – Metode 1 og 3

> Petrus-basert: EOLL hoppes over. Rekkefølge: **EP → CP → CO**

---

## Algoritmer

| Navn | Sekvens | Bevegelse |
|------|---------|-----------|
| **EP** | `FR++ U-- FR-- U- FR++ U-- FR--` | 3-sykel kanter (mot klokken) |
| **EP⁻¹** | `FR++ U++ FR-- U FR++ U++ FR--` | 3-sykel kanter (med klokken) |
| **Niklas** | `FR U- FL- U FR- U- FL U` | 3-sykel hjørner A→C→B |
| **Niklas⁻¹** | `U- FL- U FR U- FL U FR-` | 3-sykel hjørner A→B→C |
| **Sune** | `FR U FR- U FR U-- FR-` | CO: +1 til 3 hjørner |
| **Anti-Sune** | `FR- U- FR U- FR- U++ FR` | CO: +2 til 3 hjørner |

---

## EP – Kantpermutasjon

### Gjenkjenning

AUF og tell kanter som matcher senteret.

| Riktige kanter | Type | Løsning |
|---|---|---|
| 5 | Ferdig | – |
| 2 (naboer) | 3-sykel | EP eller EP⁻¹ (1 app) |
| 1 | 5-sykel | EP → bank til 2 nabo → EP (2 apps) |
| 0 | 5-sykel | EP → tell → EP (2 apps) |

### Bankingstrategi

> Mål: få 2 naboer riktige → garantert 3-sykel.

Prøv EP (eller EP⁻¹), tell riktige nabo-kanter, AUF → løs med én app.

---

## CP – Hjørnepermutasjon

### ⚠️ CO sist alltid

Niklas tvister de 3 syklerte hjørnene med +1 (72°-geometri). CO-steget absorberer dette. **Gjør aldri CO før CP.**

### Niklas fixed corners

```
Posisjon 1   FR-hjørne   ← fast
Posisjon 3   FL-hjørne   ← fast
```

De to hjørnene som Niklas *ikke* beveger er alltid i FL- og FR-sporet.

### Gjenkjenning

Tell topp-hjørner på riktig plass (uavhengig av orientering).

| Faste hjørner | Type | Løsning |
|---|---|---|
| 5 | Ferdig | – |
| 2 | 3-sykel | AUF de 2 riktige til pos 1+3 → Niklas (1 app) |
| 1 | Dobbel-transposisjon | Niklas uten AUF → gir 3-sykel → løs over (2 apps) |
| 0 | 5-sykel | Niklas → tell → gjenta. Maks 3 apps |

### Steg-for-steg worst-case

```
0 faste  →[Niklas]→  1 fast  →[AUF+Niklas]→  2 faste  →[AUF+Niklas]→  ferdig
```

---

## CO – Hjørneorientering

### Sune og Anti-Sune

```
Sune:       FR U FR- U FR U-- FR-    (+1 til 3 hjørner)
Anti-Sune:  FR- U- FR U- FR- U++ FR  (+2 til 3 hjørner)
```

> ⚠️ **Megaminx ≠ 3×3 for CO:** På 3×3 er Sune ren CO (beveger bare hjørneorienteringer). På Megaminx beveger Sune og Anti-Sune OGSÅ topp-hjørner og topp-kanter som bieffekt (72°-geometri). Etter CO er kanter og hjørneposisjoner forstyrret og trenger en ekstra EP/CP-sjekk.

De **to hjørnene Sune/Anti-Sune ikke påvirker** er alltid de samme per applikasjon — kall dem «det faste paret».

### Praktisk rekkefølge (anbefalt)

```
CO (Sune/Anti-Sune ×1-5 til alle orientert)
  → EP (fikse kanter)
  → CP (Niklas, gir +1 twist på 3 hjørner)
  → CO-fix (Anti-Sune for Niklas-twisten)
```

Etter CO-fix er vanligvis alt løst. I sjeldne tilfeller trengs en ekstra EP- eller CP-runde.

### Parkerings-trikset

> AUF for å plassere allerede-orienterte hjørner inn på det faste paret → én Sune/Anti-Sune fikser de 3 resterende.

NB: Sune beveger kanter som bieffekt. Bruk bankingsstrategien og forvent EP-sjekk etter CO.

### Metode 1 (Sune alene) — worst-case CO

| Tilstand | Sune-apps |
|---|---|
| 5 orienterte | 0 |
| 2 riktige | 1 (park + Sune) |
| Blanding | 2–5 |

### Metode 3 (+Anti-Sune) — halverer worst-case

Etter CP er eksakt 3 hjørner vridd med +1 (de Niklas syklet).

> AUF de 2 uvridade hjørnene inn på det faste paret til Anti-Sune → **ett Anti-Sune-kall** fikser alle 3.

| Tilstand | Metode 1 apps | Metode 3 apps |
|---|---|---|
| Alle +1 (3 stk) | 1–3 (Sune) | 1 (Anti-Sune direkte) |
| Blanding | 2–5 | 1–2 |

---

## Komplett flyt

```
[EP]   AUF → bank 2 nabo-kanter → EP/EP⁻¹
         ↓
[CP]   Tell faste hjørner → bank + Niklas/Niklas⁻¹
         ↓
[CO]   Parker orienterte → Sune / Anti-Sune (M3)
         ↓
       Ferdig
```

Forventet apps per løsning: **5–9** (inkl. EP-fix etter CO)

---

## Notasjon

| Symbol | Betydning |
|---|---|
| `U` / `U-` | Topp 72° med/mot klokken |
| `U++` / `U--` | Topp 144° med/mot klokken |
| `FR` / `FR-` | Høyre-fremre 72° med/mot klokken |
| `FL` / `FL-` | Venstre-fremre |
| `++` | Dobbel (144°), kan skrives som `2` i noen notasjoner |
