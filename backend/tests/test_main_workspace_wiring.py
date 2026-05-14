import importlib


def test_app_main_imports_and_registers_workspace_routes():
    main = importlib.import_module("app.main")

    paths = {route.path for route in main.app.routes}

    assert "/api/workspace/projects" in paths
    assert "/api/workspace/projects/{slug}/approve" in paths
    assert "/api/workspace/projects/{slug}/reject" in paths
    assert "/api/workspace/projects/{slug}/report-bug" in paths
