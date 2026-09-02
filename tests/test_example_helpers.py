"""Focused unit tests for transformations used by the example scripts."""

import numpy as np

from scripts.adios_derived_variables import computeDerivedFields, resolveVarName
from scripts.adios_stats import computeStats
from scripts.render_adios_visualizations_to_campaign import resolve_var_name, visualization_semantic_kwargs


def test_prefixed_adios_variable_name_resolves_to_scientific_name() -> None:
    """Code-specific prefixes must not hide the underlying variable meaning."""
    assert resolveVarName({"hll_pressure", "rho"}, "pressure") == "hll_pressure"
    assert resolveVarName({"hll_pressure", "pressure"}, "pressure") == "pressure"
    assert resolve_var_name({"hll_pressure", "rho"}, "pressure") == "hll_pressure"


def test_divergence_uses_both_magnetic_field_components() -> None:
    """The derived div_b field is computed from bx and by together."""
    y, x = np.mgrid[0:3, 0:4]
    derived = computeDerivedFields({"bx": x.astype(float), "by": y.astype(float)})

    np.testing.assert_allclose(derived["div_b"], 2.0)


def test_statistics_are_computed_over_the_complete_array() -> None:
    """Statistics written to the campaign summarize every array element."""
    stats = computeStats(np.asarray([[1.0, 2.0], [3.0, 4.0]]))

    assert stats["min"] == 1.0
    assert stats["max"] == 4.0
    assert stats["mean"] == 2.5
    assert stats["median"] == 2.5


def test_streamline_metadata_records_physical_components_and_background() -> None:
    """Visualization metadata should name every prefixed field used to render."""
    semantic = visualization_semantic_kwargs(
        "velocity_streamlines",
        "streamlines",
        {"run_vx", "run_vy", "run_speed"},
    )

    assert semantic == {
        "streamline_by": ("run_vx", "run_vy"),
        "color_by": "run_speed",
    }
