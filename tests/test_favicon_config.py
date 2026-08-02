from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_backend_prefers_svg_favicon_lookup():
    app_py = (REPO_ROOT / "apps" / "web" / "app.py").read_text(encoding="utf-8")
    assert 'icon_path = _find_frontend_file("favicon.svg") or _find_frontend_file("favicon.ico")' in app_py


def test_fallback_ui_references_svg_favicon():
    index_html = (REPO_ROOT / "apps" / "web" / "static" / "index.html").read_text(encoding="utf-8")
    assert '<link rel="icon" type="image/svg+xml" href="/favicon.svg" />' in index_html
