# -*- coding: utf-8 -*-
"""
Python rewrite of the MATLAB script:
Mechanistic closure and satellite-observable precursor skill, 3 x 3 figure.

Important:
- This script only loads existing MAT outputs and replots the figure.
- It does not recalculate any upstream diagnostics.
- The numerical operations follow the original MATLAB plotting script as closely as possible.

Recommended packages:
    pip install numpy pandas scipy matplotlib mat73

If your MAT files are MATLAB v7.3 files, mat73 is usually needed.
If your MAT files are older MAT files, scipy.io.loadmat is usually enough.
"""

from __future__ import annotations

from pathlib import Path
import re
import warnings
from typing import Any, Dict, Optional, Sequence

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from scipy.io import loadmat
except Exception as exc:  # pragma: no cover
    loadmat = None
    warnings.warn(f"scipy.io.loadmat is unavailable: {exc}")


# ============================================================
# 0. Paths
# ============================================================

rootDir = Path(r"E:\GLORYS4V1")

matNM = rootDir / "StepNM_near_miss_T100_onset_control" / "StepNM_near_miss_T100_onset_control.mat"
matTD = rootDir / "StepTD_thermocline_displacement_T100_estimate" / "StepTD_thermocline_displacement_T100_estimate.mat"
matSK = rootDir / "StepSK_DUACS_SLA_precursor_skill_AUC" / "StepSK_DUACS_SLA_precursor_skill_AUC.mat"

outDir = rootDir / "StepFIG_mechanistic_closure_satellite_precursor_skill"
outDir.mkdir(parents=True, exist_ok=True)

for label, path in [
    ("near-miss MAT file", matNM),
    ("thermocline-displacement MAT file", matTD),
    ("DUACS skill MAT file", matSK),
]:
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {label}:\n{path}")

print("Loading existing MAT outputs only...")


# ============================================================
# Helper functions for MATLAB MAT loading and table conversion
# ============================================================

def load_mat_file(path: Path) -> Dict[str, Any]:
    """Load a MAT file with scipy first and mat73 as fallback."""
    if loadmat is not None:
        try:
            data = loadmat(str(path), simplify_cells=True, squeeze_me=True, struct_as_record=False)
            return {k: _mat_to_builtin(v) for k, v in data.items() if not k.startswith("__")}
        except NotImplementedError:
            # MATLAB v7.3 HDF5 files usually trigger this path.
            pass
        except ValueError as exc:
            # Some v7.3 files can raise ValueError rather than NotImplementedError.
            if "Unknown mat file type" not in str(exc) and "Please use HDF reader" not in str(exc):
                raise
        except Exception as exc:
            warnings.warn(
                f"scipy.io.loadmat could not load {path.name}: {exc}\n"
                "Trying mat73 instead."
            )

    try:
        import mat73  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Could not load MAT file with scipy, and mat73 is not installed.\n"
            "Install it with: pip install mat73"
        ) from exc

    data = mat73.loadmat(str(path))
    return {k: _mat_to_builtin(v) for k, v in data.items()}


def _mat_to_builtin(obj: Any) -> Any:
    """Recursively convert common scipy/mat73 MATLAB objects to Python objects."""
    if isinstance(obj, dict):
        return {str(k): _mat_to_builtin(v) for k, v in obj.items()}

    if hasattr(obj, "_fieldnames"):
        return {field: _mat_to_builtin(getattr(obj, field)) for field in obj._fieldnames}

    if isinstance(obj, np.ndarray):
        if obj.dtype.names is not None:
            if obj.shape == ():
                return _mat_to_builtin(obj.item())
            if obj.size == 1:
                return _mat_to_builtin(obj.reshape(-1)[0])
            out = {}
            for name in obj.dtype.names:
                out[name] = _mat_to_builtin(obj[name].squeeze())
            return out

        if obj.dtype == object:
            if obj.shape == ():
                return _mat_to_builtin(obj.item())
            return np.array([_mat_to_builtin(v) for v in obj.ravel()], dtype=object).reshape(obj.shape)

    return obj


def _decode_string_like(x: Any) -> Any:
    """Convert MATLAB char/cellstr-like objects to Python strings when possible."""
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="ignore")
    if isinstance(x, np.bytes_):
        return bytes(x).decode("utf-8", errors="ignore")
    if isinstance(x, str):
        return x
    if isinstance(x, np.str_):
        return str(x)

    if isinstance(x, np.ndarray):
        if x.dtype.kind in "US":
            if x.ndim == 0:
                return str(x.item())
            if x.ndim == 1:
                return "".join(map(str, x.tolist())).strip()
            if x.ndim == 2:
                return np.array(["".join(map(str, row)).strip() for row in x], dtype=object)
        if x.size == 1:
            return _decode_string_like(x.reshape(-1)[0])

    return x


