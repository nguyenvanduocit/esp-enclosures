import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {sampleTrack, sampleAnimation, measurementLines, layerStarts} from '../viewer/model-core.js';

const load = id => JSON.parse(readFileSync(new URL(`../models/${id}/model.json`, import.meta.url)));
const battery = load('esp32-c3-supermini-18650');
const small = load('esp32-c3-supermini');

test('keyframes interpolate and clamp independently of frame history', () => {
  const keys = [{time: 0, value: [0, 0, 0]}, {time: 1, value: [2, -10, 30]}];
  assert.deepEqual(sampleTrack(keys, .5), [1, -5, 15]);
  assert.deepEqual(sampleTrack(keys, -1), [0, 0, 0]);
  assert.deepEqual(sampleTrack(keys, 2), [2, -10, 30]);
  assert.deepEqual(sampleTrack(keys, .5), [1, -5, 15]);
});

test('all model animations return every part and camera to its installed pose', () => {
  for (const model of [battery, small]) for (const animation of model.animations) {
    for (const time of [0, 1]) {
      const frame = sampleAnimation(model, animation, time);
      assert.ok(Object.values(frame.offsets).every(offset => offset.every(value => value === 0)));
      assert.deepEqual(frame.camera, [0, 0, 0]);
    }
  }
});

test('battery replacement opens its lid before lifting the cell; other parts stay home', () => {
  const animation = battery.animations.find(item => item.id === 'battery');
  const early = sampleAnimation(battery, animation, .2);
  assert.ok(early.offsets.batteryLid[2] > 0);
  assert.equal(early.offsets.cell[2], 0);
  const open = sampleAnimation(battery, animation, .5);
  assert.equal(open.offsets.batteryLid[2], 65);
  assert.equal(open.offsets.cell[2], 40);
  assert.deepEqual(open.offsets.electronicsLid, [0, 0, 0]);
  assert.deepEqual(open.offsets.usbCap, [0, 0, 0]);
});

test('USB removal follows its own axis without moving lids', () => {
  const frame = sampleAnimation(battery, battery.animations.find(item => item.id === 'usb'), .5);
  assert.deepEqual(frame.offsets.usbCap, [0, -24, 0]);
  assert.deepEqual(frame.offsets.batteryLid, [0, 0, 0]);
});

test('measurements keep assembled height; hidden cap changes only the configured variant', () => {
  const spec = battery.measurements.find(item => item.kind === 'case');
  assert.equal(measurementLines(spec, {usbCap: true})[1].label, '85.2 mm · Dài');
  const hidden = measurementLines(spec, {usbCap: false});
  assert.equal(hidden[1].label, '84 mm · Dài');
  assert.equal(hidden[2].b[2] - hidden[2].a[2], 27.2);
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
  for (const id of ['esp32-c3-supermini', 'esp32-c3-supermini-18650']) {
    const model = load(id);
    const data = JSON.parse(readFileSync(new URL(`../models/${id}/${model.print.layers}`, import.meta.url)));
    assert.equal(data.layers.length, model.print.layerCount);
    assert.deepEqual(data.bed, [256, 256]);
    const total = data.types.reduce((sum, type) => sum + layerStarts(data.layers, type.id).at(-1), 0);
    assert.ok(total > 1000);
  }
});
