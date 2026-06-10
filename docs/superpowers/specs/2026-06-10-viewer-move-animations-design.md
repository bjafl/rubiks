# Megaminx Viewer — Move Animations Design

## Goal

Add physically correct 3D face rotation animations to the Megaminx viewer. When stepping through an algorithm, each move shows the relevant face pieces rotating around the face normal by the correct angle (72°, 144°, −72°, −144°) before the new sticker colors settle into place.

## Architecture

Three files are affected:

| File | Change |
|---|---|
| `viewer/js/megaminx.js` | Add piece-mesh lookup tables + `origPos` storage; expose `getMeshesForFace` |
| `viewer/js/animator.js` | **New** — pivot group lifecycle, tween loop, baking, easing |
| `viewer/js/main.js` | Hook animation into WS state updates; chain play loop through `onComplete` |

No server changes. No new dependencies.

---

## Section 1 — `megaminx.js` changes

### Lookup tables

During `buildMegaminx(geometry)`, build two arrays alongside the existing `faceStickerMeshes`:

```js
const cornerMeshBySlot = Array.from({ length: 20 }, () => []);
const edgeMeshBySlot   = Array.from({ length: 30 }, () => []);
```

When creating corner sticker mesh at face `fi`, slot `k` (where `cc[k]` is the corner index):
```js
cornerMeshBySlot[cc[k]].push(mesh);
```
Similarly for edge meshes:
```js
edgeMeshBySlot[ec[k]].push(mesh);
```

### `origPos` storage

Immediately after setting each sticker mesh's final position (including the `STICKER_LIFT` offset), store:
```js
mesh.userData.origPos = mesh.position.clone();
mesh.userData.origQuat = mesh.quaternion.clone();
```
This is used to snap meshes back to canonical positions after animation baking.

### `getMeshesForFace(fi)`

Returned alongside `updateColors`:
```js
function getMeshesForFace(fi) {
  const cc = geometry.faceCornerCycles[fi];
  const ec = geometry.faceEdgeCycles[fi];
  const meshes = [faceStickerMeshes[fi].center];
  for (const ci of cc) meshes.push(...cornerMeshBySlot[ci]);
  for (const ei of ec) meshes.push(...edgeMeshBySlot[ei]);
  return meshes; // ~26 meshes
}
```

---

## Section 2 — `animator.js` (new)

```js
export function createAnimator(scene, geometry, getMeshesForFace) { ... }
```

Returns `{ animate(moveName, durationMs, reversed, onComplete), isAnimating }`.

### Move parsing

```js
function parseFaceIndex(move, faceNames) {
  // Try longest name first: DFR before D
  const sorted = [...faceNames].sort((a, b) => b.length - a.length);
  for (const name of sorted) {
    if (move.startsWith(name)) return faceNames.indexOf(name);
  }
  return -1;
}

function parseMoveAngle(move) {
  const step = (Math.PI * 2) / 5; // 72°
  if (move.endsWith('++') || move.endsWith('2')) return step * 2;
  if (move.endsWith('--') || move.endsWith("2'")) return -step * 2;
  if (move.endsWith('-')  || move.endsWith("'")) return -step;
  return step;
}
```

### Pivot group lifecycle

