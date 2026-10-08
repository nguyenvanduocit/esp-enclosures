import * as THREE from './vendor/three.module.min.js';
import {clamp, measurementLines} from './model-core.js';

function makeLine(parent, spec) {
  const group = new THREE.Group();
  parent.add(group);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(18), 3));
  const line = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({color: spec.color, depthTest: false, transparent: true}));
  line.renderOrder = 4;
  group.add(line);
  const canvas = document.createElement('canvas');
  canvas.width = 640;
  canvas.height = 128;
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const label = new THREE.Sprite(new THREE.SpriteMaterial({map: texture, depthTest: false, transparent: true}));
  label.scale.set(spec.labelWidth, spec.labelWidth / 5, 1);
  label.renderOrder = 5;
  group.add(label);
  return {group, line, label, canvas, texture, text: ''};
}

function updateLine(dimension, data, color, progress) {
  dimension.group.visible = progress > .001;
  if (!dimension.group.visible) return;
  const a = new THREE.Vector3(...data.a), b = new THREE.Vector3(...data.b);
  const end = a.clone().lerp(b, progress);
  const attribute = dimension.line.geometry.attributes.position;
  attribute.array.set([...data.a, ...end.toArray(), ...data.anchorA, ...data.a, ...data.anchorB, ...data.b]);
  attribute.needsUpdate = true;
  dimension.line.geometry.computeBoundingSphere();
  dimension.line.material.opacity = Math.min(progress * 3, 1);
  dimension.label.position.copy(a.lerp(b, .5).add(new THREE.Vector3(...data.labelOffset)));
  dimension.label.material.opacity = Math.max(0, (progress - .6) / .4);
  if (dimension.text === data.label) return;
  dimension.text = data.label;
  const ctx = dimension.canvas.getContext('2d');
  ctx.clearRect(0, 0, 640, 128);
  ctx.fillStyle = '#232527';
  ctx.beginPath();
  ctx.roundRect(4, 12, 632, 104, 12);
  ctx.fill();
  ctx.font = '500 48px sans-serif';
  ctx.fillStyle = color;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(data.label, 320, 67);
  dimension.texture.needsUpdate = true;
}

export function createDimensions(scene, model, parts) {
  const entries = model.measurements.map(spec => {
    const group = new THREE.Group();
    scene.add(group);
    return {spec, group, lines: spec.lines.map(() => makeLine(group, spec))};
  });
  return {
    update({showCase, component, progress}) {
      const visible = Object.fromEntries(Object.entries(parts).map(([id, part]) => [id, part.visible]));
      for (const {spec, group, lines} of entries) {
        group.visible = (spec.kind === 'case' ? showCase : spec.id === component) && (!spec.visibleWith || visible[spec.visibleWith]);
        const installed = model.parts.find(part => part.id === spec.followPart).position;
        group.position.copy(parts[spec.followPart].position).sub(new THREE.Vector3(...installed));
        const data = measurementLines(spec, visible);
        for (let i = 0; i < lines.length; i++) updateLine(lines[i], data[i], spec.color, clamp(progress * lines.length - i));
      }
    },
    get labels() { return Object.fromEntries(entries.map(entry => [entry.spec.id, entry.lines.map(line => line.text)])); },
    get visible() { return entries.filter(entry => entry.group.visible).map(entry => entry.spec.id); }
  };
}
