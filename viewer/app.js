import {$, element} from './dom.js';
import {readJSON, downloadURL} from './resources.js';
import {showModel, hideModel} from './model-screen.js';
import {showPrint, hidePrint} from './print-screen.js';
import {createStatus} from './status.js';

window.viewerErrors = [];
window.addEventListener('error', event => window.viewerErrors.push(event.message));
window.addEventListener('unhandledrejection', event => window.viewerErrors.push(String(event.reason)));
const appStatus = createStatus($('appStatus'));
const normalize = text => text.toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
const screens = {model: showModel, print: showPrint};
let catalog = [], activeRoute = null, thumbnails = [];

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
    image.alt = model.title;
    image.width = 960;
    image.height = 720;
    image.loading = 'lazy';
    image.onload = image.onerror = () => image.classList.add('settled');
    image.src = source.url;
    const content = element('div', undefined, 'card-content');
    content.append(element('h2', model.title));
    const meta = element('div', undefined, 'card-meta');
    meta.append(element('span', model.dimensions.map(value => value.toLocaleString('vi')).join(' × ') + ' mm'), element('span', model.status));
    content.append(meta);
    link.append(image, content);
    card.append(link);
    $('cards').append(card);
  }
  $('cards').removeAttribute('aria-busy');
  $('empty').hidden = visible.length > 0;
}

function clearScreens() {
  hideModel();
  hidePrint();
  document.body.dataset.ready = 'false';
  for (const resource of thumbnails) resource.dispose();
  thumbnails = [];
}

async function route() {
  const [, screen, id] = /^#(model|print)\/(.+)$/.exec(location.hash) ?? [];
  const key = screen && `${screen}/${id}`;
  if (key && key === activeRoute) return;
  clearScreens();
  activeRoute = null;
  appStatus.clear();
  const entry = catalog.find(item => item.model.id === id);
  $('gallery').hidden = !!entry || !!id;
  if (!entry) {
    document.title = 'Bàn in';
    renderGallery();
    if (id) {
      appStatus.error('Không tìm thấy model.', {detail: id, home: true});
      window.viewerErrors.push('Không tìm thấy model: ' + id);
    }
    document.body.dataset.ready = 'true';
    return;
  }
  activeRoute = key;
  await screens[screen](entry, retry);
}

function retry() {
  activeRoute = null;
  return route();
}

function fail(message, options) {
  $('gallery').hidden = true;
  appStatus.error(message, options);
  window.viewerErrors.push(message + ' ' + (options.detail ?? ''));
}

async function loadCatalog() {
  const paths = await readJSON('models.json');
  catalog = await Promise.all(paths.map(async path => ({model: await readJSON(path), folder: path.slice(0, path.lastIndexOf('/') + 1)})));
}

async function start() {
  appStatus.clear();
  if (location.protocol === 'file:' && !window.offlineAssets) {
    return fail('Chạy máy chủ web trong thư mục này rồi mở http://localhost:8000. Bản HTML offline nằm trong ZIP của từng model.', {detail: 'python3 -m http.server'});
  }
  const deepLink = /^#(model|print)\//.test(location.hash);
  $('gallery').hidden = deepLink;
  if (deepLink) appStatus.loading('Đang tải…');
  try {
    if (!catalog.length) await loadCatalog();
  } catch (error) {
    return fail('Không tải được danh sách model.', {detail: error.message, retry: start});
  }
  window.addEventListener('hashchange', route);
  await route();
}

$('search').oninput = renderGallery;
await start();
