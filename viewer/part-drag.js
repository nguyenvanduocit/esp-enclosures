// Pointer interaction for the viewer; part axes are in world coordinates.
export function createPartDrag({THREE, scene, camera, controls, canvas, parts, tooltip, onStart, onMove}) {
  const events = new AbortController();
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const owner = new WeakMap();
  const arrow = new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(), 15, 0xb7cebf, 3, 1.5);
  arrow.visible = false;
  for (const mesh of [arrow.line, arrow.cone]) {
    mesh.material.depthTest = false;
    mesh.material.transparent = true;
    mesh.renderOrder = 8;
  }
  scene.add(arrow);
  for (const part of parts) {
    part.home = part.object.position.clone();
    part.axis = new THREE.Vector3(...part.axis);
    part.materials = [];
    part.object.traverse(mesh => {
      if (!mesh.isMesh) return;
      owner.set(mesh, part);
      part.materials.push({material: mesh.material, color: mesh.material.emissive.clone(), intensity: mesh.material.emissiveIntensity});
    });
  }
  let hovered = null, drag = null, lastPointer = null;
  const offset = part => part.object.position.clone().sub(part.home).dot(part.axis);

  function pick(event) {
    const rect = canvas.getBoundingClientRect();
    pointer.set((event.clientX-rect.left)/rect.width*2-1, -(event.clientY-rect.top)/rect.height*2+1);
    scene.updateMatrixWorld(true);
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(parts.filter(p => p.object.visible).map(p => p.object), true);
    return hits.length ? owner.get(hits[0].object) : null;
  }

  function hover(part) {
    if (part === hovered) return;
    if (hovered) for (const saved of hovered.materials) {
      saved.material.emissive.copy(saved.color);
      saved.material.emissiveIntensity = saved.intensity;
    }
    hovered = part;
    if (part) for (const {material} of part.materials) {
      material.emissive.setHex(0xb7cebf);
      material.emissiveIntensity = .38;
    }
    canvas.style.cursor = part ? 'grab' : '';
    arrow.visible = !!part;
    tooltip.hidden = !part;
  }

  function update() {
    if (hovered && !hovered.object.visible) { finish(); hover(null); }
    if (!hovered) return;
    const box = new THREE.Box3().setFromObject(hovered.object);
    const center = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3());
    const extent = Math.abs(hovered.axis.x)*size.x + Math.abs(hovered.axis.y)*size.y + Math.abs(hovered.axis.z)*size.z;
    arrow.position.copy(center).addScaledVector(hovered.axis, extent/2+2);
    arrow.setDirection(hovered.axis);
    const distance = Math.max(0, offset(hovered));
    tooltip.textContent = hovered.label+(distance>.05 ? ` · ${distance.toFixed(1)} mm` : '');
    if (drag?.fallback) tooltip.textContent += ' · ↕';
    if (lastPointer) {
      const rect = canvas.getBoundingClientRect();
      tooltip.style.left = Math.max(8, Math.min(rect.width-tooltip.offsetWidth-8, lastPointer.x-rect.left+16))+'px';
      tooltip.style.top = Math.max(8, Math.min(rect.height-tooltip.offsetHeight-8, lastPointer.y-rect.top+20))+'px';
    }
  }

  function finish(cancel = false) {
    if (!drag) return;
    const ended = drag;
    drag = null;
    if (cancel) ended.part.object.position.copy(ended.startPosition);
    controls.enabled = ended.controlsEnabled;
    if (canvas.hasPointerCapture(ended.pointerId)) canvas.releasePointerCapture(ended.pointerId);
    canvas.style.cursor = hovered ? 'grab' : '';
  }

  canvas.addEventListener('pointerdown', event => {
    // Touch gestures retain OrbitControls' one-finger orbit and two-finger zoom.
    if (event.pointerType === 'touch' || event.button !== 0 || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || drag) return;
    const part = pick(event);
    if (!part) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    hover(part);
    onStart(part);
    const rect = canvas.getBoundingClientRect();
    const center = new THREE.Box3().setFromObject(part.object).getCenter(new THREE.Vector3());
    const from = center.clone().project(camera), to = center.clone().addScaledVector(part.axis, 10).project(camera);
    const screenAxis = new THREE.Vector2((to.x-from.x)*rect.width/2, -(to.y-from.y)*rect.height/2);
    const fallback = screenAxis.length() < 8;
    let pixelsPerMM = screenAxis.length()/10;
    if (fallback) {
      // Looking along the extraction axis has no useful on-screen projection.
      screenAxis.set(0, -1);
      pixelsPerMM = rect.height/(2*camera.position.distanceTo(center)*Math.tan(THREE.MathUtils.degToRad(camera.fov/2)));
    } else screenAxis.normalize();
    drag = {part, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY,
      startPosition: part.object.position.clone(), startOffset: offset(part), screenAxis, pixelsPerMM, fallback,
      controlsEnabled: controls.enabled};
    controls.enabled = false;
    canvas.setPointerCapture(event.pointerId);
    canvas.style.cursor = 'grabbing';
    lastPointer = {x: event.clientX, y: event.clientY};
    update();
  }, {capture: true, signal: events.signal});

  canvas.addEventListener('pointermove', event => {
    if (event.pointerType === 'touch') return;
    lastPointer = {x: event.clientX, y: event.clientY};
    if (!drag) {
      hover(event.buttons || event.altKey ? null : pick(event));
      update();
      return;
    }
    if (event.pointerId !== drag.pointerId) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const dx = event.clientX-drag.startX, dy = event.clientY-drag.startY;
    const amount = THREE.MathUtils.clamp(drag.startOffset+(dx*drag.screenAxis.x+dy*drag.screenAxis.y)/drag.pixelsPerMM, 0, drag.part.maxDistance);
    drag.part.object.position.copy(drag.part.home).addScaledVector(drag.part.axis, amount);
    onMove(drag.part, amount);
    update();
  }, {capture: true, signal: events.signal});

  for (const type of ['pointerup', 'pointercancel']) canvas.addEventListener(type, event => {
    if (!drag || event.pointerId !== drag.pointerId) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    finish(type === 'pointercancel');
  }, {capture: true, signal: events.signal});
  canvas.addEventListener('lostpointercapture', () => finish(), {signal: events.signal});
  canvas.addEventListener('pointerleave', () => { if (!drag) hover(null); }, {signal: events.signal});
  window.addEventListener('blur', () => { finish(); hover(null); }, {signal: events.signal});
  window.addEventListener('keydown', event => {
    if (event.key === 'Escape' && drag) { event.preventDefault(); finish(true); hover(null); }
  }, {signal: events.signal});
  return {
    update,
    dispose() { finish(); hover(null); events.abort(); scene.remove(arrow); for (const mesh of [arrow.line, arrow.cone]) { mesh.geometry.dispose(); mesh.material.dispose(); } },
    reset() { finish(); hover(null); },
    get activePart() { return drag?.part.id ?? null; },
    get hoveredPart() { return hovered?.id ?? null; }
  };
}
