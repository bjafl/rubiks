import * as THREE from 'three';

const STICKER_LIFT = 0.006;
const INNER_S = 0.42;

export function buildMegaminx(geometry) {
  const group = new THREE.Group();
  const faceStickerMeshes = [];

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

      // Corner sticker
      const cPrev = verts[km].clone().lerp(verts[k], 2/3);
      const cNext = verts[k].clone().lerp(verts[k1], 1/3);
      const coM = _buildFan(_shrink([cPrev, verts[k], cNext, innerV[k]]), normal, 0x888888, STICKER_LIFT);
      _storeOrig(coM);
      group.add(coM);
      coMeshes.push(coM);
      cornerMeshBySlot[cc[k]].push(coM);
    }

    faceStickerMeshes.push({ center: cMesh, edges: eMeshes, corners: coMeshes });
  }

  function getMeshesForFace(fi) {
    const cc = geometry.faceCornerCycles[fi];
    const ec = geometry.faceEdgeCycles[fi];
    const meshes = [];
    for (const ci of cc) meshes.push(...cornerMeshBySlot[ci]);
    for (const ei of ec) meshes.push(...edgeMeshBySlot[ei]);
    return meshes; // exactly 25 meshes: 5×3 corners + 5×2 edges
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

  return { group, updateColors, getMeshesForFace };
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
    // Reverse winding (face verts are CW when viewed from outside → need CCW for Three.js front-face)
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