def _as_1d_array(value: Any) -> Optional[np.ndarray]:
    """Convert a MATLAB column-like value to a 1-D numpy array if possible."""
    value = _mat_to_builtin(value)
    value = _decode_string_like(value)

    if isinstance(value, pd.Series):
        arr = value.to_numpy()
    elif isinstance(value, pd.Index):
        arr = value.to_numpy()
    elif isinstance(value, (list, tuple)):
        arr = np.array([_decode_string_like(v) for v in value], dtype=object)
    elif isinstance(value, (str, bytes, np.str_, np.bytes_)):
        arr = np.array([_decode_string_like(value)], dtype=object)
    elif np.isscalar(value):
        arr = np.array([value])
    elif isinstance(value, np.ndarray):
        value = _decode_string_like(value)
        if isinstance(value, str):
            arr = np.array([value], dtype=object)
        elif isinstance(value, np.ndarray):
            arr = value
        else:
            arr = np.array([value], dtype=object)
    else:
        return None

    if isinstance(arr, np.ndarray) and arr.dtype == object:
        arr = np.array([_decode_string_like(v) for v in arr.ravel()], dtype=object).reshape(arr.shape)

    if arr.ndim == 0:
        arr = arr.reshape(1)
    elif arr.ndim == 1:
        pass
    elif arr.ndim == 2:
        # MATLAB column/row vector.
        if 1 in arr.shape:
            arr = arr.ravel()
        # Character matrix, already handled above, but keep a safe path.
        elif arr.dtype.kind in "US":
            arr = np.array(["".join(map(str, row)).strip() for row in arr], dtype=object)
        else:
            return None
    else:
        return None

    return arr


def _get_variable_names_from_properties(props: Any) -> Optional[Sequence[str]]:
    props = _mat_to_builtin(props)
    if not isinstance(props, dict):
        return None
    for key in ("VariableNames", "VariableNames_", "variableNames"):
        if key in props:
            arr = _as_1d_array(props[key])
            if arr is not None:
                return [str(v) for v in arr]
    return None


def to_dataframe(obj: Any, name: str = "table") -> pd.DataFrame:
    """
    Convert common MATLAB table/struct representations to a pandas DataFrame.

    This handles the common cases returned by scipy.io.loadmat(simplify_cells=True)
    and mat73.loadmat. If your MATLAB table is saved in a format that Python cannot
    decode directly, resave the table as ordinary variables or use MATLAB to export it
    to CSV. That does not change the upstream data calculation.
    """
    if isinstance(obj, pd.DataFrame):
        return obj.copy()

    obj = _mat_to_builtin(obj)

    if isinstance(obj, dict):
        # Some MATLAB table decoders store variables as obj['data'] and names in Properties.
        props = obj.get("Properties", None)
        var_names = _get_variable_names_from_properties(props)
        if "data" in obj and var_names is not None:
            data_obj = obj["data"]
            if isinstance(data_obj, (list, tuple, np.ndarray)):
                flat = list(np.array(data_obj, dtype=object).ravel())
                if len(flat) == len(var_names):
                    cols = {}
                    for col_name, col_value in zip(var_names, flat):
                        arr = _as_1d_array(col_value)
                        if arr is not None:
                            cols[str(col_name)] = arr
                    if cols:
                        return _align_columns_to_dataframe(cols, name)

        # Most convenient case: a struct/dict whose fields are table columns.
        skip_keys = {
            "Properties", "Row", "Variables", "DimensionNames", "Description",
            "UserData", "VariableDescriptions", "VariableUnits", "VariableContinuity",
        }
        cols: Dict[str, np.ndarray] = {}
        for key, value in obj.items():
            if key in skip_keys or str(key).startswith("__"):
                continue
            arr = _as_1d_array(value)
            if arr is not None:
                cols[str(key)] = arr

        if cols:
            return _align_columns_to_dataframe(cols, name)

    if isinstance(obj, np.ndarray) and obj.dtype.names is not None:
        cols = {field: _as_1d_array(obj[field]) for field in obj.dtype.names}
        cols = {k: v for k, v in cols.items() if v is not None}
        if cols:
            return _align_columns_to_dataframe(cols, name)

    raise TypeError(
        f"Could not convert {name} to a pandas DataFrame.\n"
        "If this is a MATLAB table and Python cannot decode it, consider resaving it "
        "from MATLAB as a struct/table compatible MAT file or exporting the table to CSV."
    )


