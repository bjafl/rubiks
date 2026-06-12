# Megaminx-modellen — indekser for hjørner og kanter

Oppslagstabeller for slot-indeksene i `megaminx/cube.py` (`CORNERS` og `EDGES`). Indeksen er posisjonen i `cp`/`co` og `ep`/`eo`-tuplene: `cp[i]` = brikken som står i hjørneposisjon `i`, osv.

## Ordningsprinsipp

- **Hjørner**: vertex-syklusen (de tre fasadene i konsistent rotasjonsrekkefølge rundt hjørnet) rotert slik at alfabetisk minste fasade står først, deretter sortert alfabetisk. Rekkefølgen i tuppelen er *ikke* vilkårlig — den definerer orienteringen.
- **Kanter**: paret sortert alfabetisk, listen sortert alfabetisk.
- **Orienteringsreferanse**: første fasade i tuppelen. `co[i]` = hvor brikkens referansemerke ligger i slotens syklus (0, 1 eller 2). `eo[i]` = 0 når brikkens referansemerke ligger på slotens første fasade, ellers 1.

Modell- og community-navn er nå identiske (navnene ble synkronisert 2026-06-11).

## Hjørner (cp/co, indeks 0–19)

| Idx | Modell | Community | Plassering |
|---|---|---|---|
| 0 | BL/BR/U | BL/BR/U | U-laget, bak |
| 1 | BL/B/BR | BL/B/BR | Mellom bandene, bak |
| 2 | BL/dBL/B | BL/dBL/B | Mellom bandene, bak-venstre |
| 3 | BL/L/dBL | BL/L/dBL | Mellom bandene, venstre |
| 4 | BL/U/L | BL/U/L | U-laget, bak-venstre |
| 5 | BR/B/dBR | BR/B/dBR | Mellom bandene, bak-høyre |
| 6 | BR/dBR/R | BR/dBR/R | Mellom bandene, høyre |
| 7 | BR/R/U | BR/R/U | U-laget, bak-høyre |
| 8 | D/B/dBL | D/B/dBL | D-laget, bak-venstre |
| 9 | D/dBL/dL | D/dBL/dL | D-laget, venstre |
| 10 | D/dBR/B | D/dBR/B | D-laget, bak-høyre |
| 11 | D/dL/dR | D/dL/dR | D-laget, foran |
| 12 | D/dR/dBR | D/dR/dBR | D-laget, høyre |
| 13 | dBL/L/dL | dBL/L/dL | Mellom bandene, venstre foran |
| 14 | dBR/dR/R | dBR/dR/R | Mellom bandene, høyre foran |
| 15 | dL/F/dR | dL/F/dR | Mellom bandene, rett foran |
| 16 | dL/L/F | dL/L/F | Mellom bandene, venstre foran |
| 17 | dR/F/R | dR/F/R | Mellom bandene, høyre foran |
| 18 | F/L/U | F/L/U | U-laget, venstre foran |
| 19 | F/U/R | F/U/R | U-laget, høyre foran |

**Gruppert etter lag:**

- U-laget (LL hvis U er sist): **0, 4, 7, 18, 19**
- Mellom bandene («ekvator», 10 stk): 1, 2, 3, 5, 6, 13, 14, 15, 16, 17
- D-laget: 8, 9, 10, 11, 12

## Kanter (ep/eo, indeks 0–29)

| Idx | Modell | Community | Plassering |
|---|---|---|---|
| 0 | BL/BR | BL/BR | Øvre band, bak |
| 1 | BL/B | BL/B | Bandskille, bak-venstre |
| 2 | BL/dBL | BL/dBL | Bandskille, bak-venstre |
| 3 | BL/L | BL/L | Øvre band, venstre bak |
| 4 | BL/U | BL/U | U-laget, bak-venstre |
| 5 | BR/B | BR/B | Bandskille, bak-høyre |
| 6 | BR/dBR | BR/dBR | Bandskille, bak-høyre |
| 7 | BR/R | BR/R | Øvre band, høyre bak |
| 8 | BR/U | BR/U | U-laget, bak-høyre |
| 9 | D/B | D/B | D-laget, bak |
| 10 | D/dBL | D/dBL | D-laget, bak-venstre |
| 11 | D/dBR | D/dBR | D-laget, bak-høyre |
| 12 | D/dL | D/dL | D-laget, venstre foran |
| 13 | D/dR | D/dR | D-laget, høyre foran |
| 14 | B/dBL | B/dBL | Nedre band, bak-venstre |
| 15 | B/dBR | B/dBR | Nedre band, bak-høyre |
| 16 | dBL/dL | dBL/dL | Nedre band, venstre |
| 17 | dBL/L | dBL/L | Bandskille, venstre |
| 18 | dBR/dR | dBR/dR | Nedre band, høyre |
| 19 | dBR/R | dBR/R | Bandskille, høyre |
| 20 | dL/dR | dL/dR | Nedre band, foran |
| 21 | dL/F | dL/F | Bandskille, venstre foran |
| 22 | dL/L | dL/L | Bandskille, venstre foran |
| 23 | dR/F | dR/F | Bandskille, høyre foran |
| 24 | dR/R | dR/R | Bandskille, høyre foran |
| 25 | F/L | F/L | Øvre band, venstre foran |
| 26 | F/R | F/R | Øvre band, høyre foran |
| 27 | F/U | F/U | U-laget, foran |
| 28 | L/U | L/U | U-laget, venstre |
| 29 | R/U | R/U | U-laget, høyre |

**Gruppert etter lag:**

- U-laget: **4, 8, 27, 28, 29**
- Øvre band (mellom øvre-band-fasader): 0, 3, 7, 25, 26
- Bandskille (øvre band ↔ nedre band): 1, 2, 5, 6, 17, 19, 21, 22, 23, 24
- Nedre band (mellom nedre-band-fasader): 14, 15, 16, 18, 20
- D-laget: 9, 10, 11, 12, 13

## Praktiske oppslag

For last layer-arbeid (U som siste lag):

```python
LL_CORNERS = (0, 4, 7, 18, 19)
LL_EDGES   = (4, 8, 27, 28, 29)

def ll_co(state):           # vridninger i U-laget
    return tuple(state.co[i] for i in LL_CORNERS)

def ll_solved_below(state): # alt under LL på plass?
    return all(state.cp[i] == i and state.co[i] == 0
               for i in range(20) if i not in LL_CORNERS) and \
           all(state.ep[i] == i and state.eo[i] == 0
               for i in range(30) if i not in LL_EDGES)
```

Merk om co i U-laget: orienteringsreferansen er alfabetisk første fasade i tuppelen, som for LL-hjørnene er BL (idx 0, 4), BR (idx 7) og F (idx 18, 19) — **ikke U**. co = 0 betyr altså ikke automatisk «U-merket opp». Skal co-verdiene matche manuell CO-telling (U-merket opp = 0), må referansen per LL-slot byttes til U-fasaden, dvs. tuplene roteres til U først og move-tabellene regenereres. Inntil da: bruk `corner_at()` og sjekk hvor U-merket faktisk peker, eller behandle co-verdiene som internt konsistente, men konvensjonsavhengige.

Funksjonene `corner_at(*faces)` og `edge_at(*faces)` i `megaminx.py` slår opp på fasadenavn uavhengig av rekkefølge, så indeksene trengs primært for hurtige predikater, koordinater og tabellbygging.
