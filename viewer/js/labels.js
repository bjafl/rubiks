import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

export function buildLabels(scene, geometry, stickerMetas) {
  const faceSpans  = [];
  const slotSpans  = [];
  const pieceItems = [];

  for (const meta of stickerMetas) {
    const div = document.createElement('div');
    div.className = 'dbg-label';

    const fSpan = document.createElement('span');
    fSpan.className = 'dbg-facename';
    fSpan.textContent = meta.faceNames;
    fSpan.style.display = 'none';
    div.appendChild(fSpan);
    faceSpans.push(fSpan);

    if (meta.type !== 'center') {
      const prefix = meta.type === 'edge' ? 'E' : 'C';

      const sSpan = document.createElement('span');
      sSpan.className = 'dbg-slot';
      sSpan.textContent = prefix + meta.slotIdx;
      sSpan.style.display = 'none';
      div.appendChild(sSpan);
      slotSpans.push(sSpan);

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

  function updateLabelState(state) {
    for (const { span, type, slotIdx } of pieceItems) {
      const prefix = type === 'edge' ? 'E' : 'C';
      const idx    = type === 'edge'
        ? state.edges[slotIdx][0]
        : state.corners[slotIdx][0];
      span.textContent = prefix + idx;
    }
  }

  function setLabelMode({ faceNames, slots, pieces }) {
    const show = v => v ? '' : 'none';
    for (const s of faceSpans)               s.style.display = show(faceNames);
    for (const s of slotSpans)               s.style.display = show(slots);
    for (const { span } of pieceItems)       span.style.display = show(pieces);
  }

  return { updateLabelState, setLabelMode };
}
