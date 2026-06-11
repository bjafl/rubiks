# Design: Debug Labels i Megaminx Viewer

**Dato:** 2026-06-11  
**Status:** Godkjent

## Mål

Legg til et debug-overlay i 3D-vieweren som viser fasenavn, slotnummer og brikkenummer direkte på hver sticker. Tre uavhengige checkboxes lar brukeren toggle på/av hver type. Nyttig for å forstå modellstrukturen og debugge algoritmer live.

---

## Notasjon

| Begrep | Beskrivelse | Eksempel |
|---|---|---|
| **Fasenavn** | Navnene på de flatene som definerer sloten | `DFR/R`, `BR/R/U` |
| **Slotnr** | Numerisk slot-indeks med E/C-prefiks | `E24`, `C7` |
| **Brikkenr** | Nummeret på brikken som er i sloten nå | `E19`, `C14` |

---

## Label-innhold per sticker-type

| Sticker | Fasenavn | Slotnr | Brikkenr |
|---|---|---|---|
| Center | `U` (fasens navn, statisk) | — | — |
| Edge | `DFR/R` (to fasen, statisk) | `E24` (statisk) | `E19` (dynamisk) |
| Corner | `BR/R/U` (tre fasen, statisk) | `C7` (statisk) | `C14` (dynamisk) |

Bare **brikkenr** er dynamisk og oppdateres ved hvert state-change.

---

## Arkitektur

### Nye og endrede filer

**`viewer/js/labels.js`** (ny)  
Eksporterer tre funksjoner:
- `buildLabels(scene, geometry, stickerMetas)` — oppretter `CSS2DObject`-er og returnerer `{ updateLabelState, setLabelMode }`
- Internt: én `<div class="dbg-label">` per sticker med tre indre `<span>`-er (én per type)
- CSS2DObject attachces som child til sticker-meshet → følger animasjonsrotasjonen automatisk

**`viewer/js/megaminx.js`** (endres)  
`buildMegaminx` returnerer to nye felter:
- `stickerMetas`: array av `{ mesh, type, fi, k, slotIdx, faceNames }` for alle sticker-meshes
- `type` er `"center"`, `"edge"` eller `"corner"`
- `faceNames` er fasen-navn-strengen (f.eks. `"DFR/R"`)
- `slotIdx` er corner- eller edge-slot-indeksen

**`viewer/js/main.js`** (endres)  
- Oppretter `CSS2DRenderer` ved siden av `WebGLRenderer`, samme størrelse, `pointer-events: none`
- Kaller `buildLabels` etter `buildMegaminx`
- Kobler checkbox-onChange til `setLabelMode`
- Kaller `updateLabelState(msg)` i `onMessage`-handleren

**`viewer/index.html`** (endres)  
- Tre `<label><input type="checkbox"> …</label>` i controls-baren, til høyre for speed-slideren
- CSS for `.dbg-label` og de indre span-ene

### CSS2DRenderer

```
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
```

- Rendreres i render-loopen etter `webglRenderer.render(scene, camera)`
- Plasseres over canvas-elementet med `position: absolute; top: 0; left: 0; pointer-events: none`

---

## Label-styling

```css
.dbg-label { display: flex; flex-direction: column; align-items: center;
             pointer-events: none; }
.dbg-facename { font: bold 7px monospace; color: #fff;
                text-shadow: 0 0 3px #000, 0 0 3px #000; }
.dbg-slot     { font: 7px monospace; color: #7df; 
                text-shadow: 0 0 3px #000; }
.dbg-piece    { font: 7px monospace; color: #fd7;
                text-shadow: 0 0 3px #000; }
```

---

## Toggle UI

Tre checkboxes i `#controls-bar`, alle **unchecked som default**:

```html
<label class="dbg-toggle"><input type="checkbox" id="chk-facename"> Fase</label>
<label class="dbg-toggle"><input type="checkbox" id="chk-slot">     Slot</label>
<label class="dbg-toggle"><input type="checkbox" id="chk-piece">    Brikke</label>
```

---

## Dataflyt

```
geometry.json
  └─ buildMegaminx()  →  stickerMetas (mesh + slot/face-info)
       └─ buildLabels()
            ├─ CSS2DObject (fasenavn-span)   attached til mesh
            ├─ CSS2DObject (slot-span)       attached til mesh
            └─ CSS2DObject (brikke-span)     attached til mesh (dynamisk)

onMessage(state)
  └─ updateLabelState(state)  →  oppdaterer brikke-span for alle edge/corner-stickere

checkbox onChange
  └─ setLabelMode({faceNames, slots, pieces})  →  toggle visibility på hver span-type
```

---

## Avgrensninger

- Center-stickere viser kun fasenavn (ingen slot/brikkenr — center er alltid fast)
- Labels er alltid synlig over geometri (CSS2D ignorerer depth) — dette er akseptabelt for et debug-overlay
- Ingen hover-interaksjon — alle labels på/av per type
