import {$, element} from './dom.js';
import {downloadURL} from './resources.js';
import {createViewer} from './renderer.js';

let viewer = null, loading = null, resources = [];

function renderControls(model, folder) {
  $('modelTitle').textContent = model.title;
  $('printLink').hidden = !model.print;
  $('printLink').href = '#print/' + model.id;
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

function syncVisibility() {
  for (const input of $('partControls').querySelectorAll('input')) input.checked = viewer.parts[input.dataset.part].visible;
}

export async function showModel({model, folder}) {
  loading = new AbortController();
  const request = loading;
  $('workspace').hidden = false;
  $('loading').hidden = false;
  $('error').style.display = 'none';
  $('sidebarBody').inert = true;
  $('openPrint').disabled = true;
  $('play').disabled = true;
  document.title = model.title + ' · Bàn in';
  renderControls(model, folder);
  $('canvas').replaceWith($('canvas').cloneNode());
  try {
    viewer = await createViewer({model, folder, canvas: $('canvas'), stage: $('stage'), tooltip: $('partTip'), signal: request.signal, onState: syncState});
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

export function hideModel() {
  loading?.abort();
  loading = null;
  viewer?.dispose();
  viewer = null;
  window.viewer = null;
  $('printDialog').close();
  $('workspace').hidden = true;
  for (const resource of resources) resource.dispose();
  resources = [];
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
$('reset').onclick = () => { viewer.reset(); syncVisibility(); $('wireframe').checked = false; for (const input of $('measurementControls').querySelectorAll('input')) input.checked = false; };
$('openPrint').onclick = () => { viewer.pause(); $('printDialog').showModal(); };
$('closePrint').onclick = () => $('printDialog').close();
$('printDialog').addEventListener('click', event => {
  if (event.target !== $('printDialog')) return;
  const rect = $('printDialog').getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) $('printDialog').close();
});
