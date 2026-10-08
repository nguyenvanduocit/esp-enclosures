import * as THREE from './vendor/three.module.min.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {createPartDrag} from './part-drag.js';
import {createDimensions} from './dimensions.js';
import {clamp, sampleAnimation} from './model-core.js';
import {readBuffer} from './resources.js';

function stlGeometry(buffer) {
  const data = new DataView(buffer);
  if (data.byteLength < 84) throw new Error('STL thiếu dữ liệu');
  const count = data.getUint32(80, true);
  if (data.byteLength !== 84 + count * 50) throw new Error('STL không đúng định dạng binary');
  const positions = new Float32Array(count * 9);
  for (let i = 0; i < count; i++) for (let j = 0; j < 9; j++) positions[i * 9 + j] = data.getFloat32(84 + i * 50 + 12 + j * 4, true);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  return geometry;
}

export async function createViewer({model, folder, canvas, stage, tooltip, signal, onState}) {
  const sources = [...new Set(model.parts.flatMap(part => part.meshes.flatMap(mesh => mesh.src ? [mesh.src] : [])))];
  const buffers = Object.fromEntries(await Promise.all(sources.map(async src => [src, await readBuffer(folder + src)])));
  signal.throwIfAborted();
  const renderer = new THREE.WebGLRenderer({canvas, antialias: true});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0x1c1e20);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, .1, 2000);
  camera.up.set(0, 0, 1);
  camera.position.set(...model.camera.position);
  const controls = new OrbitControls(camera, canvas);
  controls.target.set(...model.camera.target);
  controls.enableDamping = true;
  controls.minDistance = model.camera.minDistance;
  controls.maxDistance = model.camera.maxDistance;
  controls.listenToKeyEvents(canvas);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x344751, 2.5));
  for (const [position, intensity] of [[[30, -60, 100], 3], [[-60, -15, 30], 1.5]]) {
    const light = new THREE.DirectionalLight(0xffffff, intensity);
    light.position.set(...position);
    scene.add(light);
  }
  const grid = new THREE.GridHelper(model.grid.size, model.grid.divisions, 0x414744, 0x343937);
  grid.rotation.x = Math.PI / 2;
  grid.position.z = -.08;
  grid.material.transparent = true;
  grid.material.opacity = .55;
  scene.add(grid);
  const parts = {};
  for (const spec of model.parts) {
    const group = new THREE.Group();
    group.position.set(...spec.position);
    group.rotation.set(...spec.rotation.map(THREE.MathUtils.degToRad));
    for (const data of spec.meshes) {
      const geometry = data.src ? stlGeometry(buffers[data.src]) : new THREE.BoxGeometry(...data.size);
      const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({color: data.color, roughness: .65, metalness: .08}));
      if (data.position) mesh.position.set(...data.position);
      group.add(mesh);
    }
    parts[spec.id] = group;
    scene.add(group);
  }
  const dimensions = createDimensions(scene, model, parts);
  let animation = model.animations[0], time = 0, playing = false, opened = false, manualPose = false;
  let measureProgress = 1, showCase = false, component = '', cameraOffset = new THREE.Vector3();
  let lastTime = 0, frameId;
  const state = () => ({playing, time, opened, animation: animation.id, manualPose});
  const notify = () => onState(state());
  const partDrag = createPartDrag({THREE, scene, camera, controls, canvas, tooltip,
    parts: model.parts.filter(part => part.drag).map(part => ({id: part.id, label: part.label, object: parts[part.id], ...part.drag})),
    onStart() { playing = false; measureProgress = 1; notify(); },
    onMove() { opened = true; manualPose = true; notify(); }
  });

  function applyOffsets(offsets, cameraValue) {
    partDrag.reset();
    manualPose = false;
    for (const part of model.parts) parts[part.id].position.set(...part.position).add(new THREE.Vector3(...(offsets[part.id] ?? [0, 0, 0])));
    const nextCamera = new THREE.Vector3(...cameraValue);
    const delta = nextCamera.clone().sub(cameraOffset);
    camera.position.add(delta);
    controls.target.add(delta);
    cameraOffset.copy(nextCamera);
    opened = Object.values(offsets).some(offset => offset.some(value => Math.abs(value) > .001));
  }
  function setTime(value) {
    time = clamp(value);
    const sample = sampleAnimation(model, animation, time);
    applyOffsets(sample.offsets, sample.camera);
    measureProgress = sample.measureProgress;
    notify();
  }
  function setOpen(value) {
    playing = false;
    time = 0;
    const camera = value ? animation.camera.reduce((best, frame) => Math.hypot(...frame.value) > Math.hypot(...best) ? frame.value : best, [0, 0, 0]) : [0, 0, 0];
    applyOffsets(value ? animation.openPose : {}, camera);
    measureProgress = 1;
    notify();
  }
  function reset() {
    animation = model.animations[0];
    setOpen(false);
    camera.position.set(...model.camera.position);
    controls.target.set(...model.camera.target);
    for (const part of Object.values(parts)) part.visible = true;
    setWireframe(false);
    showCase = false;
    component = '';
    controls.update();
    notify();
  }
  function setWireframe(value) { for (const part of Object.values(parts)) part.traverse(mesh => { if (mesh.isMesh) mesh.material.wireframe = value; }); }
  const resize = () => {
    const rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    renderer.setSize(rect.width, rect.height, false);
    camera.aspect = rect.width / rect.height;
    camera.fov = camera.aspect < .9 ? 46 : 36;
    camera.updateProjectionMatrix();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(stage);
  resize();
  function frame(timestamp) {
    const delta = lastTime ? Math.min((timestamp - lastTime) / 1000, .1) : 0;
    lastTime = timestamp;
    if (playing) {
      const next = Math.min(1, time + delta / animation.duration);
      if (next === 1) playing = false;
      setTime(next);
    }
    dimensions.update({showCase, component, progress: measureProgress});
    partDrag.update();
    if (!partDrag.activePart) controls.update();
    renderer.render(scene, camera);
    frameId = requestAnimationFrame(frame);
  }
  frameId = requestAnimationFrame(frame);
  notify();
  return {
    model, scene, camera, controls, parts, partDrag, dimensions,
    get state() { return state(); },
    togglePlay() { if (!playing && (time === 1 || manualPose || (time === 0 && opened))) setTime(0); playing = !playing; notify(); },
    pause() { playing = false; notify(); },
    scrub(value) { playing = false; setTime(value); },
    setMode(id) { animation = model.animations.find(item => item.id === id); setOpen(false); for (const track of animation.tracks) parts[track.part].visible = true; },
    setOpen, reset, setWireframe,
    setVisible(id, value) { parts[id].visible = value; },
    setMeasurements(caseVisible, componentId) { showCase = caseVisible; component = componentId; },
    setView(id) { const view = model.camera.views.find(item => item.id === id); camera.position.set(...view.offset).add(controls.target); camera.lookAt(controls.target); controls.update(); },
    dispose() {
      cancelAnimationFrame(frameId);
      observer.disconnect();
      partDrag.dispose();
      controls.dispose();
      scene.traverse(object => {
        object.geometry?.dispose();
        if (object.material) { object.material.map?.dispose(); object.material.dispose(); }
      });
      renderer.dispose();
      renderer.forceContextLoss();
    }
  };
}
