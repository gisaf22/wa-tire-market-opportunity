"""v1.1 rigour checks on the v1 snapshot. Writes data/processed/rigour_*.csv.

Reads the pipeline's processed county-year table and the cached raw DOR pull (for the city-level
concentration rule), so run scripts/run_pipeline.py first.

Usage (from the repo root):
    python3 scripts/run_rigour.py
"""

from wa_tire import build, config, model, pull_cpi, pull_wa, rigour, signals

DRAWS = 2000
SEED = 20261015
CANDIDATES = ["Kittitas", "Asotin"]


def main():
    cy = build.load_processed("county_year")
    excl = build.load_processed("exclusions")
    included = sorted(excl.loc[~excl["excluded"], "county"])
    growth_end = int(cy.loc[cy["vehicles"].notna(), "year"].max())
    rules = dict(recent_n=config.RECENT_YEARS_N, z_min=config.RESIDUAL_Z_MIN, top_share=config.TOP_SHARE,
                 base_year=config.GROWTH_BASE_YEAR, end_year=growth_end)

    frames, outputs = {}, {}
    for v, d in config.DEALER_VIEWS.items():
        df, _ = model.model_frame(cy, included, d["col"])
        frames[v] = df
        fit, ranked = rigour.score(df, cy, **rules)
        groups = df.loc[df["year"].isin(config.TRAIN_YEARS), "county"].nunique()
        outputs[f"rigour_coef_ci_{v}"] = rigour.coef_ci(fit, groups)
        outputs[f"rigour_baseline_{v}"] = ranked
        print(f"[{v}] bootstrap {DRAWS} draws")
        long = rigour.bootstrap(df, cy, DRAWS, SEED, **rules)
        outputs[f"rigour_bootstrap_{v}"] = rigour.summarise_bootstrap(long)
        loo = rigour.leave_one_out(df, cy, **rules)
        outputs[f"rigour_loo_{v}"] = loo
        outputs[f"rigour_loo_changes_{v}"] = rigour.loo_changes(loo, ranked, CANDIDATES)

    # Concentration for every included county, so a county newly tiered in a refit gets the same cap rule.
    raw, _ = pull_wa.pull_sales(refresh=False)
    deflators = pull_cpi.quarterly_deflators(pull_cpi.pull_cpi(int(config.FIRST_QUARTER[:4]), growth_end + 1))
    concentration = build.growth_concentration(
        build.city_breakdown(raw, deflators, included, config.GROWTH_BASE_YEAR, growth_end))
    views = {v: d["short"] for v, d in config.DEALER_VIEWS.items()}
    loo_tier = rigour.loo_tiers(frames, cy, views, concentration, config.CONCENTRATION_MAX_SHARE, **rules)
    outputs["rigour_loo_tiers"] = loo_tier
    outputs["rigour_tier_changes"] = rigour.tier_changes(loo_tier, build.load_processed("candidate_tiers"))

    for name, frame in outputs.items():
        frame.to_csv(config.PROCESSED / f"{name}.csv", index=False)
    for v in config.DEALER_VIEWS:
        print(f"\n[{v}]\n", outputs[f"rigour_coef_ci_{v}"].round(3).to_string(index=False))
        b = outputs[f"rigour_bootstrap_{v}"]
        print(b[b["county"].isin(CANDIDATES)].round(3).to_string(index=False))
        print(outputs[f"rigour_loo_changes_{v}"].to_string(index=False))
    print("\ntier changes under leave-one-out:\n", outputs["rigour_tier_changes"].to_string(index=False))


if __name__ == "__main__":
    main()
