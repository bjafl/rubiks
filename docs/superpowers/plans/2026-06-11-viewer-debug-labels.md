# Viewer Debug Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a debug overlay to the Megaminx 3D viewer that shows face names, slot numbers, and piece numbers as toggleable labels on each sticker.

**Architecture:** CSS2DRenderer (Three.js addon) renders HTML `<div>` elements at sticker center positions in 3D space. Labels are static scene objects (not parented to meshes), so they stay at the canonical sticker positions regardless of animation state. `buildMegaminx` is extended to compute sticker center positions and slot metadata; a new `labels.js` module consumes that metadata and owns all label lifecycle.

**Tech Stack:** Three.js `CSS2DRenderer` / `CSS2DObject` (addons), vanilla JS, Python HTTP+WS server (unchanged).

---

## File Map

| File | Change |
|---|---|
| `viewer/js/scene.js` | Add `CSS2DRenderer` to render loop; return it |
| `viewer/js/megaminx.js` | Compute sticker centers + metadata; export `stickerMetas` |
| `viewer/js/labels.js` | **New.** `buildLabels(scene, geometry, stickerMetas)` → `{ updateLabelState, setLabelMode }` |
| `viewer/js/main.js` | Import `buildLabels`; call `updateLabelState` on every state update; wire checkboxes |
| `viewer/index.html` | Add 3 checkboxes + CSS for `.dbg-label`, `.dbg-facename`, `.dbg-slot`, `.dbg-piece`, `.dbg-toggle` |

---

## Task 1 — `scene.js`: add CSS2DRenderer to the render loop

**Files:**
- Modify: `viewer/js/scene.js`

Background: `createScene` owns the `requestAnimationFrame` loop. CSS2DRenderer must call `labelRenderer.render(scene, camera)` every frame. We create it here so the loop is in one place, and return it so `main.js` can attach labels to the same scene.

- [ ] **Step 1: Replace `scene.js` with the version below**

`viewer/js/scene.js`:
```javascript
import * as THREE from 'three';
import { OrbitControls }  from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer }  from 'three/addons/renderers/CSS2DRenderer.js';

export function createScene(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d1117);

  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(0, 5, 3);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);

  const labelRenderer = new CSS2DRenderer();
  labelRenderer.setSize(container.clientWidth, container.clientHeight);
  labelRenderer.domElement.style.cssText =
    'position:absolute;top:0;left:0;pointer-events:none;overflow:hidden;';
  container.appendChild(labelRenderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8);
  dir.position.set(5, 10, 7);
  scene.add(dir);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  (function loop() {
    requestAnimationFrame(loop);
    controls.update();
    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);
  })();

  window.addEventListener('resize', () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
    labelRenderer.setSize(container.clientWidth, container.clientHeight);
  });

  return { scene, camera, renderer, labelRenderer, controls };
}
```

- [ ] **Step 2: Start the viewer server and open the browser — verify no console errors**

```bash
cd /home/bjafl/source/rubiks
python -m mcp_server.viewer_server
# Open http://localhost:8080 in a browser
# Expected: cube renders normally, no JS console errors
```

- [ ] **Step 3: Commit**

```bash
git add viewer/js/scene.js
git commit -m "feat(viewer): add CSS2DRenderer to scene render loop"
```

---

## Task 2 — `megaminx.js`: compute and export `stickerMetas`

**Files:**
- Modify: `viewer/js/megaminx.js`

`stickerMetas` is an array of objects, one per sticker (132 total: 12 centers + 60 edges + 60 corners), in face-major order (all stickers of face 0, then face 1, …). Each entry:

```
{ mesh, type, fi, slotIdx, faceNames, center }
  type:      'center' | 'edge' | 'corner'
  fi:        face index 0–11
  slotIdx:   null (center) | edge slot 0–29 | corner slot 0–19
  faceNames: 'U' | 'DFR/R' | 'BR/R/U'  (face names of the slot, joined with '/')
  center:    THREE.Vector3 — world-space center of the sticker (for label placement)
```

The sticker center is the average of the four raw (pre-`_shrink`) vertices plus the normal lift, which equals the world-space center because `_shrink` preserves the centroid.

- [ ] **Step 1: Replace `megaminx.js` with the version below**

