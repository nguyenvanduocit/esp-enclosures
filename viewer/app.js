import {readJSON, downloadURL} from './resources.js';
import {createViewer} from './renderer.js';
import {createPrintPreview} from './print-preview.js';

const $ = id => document.getElementById(id);
window.viewerErrors = [];
window.addEventListener('error', event => window.viewerErrors.push(event.message));
window.addEventListener('unhandledrejection', event => window.viewerErrors.push(String(event.reason)));
const normalize = text => text.toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
let catalog = [], viewer = null, loading = null, activeId = null, resources = [], thumbnails = [];
let preview = null, printTimer = null, activeEntry = null;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function renderGallery() {
  for (const resource of thumbnails) resource.dispose();
  thumbnails = [];
  const query = normalize($('search').value.trim());
  $('cards').replaceChildren();
  const visible = catalog.filter(({model}) => normalize(`${model.title} ${model.description} ${model.id}`).includes(query));
  for (const {model, folder} of visible) {
    const card = element('article', undefined, 'card');
    const link = element('a');
    link.href = '#model/' + model.id;
    const image = element('img');
    const source = downloadURL(folder + model.thumbnail, 'image/png');
    thumbnails.push(source);
    image.src = source.url;
    image.alt = model.title;
    image.width = 960;
    image.height = 720;
    image.loading = 'lazy';
    const content = element('div', undefined, 'card-content');
    content.append(element('h2', model.title));
    const meta = element('div', undefined, 'card-meta');
    meta.append(element('span', model.dimensions.map(value => value.toLocaleString('vi')).join(' × ') + ' mm'), element('span', model.status));
    content.append(meta);
    link.append(image, content);
    card.append(link);
    $('cards').append(card);
  }
  $('empty').hidden = visible.length > 0;
}

function renderControls(model, folder) {
  $('modelTitle').textContent = model.title;
  $('mode').replaceChildren(...model.animations.map(animation => new Option(animation.label, animation.id)));
  $('partControls').replaceChildren();
  for (const part of model.parts) {
    const label = element('label');
    const input = element('input');
    input.type = 'checkbox';
    input.checked = true;
    input.dataset.part = part.id;
    input.onchange = () => viewer.setVisible(part.id, input.checked);
    label.append(input, document.createTextNode(part.label));
    $('partControls').append(label);
  }
  $('viewControls').replaceChildren();
  for (const view of model.camera.views) {
    const button = element('button', view.label);
    button.onclick = () => viewer.setView(view.id);
    $('viewControls').append(button);
  }
  $('measurementControls').replaceChildren();
  for (const measurement of model.measurements) {
    const label = element('label');
    const input = element('input');
    input.type = 'checkbox';
    input.value = measurement.id;
    label.append(input, document.createTextNode(measurement.label));
    $('measurementControls').append(label);
  }
  $('measureMenu').hidden = model.measurements.length === 0;
  $('wireframe').checked = false;
  $('downloads').replaceChildren();
  for (const part of model.parts.filter(item => item.kind === 'print')) {
    for (const mesh of part.meshes.filter(mesh => mesh.src)) {
      const link = element('a', part.label);
      setDownload(link, folder + mesh.src, 'model/stl');
      $('downloads').append(link);
    }
  }
  setDownload($('bundleDownload'), folder + model.downloads.bundle, 'application/zip');
  $('bundleDownload').hidden = !!window.offlineAssets;
  setDownload($('stepDownload'), folder + model.downloads.step, 'application/step');
  $('projectDownload').hidden = !model.print;
  if (model.print) setDownload($('projectDownload'), folder + model.print.project, 'application/vnd.ms-package.3dmanufacturing-3dmodel+xml');
  $('printSummary').textContent = model.printInfo.summary;
  $('printSections').replaceChildren();
  for (const section of model.printInfo.sections) {
    const details = element('details');
    details.append(element('summary', section.title));
    if (section.rows.length) {
      const table = element('table'), body = element('tbody');
      for (const [name, value] of section.rows) {
        const row = element('tr'), heading = element('th', name);
        heading.scope = 'row';
        row.append(heading, element('td', value));
        body.append(row);
      }
      table.append(body);
      details.append(table);
    }
    for (const note of section.notes) details.append(element('small', note));
    if (section.links.length) {
      const links = element('small');
      section.links.forEach((source, index) => {
        if (index) links.append(' · ');
        const link = element('a', source.label);
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noopener';
        links.append(link);
      });
      details.append(links);
    }
    $('printSections').append(details);
  }
  renderPrintControls(model);
}

