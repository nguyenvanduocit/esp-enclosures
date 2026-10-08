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