`viewer/js/megaminx.js`:
```javascript
import * as THREE from 'three';

const STICKER_LIFT = 0.006;
const INNER_S = 0.42;

export function buildMegaminx(geometry) {
  const group = new THREE.Group();
  const faceStickerMeshes = [];
  const stickerMetas      = [];

  const cornerMeshBySlot = Array.from({ length: 20 }, () => []);
  const edgeMeshBySlot   = Array.from({ length: 30 }, () => []);

  for (let fi = 0; fi < 12; fi++) {
    const rawVerts = geometry.faceVertices[fi];
    const centerV  = new THREE.Vector3(...geometry.faceCenters[fi]);
    const normal   = centerV.clone().normalize();
    const verts    = rawVerts.map(v => new THREE.Vector3(...v));
    const cc = geometry.faceCornerCycles[fi];
    const ec = geometry.faceEdgeCycles[fi];

    // Black face backing
    group.add(_buildFan(verts.map(v => centerV.clone().lerp(v, 0.97)), normal, 0x111111, 0));

    const innerV = verts.map(v => centerV.clone().lerp(v, INNER_S));

    // Center sticker — fixed, never animates
    const cMesh = _buildFan(_shrink(innerV), normal, geometry.faceColors[geometry.faceNames[fi]], STICKER_LIFT);
    _storeOrig(cMesh);
    group.add(cMesh);
    stickerMetas.push({
      mesh:      cMesh,
      type:      'center',
      fi,
      slotIdx:   null,
      faceNames: geometry.faceNames[fi],
      center:    centerV.clone().addScaledVector(normal, STICKER_LIFT),
    });

    const eMeshes  = [];
    const coMeshes = [];

    for (let k = 0; k < 5; k++) {
      const k1 = (k + 1) % 5;
      const km = (k - 1 + 5) % 5;

      // Edge sticker
      const e1 = verts[k].clone().lerp(verts[k1], 1/3);
      const e2 = verts[k].clone().lerp(verts[k1], 2/3);
      const eM = _buildQuad(_shrink([e1, e2, innerV[k1], innerV[k]]), normal, 0x888888, STICKER_LIFT);
      _storeOrig(eM);
      group.add(eM);
      eMeshes.push(eM);
      edgeMeshBySlot[ec[k]].push(eM);
      stickerMetas.push({
        mesh:      eM,
        type:      'edge',
        fi,
        slotIdx:   ec[k],
        faceNames: geometry.edgeFaces[ec[k]].map(i => geometry.faceNames[i]).join('/'),
        center:    e1.clone().add(e2).add(innerV[k1]).add(innerV[k])
                     .multiplyScalar(0.25)
                     .addScaledVector(normal, STICKER_LIFT),
      });

      // Corner sticker
      const cPrev = verts[km].clone().lerp(verts[k], 2/3);
      const cNext = verts[k].clone().lerp(verts[k1], 1/3);
      const coM = _buildFan(_shrink([cPrev, verts[k], cNext, innerV[k]]), normal, 0x888888, STICKER_LIFT);
      _storeOrig(coM);
      group.add(coM);
      coMeshes.push(coM);
      cornerMeshBySlot[cc[k]].push(coM);
      stickerMetas.push({
        mesh:      coM,
        type:      'corner',
        fi,
        slotIdx:   cc[k],
        faceNames: geometry.cornerFaces[cc[k]].map(i => geometry.faceNames[i]).join('/'),
        center:    cPrev.clone().add(verts[k]).add(cNext).add(innerV[k])
                     .multiplyScalar(0.25)
                     .addScaledVector(normal, STICKER_LIFT),
      });
    }

    faceStickerMeshes.push({ center: cMesh, edges: eMeshes, corners: coMeshes });
  }

  function getMeshesForFace(fi) {
    const cc = geometry.faceCornerCycles[fi];
    const ec = geometry.faceEdgeCycles[fi];
    const meshes = [];
    for (const ci of cc) meshes.push(...cornerMeshBySlot[ci]);
    for (const ei of ec) meshes.push(...edgeMeshBySlot[ei]);
    return meshes;
  }

  function updateColors(state) {
    const { corners, edges } = state;
    for (let fi = 0; fi < 12; fi++) {
      const { edges: eMeshes, corners: coMeshes } = faceStickerMeshes[fi];
      const cc = geometry.faceCornerCycles[fi];
      const ec = geometry.faceEdgeCycles[fi];

      for (let k = 0; k < 5; k++) {
        // Edge sticker
        const eslot  = ec[k];
        const epiece = edges[eslot][0];
        const eori   = edges[eslot][1];
        const eFaces = geometry.edgeFaces[eslot];
        const ki_e   = eFaces.indexOf(fi);
        const eColor = geometry.faceColors[geometry.faceNames[geometry.edgeFaces[epiece][(ki_e + eori) % 2]]];
        eMeshes[k].material.color.set(eColor);

        // Corner sticker
        const cslot  = cc[k];
        const cpiece = corners[cslot][0];
        const cori   = corners[cslot][1];
        const cFaces = geometry.cornerFaces[cslot];
        const ki_c   = cFaces.indexOf(fi);
        const cColor = geometry.faceColors[geometry.faceNames[geometry.cornerFaces[cpiece][(ki_c - cori + 3) % 3]]];
        coMeshes[k].material.color.set(cColor);
      }
    }
  }

  return { group, updateColors, getMeshesForFace, stickerMetas };
}

function _storeOrig(mesh) {
  mesh.userData.origPos  = mesh.position.clone();
  mesh.userData.origQuat = mesh.quaternion.clone();
}

function _shrink(verts, factor = 0.88) {
  const cx = verts.reduce((s, v) => s + v.x, 0) / verts.length;
  const cy = verts.reduce((s, v) => s + v.y, 0) / verts.length;
  const cz = verts.reduce((s, v) => s + v.z, 0) / verts.length;
  const c = new THREE.Vector3(cx, cy, cz);
  return verts.map(v => c.clone().lerp(v, factor));
}

function _buildFan(verts, normal, color, lift) {
  const pos = [];
  for (let i = 1; i < verts.length - 1; i++) {
    pos.push(...verts[0].toArray(), ...verts[i + 1].toArray(), ...verts[i].toArray());
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  const mat = new THREE.MeshLambertMaterial({ color, side: THREE.FrontSide });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.addScaledVector(normal, lift);
  return mesh;
}

function _buildQuad(v4, normal, color, lift) {
  const pos = [
    ...v4[0].toArray(), ...v4[2].toArray(), ...v4[1].toArray(),
    ...v4[0].toArray(), ...v4[3].toArray(), ...v4[2].toArray(),
  ];
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.computeVertexNormals();
  const mat = new THREE.MeshLambertMaterial({ color });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.addScaledVector(normal, lift);
  return mesh;
}
```