function setDownload(link, path, type) {
  const source = downloadURL(path, type);
  resources.push(source);
  link.href = source.url;
  link.download = path.split('/').at(-1);
}

function syncState(state) {
  $('play').setAttribute('aria-pressed', String(state.playing));
  $('play').setAttribute('aria-label', state.playing ? 'Tạm dừng' : 'Phát');
  $('play').title = state.playing ? 'Tạm dừng' : 'Phát';
  $('timeline').value = String(Math.round(state.time * 1000));
  $('mode').value = state.animation;
}

function renderPrintControls(model) {
  $('printMenu').hidden = !model.print;
  $('printPreview').checked = false;
  $('printTypes').replaceChildren();
  $('printLayerLabel').textContent = '';
  $('printStats').textContent = model.print ? model.printInfo.summary : '';
  $('printPlay').disabled = $('printLayer').disabled = true;
}

function showLayer(index) {
  preview.setLayer(index);
  $('printLayer').value = String(preview.layer + 1);
  $('printLayerLabel').textContent = `Lớp ${preview.layer + 1}/${preview.layerCount} · Z ${preview.zOf(preview.layer).toLocaleString('vi')} mm`;
}

function lockModelControls(locked) {
  $('play').disabled = locked || !viewer;
  for (const control of [$('timeline'), $('mode'), $('wireframe'), ...$('partControls').querySelectorAll('input')]) control.disabled = locked;
}

function stopPrintPlay() {
  clearInterval(printTimer);
  printTimer = null;
  $('printPlay').setAttribute('aria-pressed', 'false');
}

async function setPreview(on) {
  stopPrintPlay();
  if (!on) {
    viewer?.setPrintPreview(null);
    preview?.dispose();
    preview = null;
    lockModelControls(false);
    syncVisibility();
    $('printTypes').replaceChildren();
    $('printLayerLabel').textContent = '';
    $('printPlay').disabled = $('printLayer').disabled = true;
    return;
  }
  const entry = activeEntry;
  $('printPreview').disabled = true;
  try {
    const data = await readJSON(entry.folder + entry.model.print.layers);
    if (entry !== activeEntry || !$('printPreview').checked) return;
    preview = createPrintPreview(data);
    viewer.setPrintPreview(preview);
    lockModelControls(true);
    $('printLayer').max = String(preview.layerCount);
    $('printPlay').disabled = $('printLayer').disabled = false;
    for (const type of preview.types.filter(type => data.layers.some(layer => layer.paths[type.id]?.length))) {
      const label = element('label'), input = element('input'), swatch = element('span', undefined, 'swatch');
      input.type = 'checkbox';
      input.checked = true;
      input.onchange = () => preview.setTypeVisible(type.id, input.checked);
      swatch.style.background = type.color;
      label.append(input, swatch, document.createTextNode(type.label));
      $('printTypes').append(label);
    }
    showLayer(preview.layerCount - 1);
  } catch (error) {
    $('printPreview').checked = false;
    showError(error);
  } finally {
    $('printPreview').disabled = false;
  }
}

function syncVisibility() {
  for (const input of $('partControls').querySelectorAll('input')) input.checked = viewer.parts[input.dataset.part].visible;
}

function clearViewer() {
  loading?.abort();
  stopPrintPlay();
  preview?.dispose();
  preview = null;
  viewer?.dispose();
  viewer = null;
  lockModelControls(false);
  window.viewer = null;
  activeId = null;
  activeEntry = null;
  $('printDialog').close();
  document.body.dataset.ready = 'false';
  for (const resource of [...resources, ...thumbnails]) resource.dispose();
  thumbnails = [];
  resources = [];
}

