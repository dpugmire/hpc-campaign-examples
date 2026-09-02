"""Integration tests for the schema embedded by the MHD ingest script."""

from pathlib import Path

import h5py
from hpc_campaign import Manager

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "mhd_orszag_tang.yaml"


def _make_placeholder_dataset(path: Path) -> None:
    """Create a real payload while keeping schema validation metadata-only."""
    with h5py.File(path, "w") as handle:
        handle.create_dataset("pressure", data=[1.0])


def test_schema_applies_to_two_runs_and_allows_derived_products(tmp_path: Path) -> None:
    """Each run must contain output.bp; other registered products are allowed."""
    payload = tmp_path / "payload.h5"
    _make_placeholder_dataset(payload)

    manager = Manager(archive="mhd.aca", campaign_store=str(tmp_path))
    manager.open(create=True, truncate=True)
    try:
        manager.set_schema(SCHEMA_PATH)
        for name in (
            "run-001/output.bp",
            "run-001/analysis.bp",
            "run-001/output_stats.bp",
            "run-002/output.bp",
        ):
            manager.data(payload, name=name)

        layout = manager.validate_schema()
    finally:
        manager.close()

    assert sorted(layout["instances"]) == ["run-001", "run-002"]
    assert layout["instances"]["run-001"]["file_groups"]["output"]["datasets"] == [
        "run-001/output.bp"
    ]
    assert layout["instances"]["run-002"]["file_groups"]["output"]["datasets"] == [
        "run-002/output.bp"
    ]
