import dashboard


def test_day77_dashboard_exposes_repeated_evaluation_module():
    repeated = dashboard.MODULES.get("repeated", {})

    assert callable(repeated.get("run_repeated_experiments"))
    assert callable(repeated.get("build_seed_summary"))
    assert callable(repeated.get("build_summary_table"))
    assert callable(repeated.get("calculate_consistency"))


def test_day77_dashboard_repeated_evaluation_uses_real_scenarios():
    scenarios = list(dashboard.scenario_catalogue)

    assert scenarios
    assert all(isinstance(scenario, dict) for scenario in scenarios)
    assert all(scenario.get("actions") for scenario in scenarios)
    assert all(scenario.get("resources") for scenario in scenarios)


def test_day77_dashboard_repeated_evaluation_api_round_trip():
    repeated = dashboard.MODULES["repeated"]

    results = repeated["run_repeated_experiments"](
        scenarios=list(dashboard.scenario_catalogue),
        seeds=[42, 101],
        events_per_scenario=2,
        threshold=70.0,
    )

    assert len(results) == 2

    seed_summary = repeated["build_seed_summary"](results)
    summary_table = repeated["build_summary_table"](results)
    consistency = repeated["calculate_consistency"](
        results,
        metric="f1_score",
    )

    assert not seed_summary.empty
    assert not summary_table.empty
    assert consistency["experiments"] == 2


def test_day77_dashboard_research_results_preserve_core_metrics():
    repeated = dashboard.MODULES["repeated"]

    results = repeated["run_repeated_experiments"](
        scenarios=list(dashboard.scenario_catalogue),
        seeds=[42],
        events_per_scenario=2,
        threshold=70.0,
    )

    result = results[0]

    assert "baseline" in result
    assert "aegisguard" in result

    for detector in ("baseline", "aegisguard"):
        assert "accuracy" in result[detector]
        assert "f1_score" in result[detector]
        assert "recall" in result[detector]
