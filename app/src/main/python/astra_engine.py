"""
ASTRA-BIO analysis engine for Android (Chaquopy).

Dependencies: numpy + scipy ONLY.
- statsmodels is NOT available on Chaquopy  -> Benjamini-Hochberg FDR is
  implemented by hand below (identical algorithm, verified against statsmodels).
- matplotlib is NOT available on Android     -> all charting happens natively
  in Kotlin (MPAndroidChart). This module returns plain JSON-able data only.

Public functions (called from Kotlin):
    demo_analysis()                     -> JSON string: full sample-data analysis
    analyze_uploaded(earth_json,        -> JSON string: phenotype comparison
                      space_json,
                      params_json)
    analyze_matrix_json(features_json,  -> JSON string: per-feature differential
                        e_json, s_json)    abundance for omics matrices
"""

import json
import math

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def _effect_size_label(d):
    a = abs(d)
    if a < 0.2: return "negligible"
    if a < 0.5: return "small"
    if a < 0.8: return "medium"
    return "large"


def compare_feature(e_vals, s_vals, name):
    e = np.asarray([v for v in e_vals if v is not None and not math.isnan(v)], dtype=float)
    s = np.asarray([v for v in s_vals if v is not None and not math.isnan(v)], dtype=float)

    e_mean, s_mean = float(e.mean()), float(s.mean())
    e_std, s_std = float(e.std(ddof=1)), float(s.std(ddof=1))

    pooled = math.sqrt(((len(e) - 1) * e_std ** 2 + (len(s) - 1) * s_std ** 2) /
                       (len(e) + len(s) - 2)) if (len(e) + len(s)) > 2 else 0.0
    d = (s_mean - e_mean) / pooled if pooled > 0 else 0.0

    fc = s_mean / e_mean if e_mean != 0 else float("nan")
    l2fc = math.log2(fc) if fc and fc > 0 else 0.0
    pct = (fc - 1.0) * 100.0 if fc == fc else float("nan")  # NaN check

    t_res = stats.ttest_ind(s, e, equal_var=False)
    t_stat, p_val = float(t_res.statistic), float(t_res.pvalue)

    diff = s_mean - e_mean
    se = pooled * math.sqrt(1.0 / len(e) + 1.0 / len(s)) if pooled > 0 else 0.0
    df = getattr(t_res, "df", len(e) + len(s) - 2)
    if se > 0:
        lo, hi = stats.t.interval(0.95, df, loc=diff, scale=se)
        lo, hi = float(lo), float(hi)
    else:
        lo = hi = diff

    return {
        "feature": str(name),
        "earth_mean": e_mean, "space_mean": s_mean,
        "difference": diff,
        "fold_change": fc if fc == fc else None,
        "log2_fold_change": l2fc,
        "pct_change": pct if pct == pct else None,
        "cohens_d": d, "effect_size": _effect_size_label(d),
        "t_statistic": t_stat, "p_value": p_val, "p_value_adj": p_val,
        "ci95_lower": lo, "ci95_upper": hi,
        "significant": bool(p_val < 0.05),
        "n_earth": int(len(e)), "n_space": int(len(s)),
    }


def bh_fdr(results):
    """Benjamini-Hochberg correction (replaces statsmodels.multipletests)."""
    n = len(results)
    if n == 0:
        return results
    order = sorted(range(n), key=lambda i: results[i]["p_value"])
    prev = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        q = min(prev, results[i]["p_value"] * n / rank)
        prev = q
        results[i]["p_value_adj"] = q
        results[i]["significant"] = bool(q < 0.05)
    return results


# ---------------------------------------------------------------------------
# Pipelines (input arrives as JSON strings from Kotlin)
# ---------------------------------------------------------------------------

def analyze_phenotypes(earth, space, params=None):
    """earth/space: {"columns": [...], "rows": [[...], ...]} numeric tables."""
    cols = earth["columns"]
    if params is None:
        params = cols
    results = []
    for p in params:
        if p not in cols:
            continue
        j = cols.index(p)
        e_col = [r[j] for r in earth["rows"] if j < len(r)]
        s_col = [r[j] for r in space["rows"] if j < len(r)]
        try:
            results.append(compare_feature(e_col, s_col, p))
        except (ValueError, TypeError):
            continue
    bh_fdr(results)
    return results


def analyze_matrix(features, e_matrix, s_matrix):
    """Row-oriented omics matrices: features[i], values per sample in rows."""
    results = [compare_feature(e_matrix[i], s_matrix[i], features[i])
               for i in range(min(len(features), len(e_matrix), len(s_matrix)))]
    bh_fdr(results)
    return results


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, float) and o != o:  # NaN -> null
        return None
    return str(o)


# ---------------------------------------------------------------------------
# Built-in demo (works 100% offline)
# ---------------------------------------------------------------------------

def demo_analysis():
    rng = np.random.default_rng(42)
    n = 30

    # --- phenotypes ---
    earth_rows = np.column_stack([
        rng.normal(0.45, 0.08, n),   # growth_rate
        rng.normal(2.0, 0.3, n),     # MIC
        rng.normal(0.35, 0.06, n),   # biofilm
    ]).tolist()
    space_rows = np.column_stack([
        rng.normal(0.38, 0.09, n),
        rng.normal(3.2, 0.5, n),
        rng.normal(0.52, 0.08, n),
    ]).tolist()
    pheno = analyze_phenotypes(
        {"columns": ["growth_rate", "MIC", "biofilm_biomass"], "rows": earth_rows},
        {"columns": ["growth_rate", "MIC", "biofilm_biomass"], "rows": space_rows})

    # --- omics (rows = features, cols = samples) ---
    def omics(names, e_mu, s_mu, e_sd, s_sd):
        e = rng.normal(e_mu, e_sd, (len(names), n))
        s = rng.normal(s_mu, s_sd, (len(names), n))
        return analyze_matrix(list(names), e.tolist(), s.tolist())

    genes = ["katG", "sodA", "recA", "lexA", "ompF", "acrA", "marR", "soxR"]
    proteins = [f"PRO{i:03d}" for i in range(1, 21)]
    mets = [f"MET{i:03d}" for i in range(1, 26)]

    out = {
        "phenotypes": pheno,
        "transcriptomics": omics(genes, 5.0, 9.0, 1.0, 1.5),
        "proteomics": omics(proteins, 1.0, 1.6, 0.3, 0.4),
        "metabolomics": omics(mets, 10.0, 14.0, 3.0, 4.0),
    }
    return json.dumps(out, default=_json_default)


# ---------------------------------------------------------------------------
# Entry points called from Kotlin (all take/return JSON strings)
# ---------------------------------------------------------------------------

def analyze_uploaded(earth_json, space_json, params_json="null"):
    earth = json.loads(earth_json)
    space = json.loads(space_json)
    params = json.loads(params_json)
    return json.dumps(analyze_phenotypes(earth, space, params), default=_json_default)


def analyze_matrix_json(features_json, e_json, s_json):
    return json.dumps(
        analyze_matrix(json.loads(features_json), json.loads(e_json), json.loads(s_json)),
        default=_json_default)
