"""Test-year metrics: MAPE and mean absolute log error, baseline vs model."""

import numpy as np
import pandas as pd


def mape(actual, pred):
    return float(np.mean(np.abs(pred / actual - 1)))


def male(actual, pred):
    return float(np.mean(np.abs(np.log(pred / actual))))


def evaluation_table(pred):
    rows = []
    for method in ("baseline", "model"):
        rows.append({"method": method, "MAPE": mape(pred["actual"], pred[method]),
                     "mean_abs_log_error": male(pred["actual"], pred[method]),
                     "n_county_years": len(pred), "years": f"{pred['year'].min()}-{pred['year'].max()}"})
    return pd.DataFrame(rows)


def evaluation_by_year(pred):
    return pred.groupby("year").apply(
        lambda g: pd.Series({"baseline_MAPE": mape(g["actual"], g["baseline"]),
                             "model_MAPE": mape(g["actual"], g["model"])}),
        include_groups=False,
    ).reset_index()
