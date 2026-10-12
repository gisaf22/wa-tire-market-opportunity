"""Baseline and log-linear model of real tire-dealer sales, with a time split.

Both predictors are calibrated each year so predictions sum to the actual statewide total
(of included counties). The baseline does this by construction (statewide sales per vehicle);
the model gets the same treatment, since year effects for unseen test years cannot be
estimated. Evaluation therefore measures how well each method *allocates* a year's
statewide sales across counties, which is what the residual signal relies on.
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from wa_tire import config

FORMULA = "log_tire ~ log_vehicles + log_newcar + C(year)"


def model_frame(cy, included):
    df = cy[(cy["year"] >= config.MODEL_FIRST_YEAR) & cy["county"].isin(included)].copy()
    df["log_tire"] = np.log(df["tire_real"])
    df["log_vehicles"] = np.log(df["vehicles"])
    df["log_newcar"] = np.log(df["newcar_real"])
    return df


def calibrate(df, raw_pred):
    """Scale predictions so each year's sum equals that year's actual statewide total."""
    scale = df["tire_real"].groupby(df["year"]).transform("sum") / raw_pred.groupby(df["year"]).transform("sum")
    return raw_pred * scale


def baseline_predict(df):
    """Statewide real tire sales per registered vehicle x county vehicles."""
    return calibrate(df, df["vehicles"].astype(float))


def fit_loglinear(train):
    groups = pd.factorize(train["county"])[0]
    return smf.ols(FORMULA, data=train).fit(cov_type="cluster", cov_kwds={"groups": groups})


def loglinear_predict(fit, df):
    """exp(intercept + b_v log vehicles + b_d log new-car sales), calibrated per year."""
    p = fit.params
    raw = np.exp(p["Intercept"] + p["log_vehicles"] * df["log_vehicles"] + p["log_newcar"] * df["log_newcar"])
    return calibrate(df, raw)


def split(df):
    return df[df["year"].isin(config.TRAIN_YEARS)], df[df["year"] >= config.TEST_FIRST_YEAR]


def predictions(fit, df):
    return pd.DataFrame({
        "county": df["county"], "year": df["year"], "actual": df["tire_real"],
        "baseline": baseline_predict(df), "model": loglinear_predict(fit, df),
    })


def run_split(df):
    """Fit on train years, predict test years."""
    train, test = split(df)
    fit = fit_loglinear(train)
    return fit, predictions(fit, test)


def run_full(df):
    """Fit on all model years; used for the residual signal."""
    fit = fit_loglinear(df)
    return fit, predictions(fit, df)


def coefficient_table(fit):
    rows = ["log_vehicles", "log_newcar"]
    return pd.DataFrame({
        "coef": fit.params[rows], "std_err (cluster by county)": fit.bse[rows], "p_value": fit.pvalues[rows],
    }).assign(n_obs=int(fit.nobs), r_squared=fit.rsquared)