async function route() {
  const id = location.hash.startsWith('#model/') ? location.hash.slice(7) : null;
  if (id && id === activeId) return;
  clearViewer();
  $('appError').hidden = true;
  const entry = catalog.find(item => item.model.id === id);
  $('workspace').hidden = !entry;
  $('gallery').hidden = !!entry;
  if (!entry) {
    document.title = 'Bàn in';
    renderGallery();
    if (id) showError(new Error('Không tìm thấy model: ' + id));
    document.body.dataset.ready = 'true';
    return;
  }
  activeId = id;
  activeEntry = entry;
  loading = new AbortController();
  const request = loading;
  $('loading').hidden = false;
  $('error').style.display = 'none';
  $('sidebarBody').inert = true;
  $('openPrint').disabled = true;
  $('play').disabled = true;
  document.title = entry.model.title + ' · Bàn in';
  renderControls(entry.model, entry.folder);
  $('canvas').replaceWith($('canvas').cloneNode());
  try {
    viewer = await createViewer({model: entry.model, folder: entry.folder, canvas: $('canvas'), stage: $('stage'), tooltip: $('partTip'), signal: request.signal, onState: syncState});
    window.viewer = viewer;
    $('play').disabled = false;
    $('openPrint').disabled = false;
    $('sidebarBody').inert = false;
    $('loading').hidden = true;
    document.body.dataset.ready = 'true';
  } catch (error) {
    if (request.signal.aborted) return;
    $('loading').hidden = true;
    $('error').style.display = 'block';
    $('error').textContent = 'Không tải được model. ' + error.message;
    window.viewerErrors.push(String(error));
  }
}

function showError(error) {
  $('appError').textContent = error.message;
  $('appError').hidden = false;
  window.viewerErrors.push(String(error));
}

const mobileLayout = matchMedia('(max-width:600px)');
const controlMenus = [...document.querySelectorAll('#sidebarBody > details')];
function syncControlLayout() {
  if (mobileLayout.matches) for (const menu of controlMenus) menu.open = false;
  else $('animationMenu').open = true;
}
for (const menu of controlMenus) menu.addEventListener('toggle', () => {
  if (mobileLayout.matches && menu.open) for (const other of controlMenus) if (other !== menu) other.open = false;
});
mobileLayout.addEventListener('change', syncControlLayout);
syncControlLayout();

$('play').onclick = () => viewer.togglePlay();
$('timeline').oninput = event => viewer.scrub(Number(event.target.value) / 1000);
$('mode').onchange = event => { viewer.setMode(event.target.value); syncVisibility(); };
$('wireframe').onchange = event => viewer.setWireframe(event.target.checked);
$('measurementControls').onchange = () => viewer.setMeasurements([...$('measurementControls').querySelectorAll('input:checked')].map(input => input.value));
$('reset').onclick = () => { if (preview) { $('printPreview').checked = false; setPreview(false); } viewer.reset(); syncVisibility(); $('wireframe').checked = false; for (const input of $('measurementControls').querySelectorAll('input')) input.checked = false; };
$('printPreview').onchange = event => setPreview(event.target.checked);
$('printLayer').oninput = event => { stopPrintPlay(); showLayer(Number(event.target.value) - 1); };
$('printPlay').onclick = () => {
  if (printTimer) return stopPrintPlay();
  if (preview.layer === preview.layerCount - 1) showLayer(0);
  $('printPlay').setAttribute('aria-pressed', 'true');
  printTimer = setInterval(() => {
    if (preview.layer === preview.layerCount - 1) return stopPrintPlay();
    showLayer(preview.layer + 1);
  }, 1000 / 15);
};
$('openPrint').onclick = () => { viewer.pause(); $('printDialog').showModal(); };
$('closePrint').onclick = () => $('printDialog').close();
$('printDialog').addEventListener('click', event => {
  if (event.target !== $('printDialog')) return;
  const rect = $('printDialog').getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) $('printDialog').close();
});
$('search').oninput = renderGallery;
window.addEventListener('hashchange', route);

try {
  if (location.protocol === 'file:' && !window.offlineAssets) throw new Error('Chạy python3 -m http.server trong thư mục này, rồi mở http://localhost:8000. Bản HTML offline nằm trong ZIP của từng model.');
  const paths = await readJSON('models.json');
  catalog = await Promise.all(paths.map(async path => ({model: await readJSON(path), folder: path.slice(0, path.lastIndexOf('/') + 1)})));
  await route();
} catch (error) { showError(error); }
