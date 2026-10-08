function embedded(path) {
  return window.offlineAssets?.[path];
}

export async function readBuffer(path) {
  const data = embedded(path);
  if (data !== undefined) return Uint8Array.from(atob(data), char => char.charCodeAt(0)).buffer;
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.arrayBuffer();
}

export async function readJSON(path) {
  return JSON.parse(new TextDecoder().decode(await readBuffer(path)));
}

export function downloadURL(path, type) {
  const data = embedded(path);
  if (data === undefined) return {url: path, dispose() {}};
  const bytes = Uint8Array.from(atob(data), char => char.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], {type}));
  return {url, dispose() { URL.revokeObjectURL(url); }};
}