- [ ] **Step 2: Verify in the browser — cube renders correctly, no console errors**

```bash
# Server already running from Task 1. Refresh http://localhost:8080.
# Expected: cube renders and colors update normally when you step through an algorithm.
```

- [ ] **Step 3: Spot-check stickerMetas count in the browser console**

Open the browser console and run (after making `stickerMetas` temporarily accessible, or just trust the count):

Expected: 12 center + 60 edge + 60 corner = 132 entries total. You can verify by temporarily adding `console.log(stickerMetas.length)` after `buildMegaminx` in `main.js` — should log `132`.

- [ ] **Step 4: Commit**

```bash
git add viewer/js/megaminx.js
git commit -m "feat(viewer): export stickerMetas with center positions and slot metadata"
```

---

## Task 3 — Create `labels.js`

**Files:**
- Create: `viewer/js/labels.js`

This module owns all label DOM elements and CSS2DObjects. It does not import Three.js Group/Mesh — only `CSS2DObject`. Each sticker gets one `<div class="dbg-label">` with up to three child `<span>`s. The CSS2DObject is positioned at `meta.center` and added directly to the scene (not parented to a mesh). Labels do not follow animation; they update their piece-number content after each state change.

- [ ] **Step 1: Create `viewer/js/labels.js`**

```javascript
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

/**
 * Build debug label overlay for all stickers.
 *
 * @param {THREE.Scene}  scene
 * @param {object}       geometry   — parsed geometry.json
 * @param {Array}        stickerMetas — from buildMegaminx()
 * @returns {{ updateLabelState, setLabelMode }}
 */
export function buildLabels(scene, geometry, stickerMetas) {
  const faceSpans  = [];  // one per sticker (all types)
  const slotSpans  = [];  // one per edge/corner sticker
  const pieceItems = [];  // { span, type, slotIdx } — one per edge/corner sticker

  for (const meta of stickerMetas) {
    const div = document.createElement('div');
    div.className = 'dbg-label';

    // Fasenavn span — present for all sticker types
    const fSpan = document.createElement('span');
    fSpan.className = 'dbg-facename';
    fSpan.textContent = meta.faceNames;
    fSpan.style.display = 'none';
    div.appendChild(fSpan);
    faceSpans.push(fSpan);

    if (meta.type !== 'center') {
      const prefix = meta.type === 'edge' ? 'E' : 'C';

      // Slot span — static label
      const sSpan = document.createElement('span');
      sSpan.className = 'dbg-slot';
      sSpan.textContent = prefix + meta.slotIdx;
      sSpan.style.display = 'none';
      div.appendChild(sSpan);
      slotSpans.push(sSpan);

      // Piece span — updated on every state change
      const pSpan = document.createElement('span');
      pSpan.className = 'dbg-piece';
      pSpan.style.display = 'none';
      div.appendChild(pSpan);
      pieceItems.push({ span: pSpan, type: meta.type, slotIdx: meta.slotIdx });
    }

    const obj = new CSS2DObject(div);
    obj.position.copy(meta.center);
    scene.add(obj);
  }

  /** Update piece-number labels from a state snapshot (msg.corners / msg.edges). */
  function updateLabelState(state) {
    for (const { span, type, slotIdx } of pieceItems) {
      const prefix = type === 'edge' ? 'E' : 'C';
      const idx    = type === 'edge'
        ? state.edges[slotIdx][0]
        : state.corners[slotIdx][0];
      span.textContent = prefix + idx;
    }
  }

  /** Toggle visibility of each label type. */
  function setLabelMode({ faceNames, slots, pieces }) {
    const show = v => v ? '' : 'none';
    for (const s of faceSpans)               s.style.display = show(faceNames);
    for (const s of slotSpans)               s.style.display = show(slots);
    for (const { span } of pieceItems)       span.style.display = show(pieces);
  }

  return { updateLabelState, setLabelMode };
}
```

