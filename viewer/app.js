import {$, element} from './dom.js';
import {readJSON, downloadURL} from './resources.js';
import {showModel, hideModel} from './model-screen.js';
import {showPrint, hidePrint} from './print-screen.js';

window.viewerErrors = [];
window.addEventListener('error', event => window.viewerErrors.push(event.message));
window.addEventListener('unhandledrejection', event => window.viewerErrors.push(String(event.reason)));
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
  $('appError').hidden = true;
  const entry = catalog.find(item => item.model.id === id);
  $('gallery').hidden = !!entry;
  if (!entry) {
    document.title = 'Bàn in';
    renderGallery();
    if (id) showError(new Error('Không tìm thấy model: ' + id));
    document.body.dataset.ready = 'true';
    return;
  }
  activeRoute = key;
  await screens[screen](entry);
}

function showError(error) {
  $('appError').textContent = error.message;
  $('appError').hidden = false;
  window.viewerErrors.push(String(error));
}

$('search').oninput = renderGallery;
window.addEventListener('hashchange', route);

try {
  if (location.protocol === 'file:' && !window.offlineAssets) throw new Error('Chạy python3 -m http.server trong thư mục này, rồi mở http://localhost:8000. Bản HTML offline nằm trong ZIP của từng model.');
  const paths = await readJSON('models.json');
  catalog = await Promise.all(paths.map(async path => ({model: await readJSON(path), folder: path.slice(0, path.lastIndexOf('/') + 1)})));
  await route();
} catch (error) { showError(error); }
