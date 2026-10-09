import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {sampleTrack, sampleAnimation, measurementLines, layerStarts, loadFraction} from '../viewer/model-core.js';

const load = id => JSON.parse(readFileSync(new URL(`../models/${id}/model.json`, import.meta.url)));
const esp32 = load('kit-esp32');
const battery = load('kit-battery');

test('keyframes interpolate and clamp independently of frame history', () => {
  const keys = [{time: 0, value: [0, 0, 0]}, {time: 1, value: [2, -10, 30]}];
  assert.deepEqual(sampleTrack(keys, .5), [1, -5, 15]);
  assert.deepEqual(sampleTrack(keys, -1), [0, 0, 0]);
  assert.deepEqual(sampleTrack(keys, 2), [2, -10, 30]);
  assert.deepEqual(sampleTrack(keys, .5), [1, -5, 15]);
});

test('all model animations return every part and camera to its installed pose', () => {
  for (const model of [esp32, battery]) for (const animation of model.animations) {
    for (const time of [0, 1]) {
      const frame = sampleAnimation(model, animation, time);
      assert.ok(Object.values(frame.offsets).every(offset => offset.every(value => value === 0)));
      assert.deepEqual(frame.camera, [0, 0, 0]);
    }
  }
});

test('opening the lid lifts it and its fasteners; other parts stay home', () => {
  const animation = battery.animations.find(item => item.id === 'open');
  const moving = new Set(animation.tracks.map(track => track.part));
  const frame = sampleAnimation(battery, animation, .4);
  assert.ok(frame.offsets.lid.some(value => value !== 0));
  for (const part of battery.parts) if (!moving.has(part.id)) assert.deepEqual(frame.offsets[part.id], [0, 0, 0]);
});

test('lid follows its own removal axis without moving the shell', () => {
  const animation = battery.animations.find(item => item.id === 'open');
  const frame = sampleAnimation(battery, animation, .5);
  assert.deepEqual(frame.offsets.lid, animation.openPose.lid);
  assert.deepEqual(frame.offsets.shell, [0, 0, 0]);
});

test('measurements keep assembled size; a variant replaces lines only while its part is hidden', () => {
  const spec = battery.measurements.find(item => item.kind === 'case');
  assert.equal(measurementLines(spec, {lid: true})[2].label, '39.8 mm · Cao');
  const variant = {...spec, variants: [{whenHidden: 'lid', lines: spec.lines.slice(0, 2)}]};
  assert.equal(measurementLines(variant, {lid: true}).length, 3);
  assert.equal(measurementLines(variant, {lid: false}).length, 2);
});

test('arbitrary model and part ids work without enclosure-specific branches', () => {
  const model = {parts: [{id: 'drawer'}, {id: 'cabinet'}]};
  const animation = {tracks: [{part: 'drawer', keyframes: [{time: 0, value: [0, 0, 0]}, {time: 1, value: [100, 0, 0]}]}], camera: [{time: 0, value: [0, 0, 0]}, {time: 1, value: [0, 0, 0]}], measureReveal: [.2, .8]};
  const frame = sampleAnimation(model, animation, .5);
  assert.deepEqual(frame.offsets, {drawer: [50, 0, 0], cabinet: [0, 0, 0]});
  assert.ok(Math.abs(frame.measureProgress - .5) < 1e-10);
});

test('layer starts count two vertices per polyline segment', () => {
  const layers = [
    {z: .2, paths: {outer_wall: [[0, 0, 10, 0, 10, 10]], infill: [[0, 0, 5, 5]]}},
    {z: .36, paths: {}},
    {z: .52, paths: {outer_wall: [[0, 0, 1, 1], [2, 2, 3, 3, 4, 4]]}},
  ];
  assert.deepEqual(layerStarts(layers, 'outer_wall'), [0, 4, 4, 10]);
  assert.deepEqual(layerStarts(layers, 'infill'), [0, 2, 2, 2]);
  assert.deepEqual(layerStarts(layers, 'support'), [0, 0, 0, 0]);
});

test('sliced models ship toolpaths for every layer', () => {
  const ids = JSON.parse(readFileSync(new URL('../models.json', import.meta.url))).map(path => path.split('/')[1]);
  const sliced = ids.filter(id => load(id).print);
  assert.deepEqual(sliced, ['kit-esp32', 'kit-battery', 'kit-display', 'kit-bme280', 'kit-mpu6050', 'kit-pir']);
  for (const id of sliced) {
    const model = load(id);
    const data = JSON.parse(readFileSync(new URL(`../models/${id}/${model.print.layers}`, import.meta.url)));
    assert.equal(data.layers.length, model.print.layerCount);
    assert.deepEqual(data.bed, [256, 256]);
    const total = data.types.reduce((sum, type) => sum + layerStarts(data.layers, type.id).at(-1), 0);
    assert.ok(total > 1000);
  }
});

test('print preview draws past layers opaque and darker than the full-colour current layer', async () => {
  const {createPrintPreview} = await import('../viewer/print-preview.js');
  const color = '#5aa7e8';
  const preview = createPrintPreview({
    bed: [100, 100], unit: 1, types: [{id: 'solid', color}],
    layers: [0, 1, 2].map(z => ({z, paths: {solid: [[0, 0, 10, 0, 10, 10]]}}))
  });
  const [past, current] = preview.group.children.filter(child => child.isLineSegments);
  assert.equal(past.material.transparent, false);
  assert.equal(current.material.color.getHexString(), '5aa7e8');
  assert.ok(past.material.color.r < current.material.color.r * .5 && past.material.color.b < current.material.color.b * .5);
  preview.dispose();
});

test('load progress is known only once every download reports a size', () => {
  assert.equal(loadFraction([{loaded: 50, total: 100}, null]), null);
  assert.equal(loadFraction([{loaded: 50, total: 100}, {loaded: 0, total: 0}]), null);
  assert.equal(loadFraction([{loaded: 50, total: 100}, {loaded: 150, total: 300}]), .5);
  assert.equal(loadFraction([{loaded: 120, total: 100}]), 1);
  assert.equal(loadFraction([]), null);
});