- [ ] **Step 2: Verify the module loads without errors**

Temporarily add to `main.js` (after `buildMegaminx`):
```javascript
import { buildLabels } from './labels.js';
// ...
const { updateLabelState, setLabelMode } = buildLabels(scene, geometry, stickerMetas);
setLabelMode({ faceNames: true, slots: false, pieces: false });
```
Open browser. Expected: face name labels appear on all stickers. Check that "U" appears on center of the U face, "DFR/R" appears on a sticker near the DFR-R edge, etc.

- [ ] **Step 3: Remove the temporary wiring** (will be done properly in Task 4)

Revert the temporary `buildLabels` call added in Step 2 from `main.js`. Task 4 does this properly.

- [ ] **Step 4: Commit**

```bash
git add viewer/js/labels.js
git commit -m "feat(viewer): add labels.js — CSS2D debug overlay for sticker metadata"
```

---

## Task 4 — Wire up: `main.js` + `index.html`

**Files:**
- Modify: `viewer/js/main.js`
- Modify: `viewer/index.html`

This task connects the labels module into the viewer's state and control flow, and adds the toggle checkboxes.

- [ ] **Step 1: Replace `viewer/js/main.js` with the version below**

```javascript
import { createScene }      from './scene.js';
import { buildMegaminx }    from './megaminx.js';
import { buildLabels }      from './labels.js';
import { updateTopdownSvg } from './svg.js';
import { initControls }     from './controls.js';
import { initLibrary }      from './library.js';
import { createAnimator }   from './animator.js';

const WS_URL = 'ws://localhost:8765';

async function main() {
  const geometry = await (await fetch('/geometry.json')).json();

  const container                                        = document.getElementById('canvas-container');
  const { scene }                                        = createScene(container);
  const { group, updateColors, getMeshesForFace,
          stickerMetas }                                 = buildMegaminx(geometry);
  scene.add(group);

  const { updateLabelState, setLabelMode } = buildLabels(scene, geometry, stickerMetas);

  const animator = createAnimator(scene, geometry, getMeshesForFace);

  let lastState              = null;
  let isPlaying              = false;
  let speed                  = 1.0;
  let playTimer              = null;
  let lastCommandWasBackward = false;

  function stepInterval() { return Math.max(120, 800 / speed); }
  function animDuration()  { return Math.min(stepInterval() * 0.75, 500); }

  function sendCmd(cmd) {
    fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cmd),
    }).catch(console.error);
  }

  function stopPlay() {
    isPlaying = false;
    ctrlApi.setPlaying(false);
    if (playTimer) { clearTimeout(playTimer); playTimer = null; }
  }

  function scheduleNext() {
    playTimer = setTimeout(() => {
      lastCommandWasBackward = false;
      sendCmd({ type: 'step_forward' });
    }, 50);
  }

  // Label toggles
  function syncLabelMode() {
    setLabelMode({
      faceNames: document.getElementById('chk-facename').checked,
      slots:     document.getElementById('chk-slot').checked,
      pieces:    document.getElementById('chk-piece').checked,
    });
    if (lastState) updateLabelState(lastState);
  }
  document.getElementById('chk-facename').addEventListener('change', syncLabelMode);
  document.getElementById('chk-slot').addEventListener('change', syncLabelMode);
  document.getElementById('chk-piece').addEventListener('change', syncLabelMode);

  const ctrlApi = initControls({
    onFirst: () => {
      stopPlay();
      lastCommandWasBackward = false;
      sendCmd({ type: 'goto_move', n: 0 });
    },
    onBack: () => {
      if (animator.isAnimating) return;
      stopPlay();
      lastCommandWasBackward = true;
      sendCmd({ type: 'step_backward' });
    },
    onPlay() {
      if (!lastState || lastState.totalMoves === 0) return;
      if (isPlaying) { stopPlay(); return; }
      isPlaying = true;
      ctrlApi.setPlaying(true);
      if (lastState.moveIndex >= lastState.totalMoves) {
        sendCmd({ type: 'goto_move', n: 0 });
      } else {
        scheduleNext();
      }
    },
    onFwd: () => {
      if (animator.isAnimating) return;
      stopPlay();
      lastCommandWasBackward = false;
      sendCmd({ type: 'step_forward' });
    },
    onLast: () => {
      stopPlay();
      lastCommandWasBackward = false;
      if (lastState) sendCmd({ type: 'goto_move', n: lastState.totalMoves });
    },
    onSpeedChange: v => { speed = v; },
  });

  initLibrary({
    onLoadAlg:    name => { stopPlay(); sendCmd({ type: 'load_algorithm', name }); },
    onAnimateSeq: seq  => { stopPlay(); sendCmd({ type: 'animate_sequence', sequence: seq }); },
  });

  function onMessage(msg) {
    if (msg.type === 'state') {
      lastState = msg;
      const svgEl = document.getElementById('topdown-svg');
      if (svgEl) updateTopdownSvg(svgEl, msg, geometry);

      if (msg.currentMove && !animator.isAnimating) {
        ctrlApi.updateProgress(msg.moveIndex, msg.totalMoves, msg.currentMove, msg.algName);
        animator.animate(msg.currentMove, animDuration(), lastCommandWasBackward, () => {
          updateColors(msg);
          updateLabelState(msg);
          if (isPlaying) {
            if (msg.moveIndex >= msg.totalMoves) stopPlay();
            else scheduleNext();
          }
        });
      } else {
        updateColors(msg);
        updateLabelState(msg);
        ctrlApi.updateProgress(msg.moveIndex, msg.totalMoves, msg.currentMove, msg.algName);
        if (isPlaying) {
          if (msg.moveIndex >= msg.totalMoves) stopPlay();
          else scheduleNext();
        }
      }
    } else if (msg.type === 'loaded') {
      stopPlay();
      ctrlApi.updateProgress(0, msg.moves.length, null, msg.algName);
    } else if (msg.type === 'reset') {
      stopPlay();
      ctrlApi.updateProgress(0, 0, null, null);
    }
  }

  function connect() {
    const ws = new WebSocket(WS_URL);
    ws.onopen    = () => console.log('Megaminx viewer connected');
    ws.onclose   = () => setTimeout(connect, 2000);
    ws.onerror   = e  => console.error('WS error', e);
    ws.onmessage = e  => onMessage(JSON.parse(e.data));
  }
  connect();
}

main().catch(console.error);
```

