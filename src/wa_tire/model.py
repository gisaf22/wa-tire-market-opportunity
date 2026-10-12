"""Baseline and log-linear model of real tire-dealer sales, with a time split.

The dealer-activity regressor is a parameter (`dealer_col`): CBP new-car dealer employment
(primary view) or DOR new-car-dealer real taxable sales (secondary view).

Both predictors are calibrated each year so predictions sum to the actual total of the
counties in the view. The baseline does this by construction (sales per vehicle); the model
gets the same treatment, since year effects for unseen test years cannot be estimated.
Evaluation therefore measures how well each method *allocates* a year's sales across
counties, which is what the residual signal relies on.
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from wa_tire import config

FORMULA = "log_tire ~ log_vehicles + log_dealer + C(year)"


def model_frame(cy, included, dealer_col):
    """Model years where dealer_col is available; drops counties missing it in any of those years.

    Returns (frame, dropped counties).
    """
    available = cy.loc[cy[dealer_col].notna(), "year"]
    last = int(available.max())
    df = cy[(cy["year"] >= config.MODEL_FIRST_YEAR) & (cy["year"] <= last) & cy["county"].isin(included)].copy()
    ok = (df[dealer_col] > 0).groupby(df["county"]).all() & df.groupby("county")["year"].nunique().eq(
        last - config.MODEL_FIRST_YEAR + 1)
    dropped = sorted(ok[~ok].index)
    df = df[df["county"].isin(ok[ok].index)]
    df["log_tire"] = np.log(df["tire_real"])
    df["log_vehicles"] = np.log(df["vehicles"])
    df["log_dealer"] = np.log(df[dealer_col])
    return df, dropped


def calibrate(df, raw_pred):
    """Scale predictions so each year's sum equals that year's actual total."""
    scale = df["tire_real"].groupby(df["year"]).transform("sum") / raw_pred.groupby(df["year"]).transform("sum")
    return raw_pred * scale


def baseline_predict(df):
    """Real tire sales per registered vehicle (counties in the view) x county vehicles."""
    return calibrate(df, df["vehicles"].astype(float))


def fit_loglinear(train):
    groups = pd.factorize(train["county"])[0]
    return smf.ols(FORMULA, data=train).fit(cov_type="cluster", cov_kwds={"groups": groups})


def loglinear_predict(fit, df):
    """exp(intercept + b_v log vehicles + b_d log dealer activity), calibrated per year."""
    p = fit.params
    raw = np.exp(p["Intercept"] + p["log_vehicles"] * df["log_vehicles"] + p["log_dealer"] * df["log_dealer"])
    return calibrate(df, raw)


def split(df):
    return df[df["year"].isin(config.TRAIN_YEARS)], df[df["year"] >= config.TEST_FIRST_YEAR]


def predictions(fit, df):
    return pd.DataFrame({
        "county": df["county"], "year": df["year"], "actual": df["tire_real"],
        "baseline": baseline_predict(df), "model": loglinear_predict(fit, df),
    })


def run_split(df):
    """Fit on train years, predict test years (out of sample). Used for evaluation and signals."""
    train, test = split(df)
    fit = fit_loglinear(train)
    return fit, predictions(fit, test)


def coefficient_table(fit):
    rows = ["log_vehicles", "log_dealer"]
    return pd.DataFrame({
        "coef": fit.params[rows], "std_err (cluster by county)": fit.bse[rows], "p_value": fit.pvalues[rows],
    }).assign(n_obs=int(fit.nobs), r_squared=fit.rsquared)
