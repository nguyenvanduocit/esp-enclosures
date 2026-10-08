import {$, element} from './dom.js';
import {readJSON} from './resources.js';
import {createScene} from './scene.js';
import {createPrintPreview} from './print-preview.js';
import {createStatus} from './status.js';

const status = createStatus($('printStatus'));

// Looks at the bed (origin at its centre) from the front left, framed by the bed's larger side.
function bedCamera([width, depth]) {
  const size = Math.max(width, depth);
  return {position: [size * .66, -size * 1.02, size * .9], target: [0, 0, 10], minDistance: 20, maxDistance: size * 3.5};
}
let sceneView = null, preview = null, timer = null, loading = null;

const grams = value => `${(Math.round(value * 10) / 10).toLocaleString('vi')} g`;
function duration(seconds) {
  const minutes = Math.round(seconds / 60), hours = Math.floor(minutes / 60);
  return hours ? `${hours} giờ ${minutes % 60} phút` : `${minutes} phút`;
}

function renderStats(model) {
  const labels = Object.fromEntries(model.parts.map(part => [part.id, part.label]));
  const rows = [
    ['Cả bàn in', `${grams(model.print.grams)} · ${duration(model.print.seconds)} · ${model.print.layerCount} lớp`],
    ...model.print.parts.map(part => [`${labels[part.id]} (in riêng)`, `${grams(part.grams)} · ${duration(part.seconds)}`])
  ];
  const table = element('table'), body = element('tbody');
  for (const [name, value] of rows) {
    const row = element('tr'), heading = element('th', name);
    heading.scope = 'row';
    row.append(heading, element('td', value));
    body.append(row);
  }
  table.append(body);
  $('printStats').replaceChildren(table, element('small', `${model.print.slicer}. Số liệu từng chi tiết tính cho việc in riêng chi tiết đó, nên không cộng lại thành số của cả bàn in.`));
}

function renderTypes(data) {
  $('printTypes').replaceChildren();
  for (const type of preview.types.filter(type => data.layers.some(layer => layer.paths[type.id]?.length))) {
    const label = element('label'), input = element('input'), swatch = element('span', undefined, 'swatch');
    input.type = 'checkbox';
    input.checked = true;
    input.onchange = () => preview.setTypeVisible(type.id, input.checked);
    swatch.style.background = type.color;
    label.append(input, swatch, document.createTextNode(type.label));
    $('printTypes').append(label);
  }
}

function showLayer(index) {
  preview.setLayer(index);
  $('printLayer').value = String(preview.layer + 1);
  $('printLayerLabel').textContent = `Lớp ${preview.layer + 1}/${preview.layerCount} · Z ${preview.zOf(preview.layer).toLocaleString('vi')} mm`;
}

function syncPlay(playing) {
  $('printPlay').setAttribute('aria-pressed', String(playing));
  $('printPlay').setAttribute('aria-label', playing ? 'Tạm dừng' : 'Phát');
  $('printPlay').title = playing ? 'Tạm dừng' : 'Phát';
}

function stopPlay() {
  clearInterval(timer);
  timer = null;
  syncPlay(false);
}

export async function showPrint({model, folder}, retry) {
  $('printScreen').hidden = false;
  $('printModelTitle').textContent = model.title;
  $('modelLink').href = '#model/' + model.id;
  document.title = 'Mô phỏng in · ' + model.title + ' · Bàn in';
  $('printControls').hidden = true;
  $('printCanvas').hidden = true;
  if (!model.print) {
    status.info('Model này chưa có dữ liệu in. Tạo bằng lệnh:', {detail: `uv run printkit slice ${model.id}`});
    document.body.dataset.ready = 'true';
    return;
  }
  loading = new AbortController();
  const request = loading;
  status.loading('Đang tải dữ liệu in…');
  try {
    const data = await readJSON(folder + model.print.layers, (loaded, total) => { if (!request.signal.aborted) status.progress(total ? Math.min(loaded / total, 1) : null); });
    request.signal.throwIfAborted();
    preview = createPrintPreview(data);
    $('printCanvas').replaceWith($('printCanvas').cloneNode());
    $('printCanvas').hidden = false;
    sceneView = createScene({canvas: $('printCanvas'), stage: $('printStage'), camera: bedCamera(data.bed)});
    sceneView.scene.add(preview.group);
    sceneView.start(() => sceneView.controls.update());
    $('printLayer').max = String(preview.layerCount);
    renderTypes(data);
    renderStats(model);
    showLayer(preview.layerCount - 1);
    $('printControls').hidden = false;
    status.clear();
    document.body.dataset.ready = 'true';
  } catch (error) {
    if (request.signal.aborted) return;
    preview?.dispose();
    sceneView?.dispose();
    sceneView = preview = null;
    $('printCanvas').hidden = true;
    status.error('Không tải được dữ liệu in.', {detail: error.message, retry});
    window.viewerErrors.push(String(error));
  }
}

export function hidePrint() {
  loading?.abort();
  loading = null;
  status.clear();
  stopPlay();
  sceneView?.dispose();
  sceneView = null;
  preview = null;
  $('printScreen').hidden = true;
}

$('printLayer').oninput = event => { stopPlay(); showLayer(Number(event.target.value) - 1); };
$('printPlay').onclick = () => {
  if (timer) return stopPlay();
  if (preview.layer === preview.layerCount - 1) showLayer(0);
  syncPlay(true);
  timer = setInterval(() => {
    if (preview.layer === preview.layerCount - 1) return stopPlay();
    showLayer(preview.layer + 1);
  }, 1000 / 15);
};