- [ ] **Step 2: Add checkboxes and CSS to `viewer/index.html`**

In `index.html`, add these three style blocks inside `<style>` (before `</style>`):

```css
    /* Debug label toggles */
    .dbg-toggle {
      font-size: 11px; color: #8b949e; display: flex;
      align-items: center; gap: 3px; cursor: pointer; white-space: nowrap;
    }
    .dbg-toggle input { accent-color: #58a6ff; cursor: pointer; }

    /* CSS2D label DOM elements */
    .dbg-label    { display: flex; flex-direction: column; align-items: center;
                    pointer-events: none; }
    .dbg-facename { font: bold 7px monospace; color: #fff;
                    text-shadow: 0 0 3px #000, 0 0 3px #000; }
    .dbg-slot     { font: 7px monospace; color: #7df;
                    text-shadow: 0 0 3px #000; }
    .dbg-piece    { font: 7px monospace; color: #fd7;
                    text-shadow: 0 0 3px #000; }
```

In `index.html`, add three checkboxes inside `#controls-bar` (after the `<input id="speed-slider">` line):

```html
      <label class="dbg-toggle"><input type="checkbox" id="chk-facename"> Fase</label>
      <label class="dbg-toggle"><input type="checkbox" id="chk-slot">     Slot</label>
      <label class="dbg-toggle"><input type="checkbox" id="chk-piece">    Brikke</label>
```

