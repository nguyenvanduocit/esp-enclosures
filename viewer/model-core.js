export const clamp = value => Math.min(1, Math.max(0, value));

export function sampleTrack(keyframes, time) {
  if (time <= keyframes[0].time) return [...keyframes[0].value];
  for (let i = 1; i < keyframes.length; i++) {
    const next = keyframes[i], previous = keyframes[i - 1];
    if (time > next.time) continue;
    const t = (time - previous.time) / (next.time - previous.time);
    const eased = t * t * (3 - 2 * t);
    return previous.value.map((value, axis) => value + (next.value[axis] - value) * eased);
  }
  return [...keyframes.at(-1).value];
}

// Offsets are relative to the installed pose, never to the previous frame.
export function sampleAnimation(model, animation, time) {
  const offsets = Object.fromEntries(model.parts.map(part => [part.id, [0, 0, 0]]));
  for (const track of animation.tracks) offsets[track.part] = sampleTrack(track.keyframes, time);
  const [from, to] = animation.measureReveal;
  return {offsets, camera: sampleTrack(animation.camera, time), measureProgress: clamp((time - from) / (to - from))};
}

export function measurementLines(measurement, visibility) {
  return measurement.variants?.find(variant => visibility[variant.whenHidden] === false)?.lines ?? measurement.lines;
}

// Overall download fraction, or null (indeterminate) until every download has reported a size.
export function loadFraction(downloads) {
  let loaded = 0, total = 0;
  for (const download of downloads) {
    if (!download?.total) return null;
    loaded += Math.min(download.loaded, download.total);
    total += download.total;
  }
  return total ? loaded / total : null;
}

// Vertex index where each layer's segments start in one toolpath type; LineSegments use two vertices per segment.
export function layerStarts(layers, type) {
  const starts = [0];
  for (const layer of layers) {
    let count = starts.at(-1);
    for (const path of layer.paths[type] ?? []) count += (path.length / 2 - 1) * 2;
    starts.push(count);
  }
  return starts;
}
