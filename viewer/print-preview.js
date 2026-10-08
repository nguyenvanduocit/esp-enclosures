import * as THREE from './vendor/three.module.min.js';
import {layerStarts} from './model-core.js';

// Toolpaths from print/layers.json. Layers below the current one are dimmed, the current one is bright;
// both LineSegments of a type read the same vertex buffer through their own geometry's draw range.
export function createPrintPreview(data) {
  const [width, depth] = data.bed;
  const group = new THREE.Group();
  group.position.set(-width / 2, -depth / 2, 0);
  const bed = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), new THREE.MeshBasicMaterial({color: 0x26292b}));
  bed.position.set(width / 2, depth / 2, -.05);
  group.add(bed);
  const types = data.types.map(type => {
    const starts = layerStarts(data.layers, type.id);
    const positions = new Float32Array(starts.at(-1) * 3);
    let offset = 0;
    for (const layer of data.layers) for (const path of layer.paths[type.id] ?? []) {
      for (let i = 2; i < path.length; i += 2) {
        positions.set([path[i - 2] * data.unit, path[i - 1] * data.unit, layer.z, path[i] * data.unit, path[i + 1] * data.unit, layer.z], offset);
        offset += 6;
      }
    }
    const attribute = new THREE.BufferAttribute(positions, 3);
    const line = opacity => {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', attribute);
      return new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({color: type.color, transparent: opacity < 1, opacity}));
    };
    const past = line(.4), current = line(1);
    group.add(past, current);
    return {id: type.id, starts, past, current};
  });
  let layer = data.layers.length - 1;
  function setLayer(index) {
    layer = Math.max(0, Math.min(data.layers.length - 1, index));
    for (const type of types) {
      type.past.geometry.setDrawRange(0, type.starts[layer]);
      type.current.geometry.setDrawRange(type.starts[layer], type.starts[layer + 1] - type.starts[layer]);
    }
  }
  setLayer(layer);
  return {
    group, layerCount: data.layers.length, types: data.types,
    get layer() { return layer; },
    zOf(index) { return data.layers[index].z; },
    setLayer,
    setTypeVisible(id, visible) { const type = types.find(item => item.id === id); type.past.visible = type.current.visible = visible; },
    dispose() { group.traverse(object => { object.geometry?.dispose(); object.material?.dispose(); }); }
  };
}
