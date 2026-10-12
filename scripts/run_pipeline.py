"""Pulls -> build -> model -> evaluation -> signals. Writes data/processed/ and reports/.

Runs two dealer-activity views: CBP new-car dealer employment (primary) and DOR new-car-dealer
real taxable sales (secondary).

Usage (from the repo root):
    python3 scripts/run_pipeline.py            # uses cached raw pulls in data/raw/ if present
    python3 scripts/run_pipeline.py --refresh  # re-pull WA DOR, DOL, BLS and Census CBP
"""

import argparse
import datetime as dt

from wa_tire import build, config, evaluate, model, pull_cbp, pull_cpi, pull_demand, pull_wa, signals


def md_table(df, floatfmt=".3f"):
    return df.to_markdown(index=False, floatfmt=floatfmt)


def run_view(view, cy, included, growth_end):
    """Model, evaluation and signals for one dealer-activity measure."""
    col = config.DEALER_VIEWS[view]["col"]
    df, dropped = model.model_frame(cy, included, col)
    last = int(df["year"].max())
    fit, test_pred = model.run_split(df)
    res = signals.residual_stats(test_pred, config.RECENT_YEARS_N, config.RESIDUAL_Z_MIN)
    # Growth gap uses tire vs vehicle growth over the full period, for the counties in this view.
    gap = signals.growth_gap(cy[cy["county"].isin(df["county"].unique())], config.GROWTH_BASE_YEAR, growth_end)
    missing = sorted(gap.loc[gap["growth_data_missing"], "county"])  # reported, not imputed
    gap = gap[~gap["growth_data_missing"]]
    ranked = signals.rank_and_flag(res, gap, config.TOP_SHARE)
    return {
        "dropped": dropped, "missing_growth": missing, "last_year": last, "n_counties": df["county"].nunique(),
        f"test_predictions_{view}": test_pred,
        f"evaluation_{view}": evaluate.evaluation_table(test_pred),
        f"evaluation_by_year_{view}": evaluate.evaluation_by_year(test_pred),
        f"coefficients_{view}": model.coefficient_table(fit).reset_index(names="term"),
        f"signals_{view}": ranked,
    }


