import * as THREE from 'three';

/**
 * createAnimator — manages 3D face-rotation tweens for the Megaminx viewer.
 *
 * @param {THREE.Scene} scene
 * @param {object} geometry  — parsed geometry.json
 * @param {function} getMeshesForFace  — (fi: number) => THREE.Mesh[]
 */
export function createAnimator(scene, geometry, getMeshesForFace) {
  let _isAnimating = false;

  const _faceNames   = geometry.faceNames;
  const _faceCenters = geometry.faceCenters;
  const _sortedNames = [..._faceNames].sort((a, b) => b.length - a.length);

  function _parseFaceIndex(move) {
    for (const name of _sortedNames) {
      if (move.startsWith(name)) return _faceNames.indexOf(name);
    }
    return -1;
  }

  function _parseMoveAngle(move) {
    const step = (Math.PI * 2) / 5;  // 72° in radians
    if (move.endsWith('++') || move.endsWith('2'))  return  step * 2;
    if (move.endsWith('--') || move.endsWith("2'")) return -step * 2;
    if (move.endsWith('-')  || move.endsWith("'"))  return -step;
    return step;
  }

  function _ease(t) {
    return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  }

  /**
   * Animate a single move. Calls onComplete() when the tween finishes
   * (or immediately if already animating or move is unrecognised).
   *
   * @param {string}   moveName   — e.g. "R", "U-", "BR++", "dR2'"
   * @param {number}   durationMs — total tween duration in milliseconds
   * @param {boolean}  reversed   — negate the rotation angle (for step_backward)
   * @param {function} onComplete — called after baking; apply new state here
   */
  function animate(moveName, durationMs, reversed, onComplete) {
    if (_isAnimating) { onComplete(); return; }

    const fi = _parseFaceIndex(moveName);
    if (fi === -1) { onComplete(); return; }

    _isAnimating = true;
    let angle = _parseMoveAngle(moveName);
    if (reversed) angle = -angle;

    const meshes     = getMeshesForFace(fi);
    const faceCenter = new THREE.Vector3(..._faceCenters[fi]);
    const axis       = faceCenter.clone().normalize();

    const pivot = new THREE.Group();
    pivot.position.copy(faceCenter);
    scene.add(pivot);
    meshes.forEach(m => pivot.attach(m));

    if (durationMs <= 0) {
      meshes.forEach(m => {
        scene.attach(m);
        m.position.copy(m.userData.origPos);
        m.quaternion.copy(m.userData.origQuat);
      });
      scene.remove(pivot);
      _isAnimating = false;
      onComplete();
      return;
    }

    let startTime = null;

    function tick(now) {
      if (!startTime) startTime = now;
      const t     = Math.min((now - startTime) / durationMs, 1);
      const eased = _ease(t);
      pivot.setRotationFromAxisAngle(axis, angle * eased);

      if (t < 1) {
        requestAnimationFrame(tick);
      } else {
        // Bake: restore each mesh to scene with canonical (pre-rotation) position
        meshes.forEach(m => {
          scene.attach(m);                       // preserves world transform
          m.position.copy(m.userData.origPos);   // snap to canonical slot
          m.quaternion.copy(m.userData.origQuat);
        });
        scene.remove(pivot);
        _isAnimating = false;
        onComplete();
      }
    }
    requestAnimationFrame(tick);
  }

  return {
    get isAnimating() { return _isAnimating; },
    animate,
  };
}
