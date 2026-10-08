import re
from pathlib import Path
from unittest.mock import patch

from printkit.bundle import offline_html, version_assets
from printkit.catalog import load_catalog


def test_transitive_changes_update_import_map_and_entry_together(tmp_path: Path):
    (tmp_path / "viewer").mkdir()
    (tmp_path / "viewer/app.js").write_text("import './dependency.js';")
    dependency = tmp_path / "viewer/dependency.js"
    dependency.write_text("export const value = 1;")
    (tmp_path / "viewer/style.css").write_text("body {}")
    index = tmp_path / "index.html"
    index.write_text(
        '<link rel="stylesheet" href="viewer/style.css"><script type="module" src="viewer/app.js"></script>'
    )
    with (
        patch("printkit.bundle.ROOT", tmp_path),
        patch("printkit.bundle.MODULES", ["viewer/dependency.js", "viewer/app.js"]),
    ):
        version_assets()
        first = index.read_text()
        version_assets()
        assert first == index.read_text()
        dependency.write_text("export const value = 2;")
        version_assets()
    updated = index.read_text()
    assert first != updated
    versions = re.findall(r"\?v=([a-f0-9]+)", updated)
    assert len(versions) == 4 and len(set(versions)) == 1
    assert updated.count('type="importmap"') == 1


def test_offline_export_embeds_versioned_entry_and_styles():
    manifest, model = load_catalog()[0]
    html = offline_html(manifest, model)
    assert 'type="importmap"' not in html
    assert 'src="viewer/app.js' not in html
    assert 'href="viewer/style.css' not in html
    assert "window.offlineAssets=" in html
