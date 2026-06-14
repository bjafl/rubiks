const SVG_NS = 'http://www.w3.org/2000/svg';
const INNER_SCALE = 0.42;

/**
 * Update the top-down SVG element in place.
 * Shows U face + 5 neighboring faces around it as pentagons.
 * Uses createElementNS to build DOM nodes — no innerHTML.
 */
export function updateTopdownSvg(svgEl, state, geometry) {
  while (svgEl.firstChild) {
    svgEl.removeChild(svgEl.lastChild);
  }

  const faceNames  = geometry.faceNames;
  const faceColors = geometry.faceColors;
  const R = 55;
  const D = 88;

  // Find the 5 upper-ring neighbor face indices (faces sharing a corner with U)
  const neighborSet = new Set();
  for (const slot of geometry.faceCornerCycles[0]) {
    for (const f of geometry.cornerFaces[slot]) {
      if (f !== 0) neighborSet.add(f);
    }
  }
  const neighbors = [...neighborSet].slice(0, 5);

  function addPolygon(points, fill, stroke, strokeWidth) {
    const el = document.createElementNS(SVG_NS, 'polygon');
    el.setAttribute('points', points.map(p => p.map(x => x.toFixed(2)).join(',')).join(' '));
    el.setAttribute('fill', fill);
    el.setAttribute('stroke', stroke || '#222');
    el.setAttribute('stroke-width', strokeWidth || '1');
    svgEl.appendChild(el);
  }

  function pentagonPoints(cx, cy, r, rotDeg) {
    const rot = rotDeg || 0;
    return Array.from({ length: 5 }, (_, i) => {
      const a = (i * 72 - 90 + rot) * Math.PI / 180;
      return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    });
  }

  // U face background
  addPolygon(pentagonPoints(0, 0, R), faceColors['U']);
  // U center sticker
  addPolygon(pentagonPoints(0, 0, R * INNER_SCALE), _getCenterColor(0, geometry), 'none', '0');

  for (let k = 0; k < 5; k++) {
    const angle = (k * 72 - 90) * Math.PI / 180;
    const nx = D * Math.cos(angle);
    const ny = D * Math.sin(angle);
    const fi = neighbors[k] ?? (k + 1);
    addPolygon(pentagonPoints(nx, ny, R * 0.65, k * 72), faceColors[faceNames[fi]]);
  }
}

function _getCenterColor(fi, geometry) {
  return geometry.faceColors[geometry.faceNames[fi]];
}
