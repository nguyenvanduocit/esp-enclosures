import * as THREE from './vendor/three.module.min.js';
import {OrbitControls} from './vendor/OrbitControls.js';

// One WebGL canvas with an orbit camera (Z up) that follows the size of its stage element.
export function createScene({canvas, stage, camera: view}) {
  const renderer = new THREE.WebGLRenderer({canvas, antialias: true});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0x1c1e20);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(36, 1, .1, 2000);
  camera.up.set(0, 0, 1);
  camera.position.set(...view.position);
  const controls = new OrbitControls(camera, canvas);
  controls.target.set(...view.target);
  controls.enableDamping = true;
  controls.minDistance = view.minDistance;
  controls.maxDistance = view.maxDistance;
  controls.listenToKeyEvents(canvas);
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
  let lastTime = 0, frameId;
  return {
    renderer, scene, camera, controls,
    // onFrame(seconds since the previous frame) runs before every render.
    start(onFrame) {
      const frame = timestamp => {
        const delta = lastTime ? Math.min((timestamp - lastTime) / 1000, .1) : 0;
        lastTime = timestamp;
        onFrame(delta);
        renderer.render(scene, camera);
        frameId = requestAnimationFrame(frame);
      };
      frameId = requestAnimationFrame(frame);
    },
    dispose() {
      cancelAnimationFrame(frameId);
      observer.disconnect();
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