def main(refresh):
    config.PROCESSED.mkdir(parents=True, exist_ok=True)
    config.REPORTS.mkdir(parents=True, exist_ok=True)
    this_year = dt.date.today().year

    print("1/4 pulls")
    raw, locs = pull_wa.pull_sales(refresh=refresh)
    vehicles = pull_demand.pull_registrations(refresh=refresh)
    cbp = pull_cbp.pull_cbp(config.MODEL_FIRST_YEAR, this_year, refresh=refresh)
    cpi = pull_cpi.pull_cpi(int(config.FIRST_QUARTER[:4]), this_year, refresh=refresh)
    deflators = pull_cpi.quarterly_deflators(cpi)

    print("2/4 build")
    quarters = sorted(raw["quarter"].unique())
    cq = build.deflate(build.county_quarter(raw, locs, quarters), deflators)
    cy = build.county_year(cq, vehicles, cbp)
    excl = build.exclusions(cq, cy)
    included = sorted(excl.loc[~excl["excluded"], "county"])

    print("3/4 model, evaluation and signals per dealer view")
    growth_end = int(cy.loc[cy["vehicles"].notna(), "year"].max())
    views = {v: run_view(v, cy, included, growth_end) for v in config.DEALER_VIEWS}
    comparison = signals.compare_views({v: views[v][f"signals_{v}"] for v in views})
    primary = next(iter(config.DEALER_VIEWS))
    flagged = signals.flagged_counties(comparison, list(config.DEALER_VIEWS))
    breakdown = build.city_breakdown(raw, deflators, flagged, config.GROWTH_BASE_YEAR, growth_end)
    concentration = build.growth_concentration(breakdown)
    tiers = signals.tier_table(comparison, views[primary][f"signals_{primary}"],
                               {v: d["short"] for v, d in config.DEALER_VIEWS.items()},
                               concentration, config.CONCENTRATION_MAX_SHARE)
    tiers = tiers.merge(concentration, on="county", how="left")
    view_summary = build.pd.DataFrame([
        {"view": v, "measure": config.DEALER_VIEWS[v]["label"], "model_years": f"{config.MODEL_FIRST_YEAR}-{r['last_year']}",
         "test_years": f"{config.TEST_FIRST_YEAR}-{r['last_year']}", "counties": r["n_counties"],
         "dropped_no_dealer_data": ", ".join(r["dropped"]),
         f"missing_growth_data_{config.GROWTH_BASE_YEAR}_{growth_end}": ", ".join(r["missing_growth"]) or "none",
         "top_candidates": ", ".join(r[f"signals_{v}"].query("top_candidate")["county"])}
        for v, r in views.items()
    ])

    print("4/4 write outputs")
    outputs = {
        "county_quarter": cq, "county_year": cy, "exclusions": excl,
        "coverage": build.coverage_table(cq, cy, excl),
        "naics_transition_check": build.naics_transition_check(cq),
        "qoq_outliers": build.qoq_outliers(cq, included), "cpi_quarterly": deflators,
        "view_summary": view_summary, "candidates_by_view": comparison, "candidate_tiers": tiers,
        "city_breakdown": breakdown,
    }
    for r in views.values():
        outputs.update({k: v for k, v in r.items() if k not in ("dropped", "missing_growth", "last_year", "n_counties")})
    for name, frame in outputs.items():
        frame.to_csv(config.PROCESSED / f"{name}.csv", index=False)
    locs.to_csv(config.REPORTS / "location_codes.csv", index=False)

    show = ["county", "test_years_above", "test_years", "residual_pct", "residual_z",
            "tire_growth_log", "vehicle_growth_log", "relative_gap_log", "residual_flag", "growth_flag"]
    summary = [
        "# Pipeline results (generated by scripts/run_pipeline.py)\n",
        f"Run date: {dt.date.today()}. Sales quarters: {quarters[0]}-{quarters[-1]}. "
        f"Train {min(config.TRAIN_YEARS)}-{max(config.TRAIN_YEARS)}; test {config.TEST_FIRST_YEAR}-last year of each view. "
        f"Counties passing tire-data checks: {len(included)} of {len(excl)}.\n",
        "## Candidate tiers\n", md_table(tiers), "\n",
        "## City-level breakdown of real tire-specialist growth (flagged counties)\n",
        md_table(breakdown, ".2f"), "\n",
        "## Views\n", md_table(view_summary), "\n",
    ]
    for v, r in views.items():
        ranked = r[f"signals_{v}"]
        summary += [
            f"## {config.DEALER_VIEWS[v]['label']} ({v})\n",
            "Evaluation (test years):\n", md_table(r[f"evaluation_{v}"]), "\n",
            f"Typical (median absolute) test log error: {ranked['typical_error'].iloc[0]:.3f}\n",
            "Counties with either flag:\n", md_table(ranked[ranked["residual_flag"] | ranked["growth_flag"]][show]), "\n",
        ]
    summary += [
        "## Excluded counties (tire-data quality, all views)\n",
        md_table(excl.loc[excl["excluded"], ["county", "hidden_quarter_share", "reason"]], ".2f"), "\n",
        "## 2022 NAICS switch check (statewide tire Q2/Q1)\n", md_table(outputs["naics_transition_check"]), "\n",
        f"## Quarter-over-quarter outliers: {len(outputs['qoq_outliers'])} county-quarters flagged "
        f"(|county - statewide QoQ log change| > {config.QOQ_OUTLIER_LOG}); see data/processed/qoq_outliers.csv\n",
    ]
    (config.REPORTS / "results_summary.md").write_text("\n".join(summary))

    print(f"\ncounties passing tire-data checks: {len(included)} / {len(excl)}")
    print(view_summary.to_string(index=False))
    print("\n" + tiers.to_string(index=False))
    for v, r in views.items():
        print(f"\n[{v}]")
        print(r[f"evaluation_{v}"].to_string(index=False))
        ranked = r[f"signals_{v}"]
        print(ranked[ranked["residual_flag"] | ranked["growth_flag"]][show].round(3).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-pull raw data instead of using data/raw/ caches")
    main(ap.parse_args().refresh)
