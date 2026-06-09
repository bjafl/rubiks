# Megaminx 3D Viewer — Design Spec

## Mål

Bygge et interaktivt 3D-læringsverktøy for Megaminx LL-algoritmer. Vieweren viser Megaminx i Three.js med animerte trekk, styres fra nettleseren (manuelt) og via MCP (AI-klient). Python-serveren er eneste kilde til sannhet om kubens tilstand.

---

## Arkitektur

Tre parter koblet via HTTP og WebSocket:

```
AI-klient (MCP)  ←→  Python-server  ←→  Nettleser (Three.js)
                     server.py           viewer/
                     viewer_state.py
```

**Python-server** (`mcp_server/server.py` — eksisterende, utvides):
- Serverer `viewer/` som statiske filer via HTTP (`GET /`)
- Eksponerer WebSocket-endepunkt (`ws://localhost:PORT/ws`)
- Eksponerer MCP-verktøy for AI-kontroll

**SessionState** (Python) er autoritativ — nettleseren renderer bare det serveren sender. Nettleseren sender aldri tilstandsmutasjoner, kun navigasjons-intent (step fwd/bck, speed).

---

## Fil- og komponentstruktur

```
mcp_server/
  server.py          ← legg til: HTTP static, WebSocket, MCP viewer-verktøy
  viewer_state.py    ← ny: SessionState, AnimationQueue, parse_sequence()

viewer/
  index.html         ← layout C: 3D venstre (dominerende) + høyrepanel
  js/
    main.js          ← app entry: WebSocket-tilkobling, dispatch til moduler
    scene.js         ← Three.js-oppsett, kamera, OrbitControls
    megaminx.js      ← dodekahedral geometri, ansiktsrotasjons-animasjon
    svg.js           ← top-down SVG-renderer (ren funksjon: state → SVG string)
    controls.js      ← avspillingskontroller (play/pause/step/hastighet/progresjon)
    library.js       ← algoritmebibliotek + fritekst-input
```

---

## UI-layout (C)

```
┌─────────────────────────────────┬────────────────────┐
│                                 │  [Top-down SVG]     │
│      Three.js 3D viewport       │─────────────────────│
│         (roterbar)              │  ALGORITMER         │
│                                 │  ▶ CO9              │
│                                 │  CO10               │
│─────────────────────────────────│  Sune / Anti-Sune   │
│  ⏮  ◀  ▶  ▶▶  ⏭   0.8×  4/11  │  Niklas / EP1/EP2   │
└─────────────────────────────────│─────────────────────│
                                  │  [fritekst-input]   │
                                  │  R U++ R-…     [▶]  │
                                  └────────────────────┘
```

- 3D viewport tar ~65% av bredden, er roterbar med OrbitControls
- Kontrollpanel sitter under 3D-viewporten (progress bar + navigasjonsknapper)
- Høyrepanel: top-down SVG øverst, algoritmebibliotek i midten, fritekstfelt nederst
- Begge inngangspunkter (bibliotek + fritekst) laster inn i samme viewer

---

## Animasjonsstil (C — kombinert)

- **Auto-play**: Spiller av hele sekvensen automatisk, ett trekk om gangen
- **Manuell steg**: Frem/tilbake per trekk (⏮ ◀ ▶ ⏭ knapper)
- **Hastighetskontroll**: 0.3× til 3× (slider)
- **Progresjonslinje**: Viser nåværende trekk / totalt antall trekk
- Hvert trekk animeres som en jevn 72°/144° rotasjon av den aktuelle flaten i Three.js

---

## WebSocket-protokoll

### Server → nettleser

```jsonc
// Tilstandsoppdatering (etter hvert trekk)
{ "type": "state",
  "corners": [[0,0],[1,0],...],   // 20 hjørner: [brikke-id, orientering]
  "edges":   [[0,0],[1,0],...],   // 30 kanter:  [brikke-id, orientering]
  "moveIndex":   4,
  "totalMoves":  11,
  "currentMove": "U-",
  "algName":     "CO9"            // null for fritekst-sekvenser
}

// Ny sekvens lastet inn
{ "type": "loaded",
  "algName": "CO9",               // null for fritekst
  "moves":   ["R","U++","R-",...]
}

// Tilbakestilt
{ "type": "reset" }
```

### Nettleser → server

```jsonc
{ "type": "step",  "dir": "fwd" }   // manuelt trekk frem
{ "type": "step",  "dir": "bck" }   // manuelt trekk tilbake
{ "type": "speed", "val": 1.0 }     // hastighetsjustering
```

Serveren svarer med en `state`-melding etter hver `step`.

---

## MCP-verktøy

Alle verktøy deles av én `SessionState`-instans og pusher WebSocket-events til nettleseren.

| Verktøy | Parametre | Effekt |
|---|---|---|
| `load_algorithm` | `name: str` | Laster navngitt algoritme fra `algorithms.py`, sender `loaded` |
| `animate_sequence` | `sequence: str` | Parser prosjekt-/WCA-notasjon, laster anonym sekvens |
| `step_forward` | — | Ett trekk frem, sender `state` |
| `step_backward` | — | Ett trekk tilbake, sender `state` |
| `goto_move` | `n: int` | Hopper til trekk n (rekjører fra start), sender `state` |
| `reset` | — | Tilbakestiller til løst tilstand, sender `reset` |
| `show_state` | — | Returnerer top-down SVG av nåværende tilstand som tekst |

---

## SessionState (Python)

```python
@dataclass
class SessionState:
    megaminx: Megaminx          # Simulator fra megaminx/model.py
    sequence: list[str]         # Nåværende sekvens (trekk-strenger)
    move_index: int             # Neste trekk som skal utføres (0 = start)
    alg_name: str | None        # Navn hvis lastet fra bibliotek, ellers None
    ws_clients: set             # Aktive WebSocket-tilkoblinger

    def state_snapshot(self) -> dict: ...
    def apply_move(self, move: str) -> None: ...
    def rewind_to(self, n: int) -> None: ...   # rekjører fra solved
```

`rewind_to(n)` lager en ny `Megaminx()`-instans og kjører `sequence[:n]` på nytt — enkel og korrekt, ingen delta-lagring nødvendig.

---

## Three.js geometri

- Dodekahedral geometri bygges ved oppstart fra `viewer/geometry.json` — genereres av Python (`mcp_server/gen_geometry.py`) og sjekkes inn i repo
- Hvert ansikt har 11 synlige brikker (1 center + 5 kanter + 5 hjørner)
- Ansiktsrotasjon: roterer en `THREE.Group` med alle 11 brikker 72°/144° rundt ansiktsnormalen via lineær interpolasjon i `requestAnimationFrame` (ingen ekstern animasjonsbibliotek)
- Farger: fast fargekart (U=gul, F=grønn, R=oransje, ...) — samme som prosjektets eksisterende visualiseringer

---

## Top-down SVG

Ren funksjon `stateToSvg(state)` i `svg.js`:
- U-flaten som regulær pentagon i midten
- 5 tilstøtende flater "brettet ut" rundt U som trapesformer
- Brikkefarger farges etter `state.corners` og `state.edges`
- Oppdateres synkront ved hver `state`-melding

---

## Avgrensninger

- Kun ett WebSocket-tilkobling støttes i MVP (serveren broadcaster til alle, men forutsetter én bruker)
- Ingen persistens av sekvenser mellom sesjoner
- Kun øverste lag (LL-fokus) er animert manuelt; fullstendig scramble via `animate_sequence`
- Mobilvisning er ikke prioritert (desktop-first)
