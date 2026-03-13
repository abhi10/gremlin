"""Lightweight tests for dashboard data integrity."""

import json
from pathlib import Path


def test_catalog_exists():
    """Test that catalog.json exists."""
    catalog_path = Path("dashboard/data/catalog.json")
    assert catalog_path.exists(), "catalog.json is missing"


def test_catalog_valid_json():
    """Test that catalog.json is valid JSON."""
    catalog_path = Path("dashboard/data/catalog.json")
    with open(catalog_path) as f:
        data = json.load(f)
    assert "projects" in data
    assert isinstance(data["projects"], list)
    assert len(data["projects"]) > 0


def test_all_catalog_files_exist():
    """Test that all files listed in catalog exist."""
    catalog_path = Path("dashboard/data/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    for project in catalog["projects"]:
        file_path = Path("dashboard/data") / project["file"]
        assert file_path.exists(), f"Missing data file: {project['file']}"


def test_results_files_valid_json():
    """Test that all results files are valid JSON with required schema."""
    catalog_path = Path("dashboard/data/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    for project in catalog["projects"]:
        file_path = Path("dashboard/data") / project["file"]
        with open(file_path) as f:
            data = json.load(f)

        # Verify schema
        assert "target" in data, f"{project['file']}: missing 'target'"
        assert "areas" in data, f"{project['file']}: missing 'areas'"
        assert isinstance(data["areas"], list), f"{project['file']}: 'areas' not a list"

        # Verify each area has required structure
        for i, area in enumerate(data["areas"]):
            assert "area" in area, f"{project['file']}: area {i} missing 'area' field"
            assert "result" in area, f"{project['file']}: area {i} missing 'result'"
            assert "risks" in area["result"], f"{project['file']}: area {i} missing 'risks'"


def test_risks_have_required_fields():
    """Test that all risks have required fields for dashboard rendering."""
    catalog_path = Path("dashboard/data/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    required_fields = {"severity", "confidence", "scenario", "impact"}

    for project in catalog["projects"]:
        file_path = Path("dashboard/data") / project["file"]
        with open(file_path) as f:
            data = json.load(f)

        for area in data["areas"]:
            for risk_idx, risk in enumerate(area["result"]["risks"]):
                missing = required_fields - set(risk.keys())
                assert not missing, (
                    f"{project['file']}, area '{area['area']}', "
                    f"risk {risk_idx}: missing fields {missing}"
                )

                # Verify severity is valid
                assert risk["severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}, (
                    f"{project['file']}: invalid severity '{risk['severity']}'"
                )


def test_no_duplicate_project_ids():
    """Test that catalog has no duplicate project IDs."""
    catalog_path = Path("dashboard/data/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    ids = [p["id"] for p in catalog["projects"]]
    assert len(ids) == len(set(ids)), f"Duplicate project IDs: {ids}"


def test_no_duplicate_filenames():
    """Test that catalog has no duplicate filenames."""
    catalog_path = Path("dashboard/data/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    files = [p["file"] for p in catalog["projects"]]
    assert len(files) == len(set(files)), f"Duplicate filenames: {files}"


# ── URL query param & landing page tests ─────────────────────────


def test_catalog_projects_have_id_for_url_param():
    """Test that every catalog project has an 'id' field for ?project= deep linking."""
    catalog_path = Path("dashboard/data/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    for project in catalog["projects"]:
        assert "id" in project, f"Project missing 'id': {project}"
        assert isinstance(project["id"], str) and project["id"].strip(), (
            f"Project 'id' must be a non-empty string: {project}"
        )


def test_project_param_resolves_to_valid_file():
    """Test that each catalog project id maps to an existing data file."""
    catalog_path = Path("dashboard/data/catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    for project in catalog["projects"]:
        file_path = Path("dashboard/data") / project["file"]
        assert file_path.exists(), (
            f"?project={project['id']} would resolve to {project['file']} but file is missing"
        )


def test_dashboard_html_reads_project_query_param():
    """Smoke test that dashboard JS contains ?project= param handling."""
    html_path = Path("dashboard/index.html")
    html = html_path.read_text()
    assert "params.get('project')" in html, (
        "Dashboard JS must read the 'project' query parameter"
    )


def test_dashboard_html_renders_landing_page():
    """Smoke test that dashboard HTML/JS contains landing page rendering logic."""
    html_path = Path("dashboard/index.html")
    html = html_path.read_text()
    assert "renderLanding" in html, "Dashboard must have renderLanding function"
    assert "landing-title" in html, "Dashboard must have landing-title CSS class"
    assert "landing-description" in html, "Dashboard must have landing-description CSS class"


def test_dashboard_html_syncs_url_on_change():
    """Smoke test that dropdown change updates the browser URL."""
    html_path = Path("dashboard/index.html")
    html = html_path.read_text()
    assert "history.replaceState" in html, (
        "Dashboard must use history.replaceState to sync URL on project change"
    )
