"""Version the shared viewer assets and package each model as an offline ZIP."""

import base64
import hashlib
import json
import re
import zipfile

from printkit.catalog import ROOT, load_catalog, local_file

MODULES = [
    "viewer/vendor/three.module.min.js",
    "viewer/vendor/OrbitControls.js",
    "viewer/resources.js",
    "viewer/model-core.js",
    "viewer/part-drag.js",
    "viewer/dimensions.js",
    "viewer/renderer.js",
    "viewer/app.js",
]


def offline_html(manifest, model):
    folder = manifest.parent
    assets = {}
    paths = [
        manifest,
        local_file(folder, model["thumbnail"]),
        local_file(folder, model["downloads"]["step"]),
    ]
    paths += [
        local_file(folder, mesh["src"])
        for part in model["parts"]
        for mesh in part["meshes"]
        if "src" in mesh
    ]
    for path in paths:
        assets[path.relative_to(ROOT).as_posix()] = base64.b64encode(
            path.read_bytes()
        ).decode()
    assets["models.json"] = base64.b64encode(
        json.dumps([manifest.relative_to(ROOT).as_posix()]).encode()
    ).decode()
    modules = [[name, (ROOT / name).read_text()] for name in MODULES]
    # Each dependency appears before its importers; the module code is unchanged.
    boot = "window.offlineAssets=" + json.dumps(assets, separators=(",", ":")) + ";\n"
    boot += "const modules=" + json.dumps(modules, separators=(",", ":")) + ";\n"
    boot += """const urls = new Map();
for (const [path, source] of modules) {
  const code = source.replace(/from (['"])(\\.[^'"]+)\\1/g, (_, quote, specifier) => {
    const dependency = new URL(specifier, 'https://offline/' + path).pathname.slice(1);
    if (!urls.has(dependency)) throw new Error('Missing module: ' + dependency);
    return 'from ' + quote + urls.get(dependency) + quote;
  });
  urls.set(path, URL.createObjectURL(new Blob([code], {type:'text/javascript'})));
}
"""
    boot += f"if (!location.hash) location.hash = '#model/{model['id']}';\n"
    boot += "await import(urls.get('viewer/app.js'));\n"
    boot += "for (const url of urls.values()) URL.revokeObjectURL(url);\n"
    html = (ROOT / "index.html").read_text()
    html = re.sub(
        r'<link rel="stylesheet" href="viewer/style.css(?:\?[^"]*)?">',
        lambda _: "<style>" + (ROOT / "viewer/style.css").read_text() + "</style>",
        html,
    )
    html = re.sub(r'<script type="importmap">.*?</script>', "", html, flags=re.S)
    return re.sub(
        r'<script type="module" src="viewer/app.js(?:\?[^"]*)?"></script>',
        lambda _: '<script type="module">' + boot.replace("</", "<\\/") + "</script>",
        html,
    )


def version_assets():
    digest = hashlib.sha256()
    for path in MODULES + ["viewer/style.css"]:
        digest.update((ROOT / path).read_bytes())
    version = digest.hexdigest()[:12]
    html = (ROOT / "index.html").read_text()
    html = re.sub(r'<script type="importmap">.*?</script>\n?', "", html, flags=re.S)
    imports = {"./" + path: "./" + path + "?v=" + version for path in MODULES}
    importmap = (
        '<script type="importmap">'
        + json.dumps({"imports": imports}, separators=(",", ":"))
        + "</script>\n"
    )
    html = re.sub(
        r'(<script type="module" src="viewer/app.js)(?:\?[^"]*)?("></script>)',
        lambda m: importmap + m[1] + "?v=" + version + m[2],
        html,
    )
    html = re.sub(
        r'(href="viewer/style.css)(?:\?[^"]*)?(")',
        lambda m: m[1] + "?v=" + version + m[2],
        html,
    )
    (ROOT / "index.html").write_text(html)


def build_all():
    models = load_catalog()
    version_assets()
    for manifest, model in models:
        folder = manifest.parent
        target = folder / model["downloads"]["bundle"]
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("index.html", offline_html(manifest, model))
            archive.write(ROOT / "model.schema.json", "model.schema.json")
            archive.write(ROOT / "viewer/vendor/LICENSE", "THREE-LICENSE.txt")
            for path in sorted(folder.rglob("*")):
                if (
                    not path.is_file()
                    or path.suffix in (".zip", ".pyc")
                    or "__pycache__" in path.parts
                    or path.name == ".DS_Store"
                ):
                    continue
                archive.write(path, path.relative_to(ROOT).as_posix())
        print(f"{model['id']}: validated, packaged {target.stat().st_size:,} bytes")