- [ ] **Step 3: Full manual verification**

```bash
# Ensure server is running:
python -m mcp_server.viewer_server
# Open http://localhost:8080
```

Check each of the following:

1. **Default state**: No labels visible. Cube renders and animates normally.
2. **Fase checkbox ON**: Every sticker gets a white text label. Center of U face shows `U`. An edge sticker near the DFR-R boundary shows `DFR/R`. A corner sticker shows e.g. `BR/R/U`.
3. **Slot checkbox ON**: Blue labels appear showing `E0`–`E29` for edges, `C0`–`C19` for corners. Centers show nothing extra.
4. **Brikke checkbox ON** (solved state): Yellow piece labels match slot labels (`E24` piece = `E24` slot, since solved).
5. **Load an algorithm from the library, step forward once**: Yellow piece labels on the moved face update to new piece numbers. Face and slot labels are unchanged.
6. **Step backward**: Piece labels return to previous values.
7. **All three ON simultaneously**: Three rows of labels on each edge/corner sticker (white / blue / yellow).

- [ ] **Step 4: Commit**

```bash
git add viewer/js/main.js viewer/index.html
git commit -m "feat(viewer): wire debug label toggles — fasenavn, slotnr, brikkenr"
```

---

## Self-Review

**Spec coverage:**
- ✅ Fasenavn per sticker (center: face name; edge: two faces; corner: three faces)
- ✅ Slotnr per edge/corner sticker (`E`/`C` prefix)
- ✅ Brikkenr per edge/corner, dynamically updated from state
- ✅ Three independent toggle checkboxes, all off by default
- ✅ CSS2DRenderer in render loop
- ✅ Labels attached to scene at sticker centers (static position, no animation following)
- ✅ CSS styling matches spec (`.dbg-facename`, `.dbg-slot`, `.dbg-piece`)

**Placeholder scan:** No TBDs or incomplete steps.

**Type consistency:**
- `stickerMetas` returned by `buildMegaminx` in Task 2, consumed by `buildLabels` in Task 3 and `main.js` in Task 4 — field names (`mesh`, `type`, `fi`, `slotIdx`, `faceNames`, `center`) used consistently.
- `updateLabelState(state)` receives the full WebSocket state message (has `.edges[i][0]` and `.corners[i][0]`) — matches `viewer_state.py`'s `state_snapshot()` format.
- `setLabelMode({ faceNames, slots, pieces })` called in `syncLabelMode` with those exact keys.