def _align_columns_to_dataframe(cols: Dict[str, np.ndarray], name: str) -> pd.DataFrame:
    lengths = {k: len(v) for k, v in cols.items()}
    if not lengths:
        return pd.DataFrame()

    n = max(lengths.values())
    aligned: Dict[str, np.ndarray] = {}
    for k, v in cols.items():
        if len(v) == n:
            aligned[k] = v
        elif len(v) == 1 and n > 1:
            aligned[k] = np.repeat(v, n)
        else:
            warnings.warn(
                f"Column {k!r} in {name} has length {len(v)}, not {n}; dropping it."
            )

    return pd.DataFrame(aligned)


def get_field(container: Any, key: str) -> Any:
    if isinstance(container, dict):
        if key not in container:
            raise KeyError(key)
        return container[key]
    if hasattr(container, key):
        return getattr(container, key)
    raise KeyError(key)


def has_field(container: Any, key: str) -> bool:
    if isinstance(container, dict):
        return key in container
    return hasattr(container, key)


def string_col(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    if col_name in df.columns:
        df[col_name] = df[col_name].map(lambda x: str(_decode_string_like(x)))
    return df


def numeric_col(df: pd.DataFrame, col_name: str) -> np.ndarray:
    if col_name not in df.columns:
        raise KeyError(f"DataFrame does not contain required column: {col_name}")
    return pd.to_numeric(df[col_name], errors="coerce").to_numpy(dtype=float)


def bool_col(df: pd.DataFrame, col_name: str) -> np.ndarray:
    if col_name not in df.columns:
        raise KeyError(f"DataFrame does not contain required column: {col_name}")
    s = df[col_name]
    if s.dtype == bool:
        return s.to_numpy(dtype=bool)
    return pd.to_numeric(s, errors="coerce").fillna(0).to_numpy(dtype=float).astype(bool)


def scalar_value(value: Any) -> float:
    value = _decode_string_like(value)
    arr = np.asarray(value)
    if arr.size == 0:
        return np.nan
    try:
        return float(arr.reshape(-1)[0])
    except Exception:
        return np.nan


def row_scalar(row: Optional[pd.DataFrame], col_name: str) -> float:
    if row is None or row.empty or col_name not in row.columns:
        return np.nan
    return scalar_value(row.iloc[0][col_name])


def matlab_valid_name_approx(s: str) -> str:
    """Approximate MATLAB matlab.lang.makeValidName for ROCstore lookup."""
    s = str(s)

    # MATLAB removes whitespace and capitalizes the following character.
    out = []
    cap_next = False
    for ch in s:
        if ch.isspace():
            cap_next = True
            continue
        if cap_next:
            out.append(ch.upper())
            cap_next = False
        else:
            out.append(ch)
    s = "".join(out)

    # Replace invalid identifier characters with underscores.
    s = re.sub(r"[^0-9A-Za-z_]", "_", s)

    # First character must be a letter.
    if not s or not re.match(r"[A-Za-z]", s[0]):
        s = "x" + s
    return s


def get_roc_entry(rocstore: Any, comparison: str, predictor: str) -> Optional[Any]:
    rocstore = _mat_to_builtin(rocstore)
    raw = f"{comparison}_{predictor}"
    candidates = [
        matlab_valid_name_approx(raw),
        raw,
        raw.replace(" ", "_").replace("-", "_"),
        re.sub(r"[^0-9A-Za-z_]", "_", raw),
    ]

    if isinstance(rocstore, dict):
        for key in candidates:
            if key in rocstore:
                return rocstore[key]

        # Fallback: search by predictor and warm/near/miss keywords.
        pred_low = predictor.lower()
        for key, value in rocstore.items():
            key_low = str(key).lower()
            if pred_low in key_low and "warm" in key_low and "miss" in key_low:
                return value

    for key in candidates:
        if hasattr(rocstore, key):
            return getattr(rocstore, key)

    return None


def array_from_field(container: Any, key: str) -> np.ndarray:
    value = get_field(container, key)
    arr = _as_1d_array(value)
    if arr is None:
        arr = np.asarray(value).ravel()
    return pd.to_numeric(pd.Series(arr), errors="coerce").to_numpy(dtype=float)


# ============================================================
# 1. Load MAT files
# ============================================================

NM = load_mat_file(matNM)
TD = load_mat_file(matTD)
SK = load_mat_file(matSK)


# ============================================================
# 2. Unified style
# ============================================================

plt_style = {
    "fontName": "Arial",
    "fontSize": 16,
    "lineWidth": 1.6,
}

plt.rcParams["font.family"] = plt_style["fontName"]
plt.rcParams["font.size"] = plt_style["fontSize"]
plt.rcParams["axes.linewidth"] = 0.9
plt.rcParams["axes.grid"] = True

# Required unified colors
cTrue = np.array([0.82, 0.16, 0.13])   # True onset: red
cFail = np.array([0.93, 0.48, 0.16])   # Failed P90 spell: orange
cNear = np.array([0.10, 0.43, 0.78])   # Near-miss P85-P90: blue
cRand = np.array([0.50, 0.50, 0.50])   # Random non-event: gray

cObs = cTrue                            # Observed T100: red
cDisp = cNear                           # Displacement estimate: blue
cRes = cRand                            # Residual: gray

cSLA = cTrue                            # DUACS SLA: red
cT100 = cNear                           # T100 persistence: blue
cComb = np.array([0.18, 0.58, 0.28])    # SLA + T100: green

GroupList = [
    "True onset",
    "Failed P90 spell",
    "Near-miss P85-P90",
    "Random non-event",
]

GroupShort = ["True", "Failed P90", "Near-miss", "Random"]
GroupColors = np.vstack([cTrue, cFail, cNear, cRand])

colors = {
    "True onset": cTrue,
    "Failed P90 spell": cFail,
    "Near-miss P85-P90": cNear,
    "Random non-event": cRand,
}


# ============================================================
# 3. Basic checks and table conversion
# ============================================================

needNM = ["PreEvent", "ProbTab"]
for key in needNM:
    if not has_field(NM, key):
        raise KeyError(f"Near-miss MAT does not contain {key}.")

needTD = ["D", "Comp", "Metrics", "PreEvent"]
for key in needTD:
    if not has_field(TD, key):
        raise KeyError(f"Thermocline MAT does not contain {key}.")

needSK = ["Cand", "Skill", "ProbSLA", "ROCstore"]
for key in needSK:
    if not has_field(SK, key):
        raise KeyError(f"DUACS skill MAT does not contain {key}.")

NM_PreEvent = string_col(to_dataframe(get_field(NM, "PreEvent"), "NM.PreEvent"), "Group")
NM_ProbTab = string_col(to_dataframe(get_field(NM, "ProbTab"), "NM.ProbTab"), "Predictor")

TD_D = to_dataframe(get_field(TD, "D"), "TD.D")
TD_Comp = string_col(to_dataframe(get_field(TD, "Comp"), "TD.Comp"), "Variable")
TD_Metrics = string_col(to_dataframe(get_field(TD, "Metrics"), "TD.Metrics"), "Sample")
TD_PreEvent = to_dataframe(get_field(TD, "PreEvent"), "TD.PreEvent")

SK_Cand = string_col(to_dataframe(get_field(SK, "Cand"), "SK.Cand"), "Group")
SK_Skill = string_col(to_dataframe(get_field(SK, "Skill"), "SK.Skill"), "Comparison")
SK_Skill = string_col(SK_Skill, "Predictor")
SK_Skill = string_col(SK_Skill, "PredictorLabel")
SK_ProbSLA = to_dataframe(get_field(SK, "ProbSLA"), "SK.ProbSLA")
SK_ROCstore = get_field(SK, "ROCstore")


# ============================================================
# Local plotting helpers
# ============================================================

def style_axis(ax: plt.Axes, style: Dict[str, Any]) -> None:
    ax.tick_params(axis="both", which="both", direction="out", labelsize=style["fontSize"])
    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
    ax.grid(True, alpha=0.18)
    ax.set_axisbelow(False)


def get_metric_row(metrics: pd.DataFrame, sample_name: str) -> pd.DataFrame:
    if metrics.empty or "Sample" not in metrics.columns:
        return pd.DataFrame()
    idx = metrics["Sample"].astype(str) == str(sample_name)
    if idx.any():
        return metrics.loc[idx].iloc[[0]].copy()
    return pd.DataFrame()


def add_saved_scatter_lines(ax: plt.Axes, x: np.ndarray, y: np.ndarray, m_row: pd.DataFrame) -> None:
    x = np.asarray(x).ravel()
    y = np.asarray(y).ravel()
    ok = np.isfinite(x) & np.isfinite(y)

    if np.sum(ok) < 3:
        return

    allv = np.concatenate([x[ok], y[ok]])
    mn = np.nanmin(allv)
    mx = np.nanmax(allv)
    pad = 0.08 * (mx - mn)

    if not np.isfinite(pad) or pad == 0:
        pad = 0.1

    lims = np.array([mn - pad, mx + pad])

    ax.plot(lims, lims, "k--", linewidth=0.9)

    # Use saved regression slope/intercept from Metrics when available.
    if (
        m_row is not None
        and not m_row.empty
        and "Slope_est_vs_obs" in m_row.columns
        and "Intercept_est_vs_obs" in m_row.columns
    ):
        slope = row_scalar(m_row, "Slope_est_vs_obs")
        intercept = row_scalar(m_row, "Intercept_est_vs_obs")

        if np.isfinite(slope) and np.isfinite(intercept):
            xx = np.linspace(lims[0], lims[1], 100)
            yy = slope * xx + intercept
            ax.plot(xx, yy, "-", color=[0.10, 0.10, 0.10], linewidth=1.1)

    ax.set_xlim(lims)
    ax.set_ylim(lims)


def plot_comp(
    ax: plt.Axes,
    comp: pd.DataFrame,
    var_name: str,
    color_val: Sequence[float],
    line_width: float,
    display_name: str,
) -> None:
    if comp.empty:
        warnings.warn("Comp is empty.")
        return

    need_cols = ["Variable", "RelDay", "Mean", "SEM"]
    for col in need_cols:
        if col not in comp.columns:
            warnings.warn(f"Comp does not contain {col}.")
            return

    idx = comp["Variable"].astype(str) == str(var_name)
    tab = comp.loc[idx].copy()

    if tab.empty:
        warnings.warn(f"Cannot find composite variable: {var_name}")
        return

    tab = tab.sort_values("RelDay")

    xx = pd.to_numeric(tab["RelDay"], errors="coerce").to_numpy(dtype=float)
    yy = pd.to_numeric(tab["Mean"], errors="coerce").to_numpy(dtype=float)
    ee = pd.to_numeric(tab["SEM"], errors="coerce").to_numpy(dtype=float)

    ax.fill_between(xx, yy - ee, yy + ee, color=color_val, alpha=0.13, linewidth=0)
    ax.plot(xx, yy, "-", color=color_val, linewidth=line_width, label=display_name)
    ax.set_xlim(np.nanmin(xx), np.nanmax(xx))


def safe_sem(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size > 1:
        return np.nanstd(x, ddof=0) / np.sqrt(x.size)
    return np.nan


# ============================================================
# 4. Create 3 x 3 figure
# ============================================================

fig, axes = plt.subplots(3, 3, figsize=(18.5, 15.0), dpi=100)
fig.patch.set_facecolor("white")
axes = axes.ravel()

# Similar to MATLAB tiledlayout(..., 'Padding','compact', 'TileSpacing','compact')
fig.subplots_adjust(left=0.055, right=0.985, bottom=0.055, top=0.975, wspace=0.26, hspace=0.30)


# ============================================================
# (a) near-miss Fig d
# Pre-onset SSH/D26/T100 anomalies bar
# ============================================================

ax = axes[0]
metricNames = ["SSH_pre_z", "D26_pre_z", "T100_pre_z"]
metricLabels = ["SSH", "D26", "T100"]

B = np.full((len(metricNames), len(GroupList)), np.nan)
SEM = np.full((len(metricNames), len(GroupList)), np.nan)

for im, v in enumerate(metricNames):
    if v not in NM_PreEvent.columns:
        warnings.warn(f"NM.PreEvent does not contain {v}. Panel (a) may be incomplete.")
        continue

    for ig, group_name in enumerate(GroupList):
        idx = NM_PreEvent["Group"] == group_name
        x = pd.to_numeric(NM_PreEvent.loc[idx, v], errors="coerce").to_numpy(dtype=float)
        x = x[np.isfinite(x)]
        B[im, ig] = np.nanmean(x) if x.size else np.nan
        SEM[im, ig] = safe_sem(x)

x_base = np.arange(len(metricNames))
bar_width = 0.82 / len(GroupList)
bar_handles = []

for ig, group_name in enumerate(GroupList):
    xpos = x_base - 0.41 + bar_width / 2 + ig * bar_width
    bars = ax.bar(
        xpos,
        B[:, ig],
        width=bar_width,
        color=GroupColors[ig],
        edgecolor=[0.25, 0.25, 0.25],
        linewidth=0.6,
        label=group_name,
    )
    bar_handles.append(bars)
    ax.errorbar(
        xpos,
        B[:, ig],
        yerr=SEM[:, ig],
        fmt="k.",
        linewidth=0.8,
        capsize=5,
    )

ax.axhline(0, color="k", linestyle=":", linewidth=1.0)
ax.set_xticks(x_base)
ax.set_xticklabels(metricLabels)
ax.set_ylabel("Mean z anomaly, day -10 to -1")
ax.set_title("(a) Pre-onset SSH / D26 / T100 anomalies")
ax.legend(loc="upper right", frameon=False)
style_axis(ax, plt_style)


# ============================================================
# (b) near-miss Fig f
# True-onset fraction by SSH-D26 precursor quartile
# ============================================================

ax = axes[1]
P = NM_ProbTab

if not P.empty:
    ax.bar(
        numeric_col(P, "Quartile"),
        numeric_col(P, "TrueOnsetFraction"),
        width=0.65,
        color=cNear,
        edgecolor=[0.25, 0.25, 0.25],
        linewidth=0.7,
    )
    ax.set_ylim(0, 1)
    ax.set_xlim(0.4, 4.6)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlabel("SSH-D26 precursor quartile")
    ax.set_ylabel("Fraction of true onsets")
else:
    ax.text(0.5, 0.5, "Not enough samples", transform=ax.transAxes, ha="center", va="center")

ax.set_title("(b) True-onset fraction by precursor strength")
style_axis(ax, plt_style)


# ============================================================
# (c) thermocline Fig c
# Observed vs displacement-estimated daily T100
# ============================================================

ax = axes[2]
D = TD_D

obs = numeric_col(D, "T100_anom_obs")
est = numeric_col(D, "T100_disp_est")
ok = np.isfinite(obs) & np.isfinite(est)

ax.scatter(
    obs[ok],
    est[ok],
    s=9,
    color=[0.25, 0.25, 0.25],
    alpha=0.22,
    edgecolors="none",
)

if "IsEventDay_final" in D.columns:
    okE = ok & bool_col(D, "IsEventDay_final")
else:
    okE = np.zeros_like(ok, dtype=bool)

ax.scatter(
    obs[okE],
    est[okE],
    s=14,
    color=cTrue,
    alpha=0.42,
    edgecolors="none",
)

mAll = get_metric_row(TD_Metrics, "All days")
add_saved_scatter_lines(ax, obs[ok], est[ok], mAll)

ax.set_xlabel("Observed T100 anomaly ($^{\\circ}$C)")
ax.set_ylabel("Displacement-estimated T100 anomaly ($^{\\circ}$C)")
ax.set_title("(c) Observed vs displacement-estimated daily T100")

if mAll is not None and not mAll.empty:
    txt = f"r = {row_scalar(mAll, 'R'):.2f}\n$R^2$ = {row_scalar(mAll, 'R2_corr'):.2f}"
    ax.text(
        0.05,
        0.94,
        txt,
        transform=ax.transAxes,
        ha="left",
        va="top",
        bbox=dict(facecolor="white", edgecolor="none", pad=4),
        fontsize=plt_style["fontSize"] - 0.5,
    )

style_axis(ax, plt_style)


# ============================================================
# (d) thermocline Fig d
# Event-onset composite: observed / displacement / residual
# ============================================================

ax = axes[3]
plot_comp(ax, TD_Comp, "T100_anom_obs", cObs, plt_style["lineWidth"], "Observed T100")
plot_comp(ax, TD_Comp, "T100_disp_est", cDisp, plt_style["lineWidth"], "Displacement estimate")
plot_comp(ax, TD_Comp, "T100_residual", cRes, 1.25, "Residual")

ax.axvline(0, color="k", linestyle="--", linewidth=1.0)
ax.axhline(0, color="k", linestyle=":", linewidth=1.0)
ax.set_xlabel("Days relative to T100 event onset")
ax.set_ylabel("T100 anomaly ($^{\\circ}$C)")
ax.set_title("(d) Event-onset composite")
ax.legend(loc="upper left", frameon=False)
style_axis(ax, plt_style)


# ============================================================
# (e) thermocline Fig f
# Pre-onset mean decomposition
# ============================================================

ax = axes[4]
PEtd = TD_PreEvent

preMeanObs = np.nanmean(numeric_col(PEtd, "T100_obs_pre"))
preMeanEst = np.nanmean(numeric_col(PEtd, "T100_disp_pre"))
preMeanRes = np.nanmean(numeric_col(PEtd, "T100_resid_pre"))
B_decomp = np.array([preMeanObs, preMeanEst, preMeanRes], dtype=float)

ax.bar(
    [1, 2, 3],
    B_decomp,
    width=0.6,
    color=[cObs, cDisp, cRes],
    edgecolor=[0.25, 0.25, 0.25],
    linewidth=0.8,
)

ax.set_xticks([1, 2, 3])
ax.set_xticklabels(["Observed", "Displacement", "Residual"])
ax.set_ylabel("Mean T100 anomaly, day -10 to -1 ($^{\\circ}$C)")
ax.set_title("(e) Pre-onset mean decomposition")
ax.axhline(0, color="k", linestyle=":", linewidth=1.0)

for i, val in enumerate(B_decomp, start=1):
    if np.isfinite(val):
        if val >= 0:
            va = "bottom"
            ytxt = val + 0.02
        else:
            va = "top"
            ytxt = val - 0.02
        ax.text(
            i,
            ytxt,
            f"{val:.2f}",
            ha="center",
            va=va,
            fontsize=plt_style["fontSize"] - 0.5,
        )

if np.isfinite(preMeanObs) and abs(preMeanObs) > 1e-6:
    fracText = f"Displacement / observed = {100 * preMeanEst / preMeanObs:.0f}%"
else:
    fracText = "Displacement / observed = NaN"

ax.text(
    0.99,
    0.94,
    fracText,
    transform=ax.transAxes,
    ha="right",
    va="top",
    bbox=dict(facecolor="white", edgecolor="none", pad=4),
    fontsize=plt_style["fontSize"] - 0.5,
)
style_axis(ax, plt_style)


# ============================================================
# (f) DUACS skill Fig b
# Pre-onset DUACS SLA bar
# ============================================================

ax = axes[5]
Cand = SK_Cand

B_sla = np.full(len(GroupList), np.nan)
SEM_sla = np.full(len(GroupList), np.nan)

if "DUACS_SLA_pre_z" not in Cand.columns:
    raise KeyError("SK.Cand does not contain DUACS_SLA_pre_z.")

for ig, group_name in enumerate(GroupList):
    idx = Cand["Group"] == group_name
    x = pd.to_numeric(Cand.loc[idx, "DUACS_SLA_pre_z"], errors="coerce").to_numpy(dtype=float)
    x = x[np.isfinite(x)]
    B_sla[ig] = np.nanmean(x) if x.size else np.nan
    SEM_sla[ig] = safe_sem(x)

xpos = np.arange(1, len(GroupList) + 1)
ax.bar(
    xpos,
    B_sla,
    width=0.68,
    color=GroupColors,
    edgecolor=[0.25, 0.25, 0.25],
    linewidth=0.7,
)
ax.errorbar(xpos, B_sla, yerr=SEM_sla, fmt="k.", linewidth=0.9, capsize=6)
ax.axhline(0, color="k", linestyle=":", linewidth=1.0)
ax.set_xticks(xpos)
ax.set_xticklabels(GroupShort, rotation=20)
ax.set_ylabel("Mean DUACS SLA z, day -10 to -1")
ax.set_title("(f) Pre-onset DUACS SLA")
style_axis(ax, plt_style)


# ============================================================
# (g) DUACS skill Fig c
# ROC: true onset vs warm near-miss
# ============================================================

ax = axes[6]
ax.plot([0, 1], [0, 1], "k--", linewidth=0.9)

rocPreds = ["DUACS_SLA_pre_z", "T100_pre_z", "SLA_T100_score"]
rocLabels = ["DUACS SLA", "T100", "SLA + T100"]
rocColors = np.vstack([cSLA, cT100, cComb])

for ip, pred in enumerate(rocPreds):
    R = get_roc_entry(SK_ROCstore, "True vs warm near-miss", pred)
    if R is None:
        warnings.warn(f"ROCstore does not contain an entry for predictor: {pred}")
        continue

    try:
        fpr = array_from_field(R, "FPR")
        tpr = array_from_field(R, "TPR")
        auc = scalar_value(get_field(R, "AUC"))
    except Exception as exc:
        warnings.warn(f"Could not read ROC entry for {pred}: {exc}")
        continue

    ax.plot(
        fpr,
        tpr,
        "-",
        color=rocColors[ip],
        linewidth=plt_style["lineWidth"],
        label=f"{rocLabels[ip]} AUC={auc:.2f}",
    )

ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.set_title("(g) ROC: true onset vs warm near-miss")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.legend(loc="lower right", frameon=False)
style_axis(ax, plt_style)


# ============================================================
# (h) DUACS skill Fig d
# AUC bar
# ============================================================

ax = axes[7]
Skill = SK_Skill

plotComp = "True vs warm near-miss"
plotPreds = ["DUACS_SLA_pre_z", "T100_pre_z", "SLA_T100_score"]
plotLabs = ["DUACS SLA", "T100", "SLA+T100"]
plotCols = np.vstack([cSLA, cT100, cComb])

AUCvals = np.full(len(plotPreds), np.nan)
CIlo = np.full(len(plotPreds), np.nan)
CIhi = np.full(len(plotPreds), np.nan)

for ip, pred in enumerate(plotPreds):
    idx = (Skill["Comparison"].astype(str) == plotComp) & (Skill["Predictor"].astype(str) == pred)

    if idx.any():
        row = Skill.loc[idx].iloc[0]
        AUCvals[ip] = scalar_value(row["AUC"])
        if "AUC_CI_low" in Skill.columns:
            CIlo[ip] = scalar_value(row["AUC_CI_low"])
        if "AUC_CI_high" in Skill.columns:
            CIhi[ip] = scalar_value(row["AUC_CI_high"])
    else:
        warnings.warn(f"Cannot find AUC row for {pred}.")

xpos = np.arange(1, len(plotPreds) + 1)
ax.bar(
    xpos,
    AUCvals,
    width=0.66,
    color=plotCols,
    edgecolor=[0.25, 0.25, 0.25],
    linewidth=0.7,
)

errLow = AUCvals - CIlo
errHigh = CIhi - AUCvals
ax.errorbar(xpos, AUCvals, yerr=np.vstack([errLow, errHigh]), fmt="k.", linewidth=1.0, capsize=6)
ax.axhline(0.5, color="k", linestyle="--", linewidth=1.0)
ax.set_xticks(xpos)
ax.set_xticklabels(plotLabs, rotation=15)
ax.set_ylabel("AUC")
ax.set_title("(h) AUC against warm near-miss controls")
ax.set_ylim(0.3, 1.0)

for ip, val in enumerate(AUCvals, start=1):
    if np.isfinite(val):
        ax.text(
            ip,
            val + 0.035,
            f"{val:.2f}",
            ha="center",
            fontsize=plt_style["fontSize"] - 0.5,
        )

style_axis(ax, plt_style)


# ============================================================
# (i) DUACS skill Fig f
# True-onset fraction by DUACS SLA quartile
# ============================================================

ax = axes[8]
ProbSLA = SK_ProbSLA

if not ProbSLA.empty:
    ax.bar(
        numeric_col(ProbSLA, "Quartile"),
        numeric_col(ProbSLA, "TrueOnsetFraction"),
        width=0.65,
        color=cSLA,
        edgecolor=[0.25, 0.25, 0.25],
        linewidth=0.7,
    )
    ax.set_ylim(0, 1)
    ax.set_xlim(0.4, 4.6)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlabel("DUACS SLA precursor quartile")
    ax.set_ylabel("Fraction of true onsets")
else:
    ax.text(0.5, 0.5, "Not enough samples", transform=ax.transAxes, ha="center", va="center")

ax.set_title("(i) True-onset fraction by DUACS SLA")
style_axis(ax, plt_style)


# ============================================================
# 5. Figure title and export
# ============================================================

# Original MATLAB script has sgtitle commented out. Keep it commented here too.
# fig.suptitle(
#     "Mechanistic closure and satellite-observable precursor skill",
#     fontsize=18,
#     fontweight="bold",
#     fontname=plt_style["fontName"],
# )

outPNG = outDir / "Fig_mechanistic_closure_satellite_precursor_skill_3x3.png"
outTIF = outDir / "Fig_mechanistic_closure_satellite_precursor_skill_3x3.tif"
outPDF = outDir / "Fig_mechanistic_closure_satellite_precursor_skill_3x3.pdf"

fig.savefig(outPNG, dpi=600, facecolor="white")
fig.savefig(outTIF, dpi=600, facecolor="white")
fig.savefig(outPDF, facecolor="white")

print("\nSaved merged 3 x 3 figure:")
print(f"1) {outPNG}")
print(f"2) {outTIF}")
print(f"3) {outPDF}")
print("\nFinished.")