```js
function animate(moveName, durationMs, reversed, onComplete) {
  if (isAnimating) { onComplete(); return; }
  isAnimating = true;

  const fi    = parseFaceIndex(moveName, geometry.faceNames);
  let angle   = parseMoveAngle(moveName);
  if (reversed) angle = -angle;

  const meshes     = getMeshesForFace(fi);
  const faceCenter = new THREE.Vector3(...geometry.faceCenters[fi]);
  const faceNormal = faceCenter.clone().normalize();

  const pivot = new THREE.Group();
  pivot.position.copy(faceCenter);
  scene.add(pivot);
  meshes.forEach(m => pivot.attach(m));

  const axis = faceNormal;
  let startTime = null;

  function tick(now) {
    if (!startTime) startTime = now;
    const t      = Math.min((now - startTime) / durationMs, 1);
    const eased  = t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t+2, 2)/2;
    pivot.setRotationFromAxisAngle(axis, angle * eased);

    if (t < 1) {
      requestAnimationFrame(tick);
    } else {
      // Bake: restore all meshes to scene with canonical positions
      meshes.forEach(m => {
        scene.attach(m);                          // preserves world transform
        m.position.copy(m.userData.origPos);      // snap to canonical slot
        m.quaternion.copy(m.userData.origQuat);
      });
      scene.remove(pivot);
      isAnimating = false;
      onComplete();
    }
  }
  requestAnimationFrame(tick);
}
```

### Safety fallback

If `fi === -1` (unrecognised move name), call `onComplete()` immediately without animating.

---

## Section 3 — `main.js` changes

### Duration calculation

```js
function stepInterval() { return Math.max(120, 800 / speed); }
function animDuration()  { return Math.min(stepInterval() * 0.75, 500); }
```

### WS state handler

```js
function onMessage(msg) {
  if (msg.type === 'state') {
    lastState = msg;
    if (msg.currentMove && !animator.isAnimating) {
      animator.animate(
        msg.currentMove,
        animDuration(),
        lastCommandWasBackward,
        () => {
          updateColors(msg);
          if (isPlaying) {
            if (msg.moveIndex >= msg.totalMoves) stopPlay();
            else scheduleNext();
          }
        }
      );
    } else {
      updateColors(msg);
      ctrlApi.updateProgress(msg.moveIndex, msg.totalMoves, msg.currentMove, msg.algName);
      if (isPlaying) {
        if (msg.moveIndex >= msg.totalMoves) stopPlay();
        else scheduleNext();
      }
    }
    ...
  }
}
```

`ctrlApi.updateProgress` is called immediately when the animation starts (before `onComplete`) so the move counter ticks up as the face begins rotating, not after it finishes. In the non-animated path it is also called immediately.

### Direction tracking

```js
let lastCommandWasBackward = false;

// In onBack:
lastCommandWasBackward = true;
sendCmd({ type: 'step_backward' });

// In onFwd / scheduleNext:
lastCommandWasBackward = false;
sendCmd({ type: 'step_forward' });
```

### Manual step guard

```js
onBack: () => {
  if (animator.isAnimating) return;
  stopPlay();
  lastCommandWasBackward = true;
  sendCmd({ type: 'step_backward' });
},
onFwd: () => {
  if (animator.isAnimating) return;
  stopPlay();
  lastCommandWasBackward = false;
  sendCmd({ type: 'step_forward' });
},
```

### Auto-play loop

`scheduleNext` no longer uses `setTimeout` — the animation duration provides natural pacing:
```js
function scheduleNext() {
  lastCommandWasBackward = false;
  sendCmd({ type: 'step_forward' });
}
```
`sendCmd` fires immediately; the next `scheduleNext` call comes from inside `onComplete` after the animation finishes.

### Jump / reset commands

`goto_move` and `reset` produce states with `currentMove: null` — the `null` check bypasses animation, calling `updateColors` instantly.

---

## Edge cases

| Scenario | Behaviour |
|---|---|
| `currentMove` is null (jump/reset) | Instant `updateColors`, no animation |
| Unknown move name | `fi === -1` → skip animation, call `onComplete` |
| Animation already running (shouldn't happen due to guard) | `onComplete` called immediately, no crash |
| Speed so fast that `animDuration < 50ms` | Animation still runs; at extreme speed the 75% rule means 90ms minimum |

---

## What is NOT in scope

- Smooth face rotation for `goto_move` jumps (multi-step, no single face to rotate)
- Easing curve configurability (always ease-in-out)
- Animation queue / buffering (ignored presses while animating is acceptable)
- Server-side changes of any kind
