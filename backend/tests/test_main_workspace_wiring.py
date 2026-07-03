import importlib


def _collect_paths(routes: list) -> set[str]:
    """Recursively collect route paths handling both Route and IncludedRouter objects."""
    paths: set[str] = set()
    for route in routes:
        if hasattr(route, "path"):
            paths.add(route.path)
        if hasattr(route, "routes"):
            paths |= _collect_paths(route.routes)
    return paths


def test_app_main_imports_and_registers_workspace_routes():
    main = importlib.import_module("app.main")

    paths = _collect_paths(main.app.routes)

    assert "/api/workspace/projects" in paths
    assert "/api/workspace/projects/{slug}/approve" in paths
    assert "/api/workspace/projects/{slug}/reject" in paths
    assert "/api/workspace/projects/{slug}/report-bug" in paths
