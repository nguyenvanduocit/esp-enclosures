function embedded(path) {
  return window.offlineAssets?.[path];
}

// onProgress(loaded, total) fires per chunk; total is 0 when the size is unknown.
// A Content-Encoding makes Content-Length count compressed bytes while chunks arrive decompressed, so it is not trusted.
export async function readBuffer(path, onProgress) {
  const data = embedded(path);
  if (data !== undefined) return Uint8Array.from(atob(data), char => char.charCodeAt(0)).buffer;
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  if (!onProgress || !response.body) return response.arrayBuffer();
  const total = response.headers.get('content-encoding') ? 0 : Number(response.headers.get('content-length')) || 0;
  const reader = response.body.getReader();
  const chunks = [];
  let loaded = 0;
  onProgress(loaded, total);
  for (let chunk = await reader.read(); !chunk.done; chunk = await reader.read()) {
    chunks.push(chunk.value);
    loaded += chunk.value.length;
    onProgress(loaded, total);
  }
  return new Blob(chunks).arrayBuffer();
}

export async function readJSON(path, onProgress) {
  return JSON.parse(new TextDecoder().decode(await readBuffer(path, onProgress)));
}

export function downloadURL(path, type) {
  const data = embedded(path);
  if (data === undefined) return {url: path, dispose() {}};
  const bytes = Uint8Array.from(atob(data), char => char.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], {type}));
  return {url, dispose() { URL.revokeObjectURL(url); }};
}
