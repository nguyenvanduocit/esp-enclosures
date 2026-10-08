---
name: meshy-extract
description: Extract a 3D model (GLB + textures) from a Meshy.ai community model page without a PRO subscription
---

# meshy-extract

Extracts GLB + PBR textures from a Meshy.ai community model URL by replicating the browser's own decryption pipeline locally.

## How it works

Meshy serves models in a proprietary `.meshy` format (MESHY.AI header + AES-like encrypted body). The browser decrypts them using an Emscripten WASM module that the page loads. The WASM validates a domain signature before decrypting. We replicate that signature locally.

**Key artifacts:**
- `mesh_loader.wasm` / `mesh_loader.js` — Emscripten decryptor at `/resource/decrypt/`
- `lazy_1lab8ldkja3hh.js` — Turbopack lazy chunk with the FNV-1a signature function and decrypt pipeline
- Signature key: `"Meshy_Crypto_Key"` — hard-coded in the JS

## Step-by-step

### 1. Get the model metadata

Use ego-browser to open the Meshy model page. The model metadata (CDN URL for the `.meshy` file, signed texture URLs) is embedded in `__NEXT_DATA__`:

```js
const task = await taskSpace("meshy extract");
const page = task.page("p1");
await page.goto("https://www.meshy.ai/3d-models/<MODEL_ID>?page=landing");
await page.waitForLoadState('networkidle');
const nextData = await page.evaluate(() => JSON.parse(document.getElementById('__NEXT_DATA__').textContent));
const model = nextData.props.pageProps.model3d;
// model.objectUrl → signed CDN URL for the .meshy file
// model.thumbnailUrl → preview image
```

If `objectUrl` 403s, look in the page HTML for `"objectUrl":"` or intercept network requests.

### 2. Download the .meshy file and decoder

```bash
WORK=/tmp/meshy-probe
mkdir -p $WORK
# Download .meshy file (use full signed URL with Signature= and Key-Pair-Id= params)
curl -L "SIGNED_URL" -o $WORK/model.meshy
# Download WASM decoder
curl -L "https://www.meshy.ai/resource/decrypt/mesh_loader.js" -o $WORK/mesh_loader.js
curl -L "https://www.meshy.ai/resource/decrypt/mesh_loader.wasm" -o $WORK/mesh_loader.wasm
```

### 3. Get the Turbopack lazy chunk with the signature function

The decrypt pipeline lives in a lazy chunk. Find it by downloading all chunks and grepping:

```bash
# Get the list of lazy chunk names from the page source
curl -s "https://www.meshy.ai/3d-models/<MODEL_ID>?page=landing" | grep -o '"lazy_[^"]*\.js"' | sort -u

# Then download each and grep for MESHY.AI or authorize(
for chunk in lazy_1lab8ldkja3hh.js lazy_1okj8_b6pllv-.js; do
  curl -s "https://www.meshy.ai/_next/static/chunks/$chunk" -o $WORK/$chunk
done
grep -l "MESHY.AI\|processMeshyFile" $WORK/lazy_*.js
```

### 4. Extract the signature function

From the lazy chunk, the signature uses FNV-1a with key `"Meshy_Crypto_Key"`:

```js
function computeSignature(hostname, timestamp) {
  const data = hostname + ":" + timestamp;
  const key = "Meshy_Crypto_Key";
  let r = BigInt("14695981039346656037");
  const n = BigInt("1099511628211");
  const a = BigInt("0xFFFFFFFFFFFFFFFF");
  for (let i = 0; i < key.length; i++) { r ^= BigInt(key.charCodeAt(i)); r = r * n & a; }
  for (let i = 0; i < data.length; i++) { r ^= BigInt(data.charCodeAt(i)); r = r * n & a; }
  r ^= r >> BigInt(33); r = r * BigInt("0xff51afd7ed558ccd") & a;
  r ^= r >> BigInt(33); r = r * BigInt("0xc4ceb9fe1a85ec53") & a;
  r ^= r >> BigInt(33);
  return r.toString(16).padStart(16, "0");
}
```

### 5. Decrypt with the WASM

```js
// decrypt.mjs — run with: node /path/to/decrypt.mjs
import Module from '/tmp/meshy-probe/mesh_loader.js';
import { readFileSync, writeFileSync } from 'node:fs';

const m = await Module({ locateFile: () => '/tmp/meshy-probe/mesh_loader.wasm' });

// Authorize
const hostname = 'www.meshy.ai';
const timestamp = Math.floor(Date.now() / 1000);
const sig = computeSignature(hostname, timestamp); // use function above
const authResult = m.authorize(hostname, timestamp, sig);
console.log('auth:', authResult); // should be { success: true }

// Decrypt
const meshyBytes = new Uint8Array(readFileSync('/tmp/meshy-probe/model.meshy').buffer);
const result = m.processMeshyFile(meshyBytes);
if (!result.success) throw new Error(result.error);

// result.data is a Uint8Array of the GLB
writeFileSync('/tmp/meshy-probe/shrine.glb', result.data);
console.log('GLB written:', result.data.byteLength, 'bytes');
// Verify header
const buf = readFileSync('/tmp/meshy-probe/shrine.glb');
console.log('magic:', buf.slice(0, 4).toString('ascii')); // should print "glTF"
```

### 6. Download textures

Texture URLs are in the model metadata or the page HTML. They are signed CloudFront URLs that expire. Look for `"baseColorTextureUrl"`, `"normalTextureUrl"`, `"metallicRoughnessTextureUrl"` fields, or capture them from network requests via ego-browser.

```bash
curl -L "SIGNED_TEXTURE_URL" -o /tmp/meshy-probe/texture_base.png
curl -L "SIGNED_NORMAL_URL"   -o /tmp/meshy-probe/texture_normal.png
# etc.
```

### 7. Add to viewer

```bash
mkdir -p models/<name>
cp /tmp/meshy-probe/shrine.glb models/<name>/<name>.glb
```

Create `models/<name>/model.json`:
```json
{
  "schemaVersion": 1,
  "id": "<name>",
  "type": "glb",
  "src": "<name>.glb",
  "units": "m",
  "category": "Mô hình 3D",
  "status": "Tham khảo",
  "thumbnail": "thumbnail.png",
  "title": "<Title>",
  "description": "<description>",
  "dimensions": [1000, 1000, 1000],
  "camera": { "position": [2.5, -3.5, 2.0], "target": [0, 0, 0], "minDistance": 0.5, "maxDistance": 15 },
  "grid": { "size": 4, "divisions": 8 },
  "parts": [], "animations": [], "measurements": [],
  "downloads": { "bundle": null, "step": null },
  "printInfo": { "summary": "", "sections": [] }
}
```

Add `"models/<name>/model.json"` to `models.json`.

## Notes

- The WASM `authorize()` uses wall-clock time; run decrypt quickly after calling it (or re-authorize before each batch).
- GLB uses GLTF Y-up; viewer is Z-up. The renderer rotates `gltf.scene.rotation.x = Math.PI / 2` automatically for `type: "glb"` models.
- Textures in the GLB are already embedded as WebP (`EXT_texture_webp`). The separate texture downloads are only needed if you want to edit them.
- `KHR_mesh_quantization` is handled by Three.js GLTFLoader r169+.
