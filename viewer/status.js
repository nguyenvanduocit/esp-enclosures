import {element} from './dom.js';

const ICONS = {
  error: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.5"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5v.5"/>',
};

function icon(kind) {
  const holder = element('span', undefined, 'status-icon');
  holder.innerHTML = `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${ICONS[kind]}</svg>`;
  return holder;
}

// One loading / error / info presentation for every screen; the host decides where it sits.
export function createStatus(host) {
  let track = null, bar = null, percent = null;
  host.setAttribute('role', 'status');

  function show(kind, ...children) {
    host.dataset.kind = kind;
    host.replaceChildren(element('div', undefined, 'status-box'));
    host.firstChild.append(...children);
    host.hidden = false;
  }

  function notice(kind, message, {detail, retry, home} = {}) {
    track = bar = percent = null;
    const actions = element('div', undefined, 'status-actions');
    if (retry) {
      const button = element('button', 'Thử lại');
      button.onclick = retry;
      actions.append(button);
    }
    if (home) {
      const link = element('a', 'Về danh sách', 'screen-link');
      link.href = '#';
      actions.append(link);
    }
    show(kind, icon(kind), element('p', message, 'status-text'),
      ...(detail ? [element('code', detail, 'status-detail')] : []),
      ...(actions.hasChildNodes() ? [actions] : []));
  }

  // fraction is 0..1, or null while the total size is unknown.
  function progress(fraction) {
    if (!track) return;
    track.toggleAttribute('data-indeterminate', fraction === null);
    bar.style.transform = fraction === null ? '' : `scaleX(${fraction})`;
    percent.textContent = fraction === null ? '' : Math.round(fraction * 100) + '%';
  }

  return {
    loading(label) {
      track = element('div', undefined, 'status-bar');
      bar = element('i');
      track.append(bar);
      percent = element('span', undefined, 'status-percent');
      percent.setAttribute('aria-hidden', 'true');
      show('loading', element('span', undefined, 'status-spinner'), element('p', label, 'status-text'), track, percent);
      progress(null);
    },
    progress,
    error: (message, options) => notice('error', message, options),
    info: (message, options) => notice('info', message, options),
    clear() {
      track = bar = percent = null;
      host.replaceChildren();
      host.hidden = true;
    },
  };
}
