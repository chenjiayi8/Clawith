import importlib


def _collect_paths(routes: list) -> set[str]:
    """Recursively collect route paths handling Route, Mount, and IncludedRouter objects."""
    paths: set[str] = set()
    for route in routes:
        if hasattr(route, "path"):
            paths.add(route.path)
        # Starlette 1.x wraps included routers as _IncludedRouter with .original_router
        if hasattr(route, "original_router") and hasattr(route.original_router, "routes"):
            paths |= _collect_paths(route.original_router.routes)
        # Older Starlette/FastAPI may nest routes directly
        if hasattr(route, "routes") and not hasattr(route, "original_router"):
            paths |= _collect_paths(route.routes)
    return paths


def test_app_main_imports_and_registers_workspace_routes():
    main = importlib.import_module("app.main")

    paths = _collect_paths(main.app.routes)

    # Workspace routes may appear with or without the API prefix depending on
    # the FastAPI/Starlette version and how include_router flattens routes.
    assert any(
        p.endswith("/workspace/projects") or p.endswith("/workspace/projects/")
        for p in paths
    ), f"workspace projects route not found in: {sorted(p for p in paths if 'workspace' in p.lower())}"
    assert any(
        "/workspace/projects/" in p and "/approve" in p
        for p in paths
    ), "workspace projects approve route not found"
    assert any(
        "/workspace/projects/" in p and "/reject" in p
        for p in paths
    ), "workspace projects reject route not found"
    assert any(
        "/workspace/projects/" in p and "/report-bug" in p
        for p in paths
    ), "workspace projects report-bug route not found"
