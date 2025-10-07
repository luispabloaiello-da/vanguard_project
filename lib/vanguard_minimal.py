
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# Matplotlib: no specific style/colors set as requested
matplotlib.use("Agg")

OUTDIR = Path("./vanguard_minimal_outputs")
OUTDIR.mkdir(parents=True, exist_ok=True)

def _to_num(s):
    return pd.to_numeric(s, errors="coerce")

def _ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = _to_num(df[c])
    return df

def build_available_groups(ns):
    groups = {}
    for name, var in [("Variation", "df_demo_variation"), ("Test", "df_demo_test"), ("Control", "df_demo_control")]:
        df = ns.get(var, None)
        if isinstance(df, pd.DataFrame) and len(df)>0:
            groups[name] = df.copy()
    # normalize numerics
    num_cols = ["clnt_age","clnt_tenure_yr","num_accts","bal","logons_6_mnth","calls_6_mnth"]
    for k in groups:
        groups[k] = _ensure_numeric(groups[k], num_cols)
    return groups

def freq_table_num_accts(groups: dict) -> pd.DataFrame | None:
    frames = []
    for gname, gdf in groups.items():
        if "num_accts" not in gdf.columns: 
            continue
        vc = gdf["num_accts"].value_counts(dropna=False).sort_index()
        perc = (vc/vc.sum()*100.0).round(2)
        frames.append(pd.DataFrame({"num_accts": vc.index, f"{gname}_count": vc.values, f"{gname}_perc": perc.values}))
    if not frames:
        return None
    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on="num_accts", how="outer")
    return out.sort_values("num_accts")

def summarize_groups(groups: dict, vars_list: list[str]) -> pd.DataFrame:
    rows = []
    for gname, gdf in groups.items():
        for v in vars_list:
            if v not in gdf.columns: 
                continue
            s = pd.to_numeric(gdf[v], errors="coerce").dropna()
            if len(s)==0: 
                continue
            q1, med, q3 = s.quantile([0.25,0.5,0.75])
            rows.append({"group": gname, "variable": v, "n": int(s.size),
                         "median": float(med), "Q1": float(q1), "Q3": float(q3),
                         "IQR": float(q3 - q1), "skew": float(s.skew())})
    return pd.DataFrame(rows)

def boxplot_by_group(groups: dict, var: str, title: str, filename: str) -> str | None:
    data, labels = [], []
    for gname, gdf in groups.items():
        if var in gdf.columns:
            arr = pd.to_numeric(gdf[var], errors="coerce").dropna().values
            if len(arr)>0:
                data.append(arr); labels.append(gname)
    if not data: return None
    fig = plt.figure(figsize=(6,4))
    plt.boxplot(data, labels=labels, showfliers=True)
    plt.title(title); plt.ylabel(var); plt.tight_layout()
    outpath = OUTDIR/filename
    plt.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return str(outpath)

def overlay_hist(groups: dict, var: str, filename: str, bins: int=30, title: str="") -> str | None:
    fig = plt.figure(figsize=(6,4))
    plotted = False
    for gname, gdf in groups.items():
        if var in gdf.columns:
            s = pd.to_numeric(gdf[var], errors="coerce").dropna().values
            if len(s)>0:
                plt.hist(s, bins=bins, alpha=0.5, label=gname)  # default colors
                plotted = True
    if not plotted: 
        plt.close(fig); return None
    plt.title(title); plt.xlabel(var); plt.ylabel("Count"); plt.legend(); plt.tight_layout()
    outpath = OUTDIR/filename
    plt.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return str(outpath)

def scatter_bal_vs_accounts(groups: dict, filename: str, title: str) -> str | None:
    fig = plt.figure(figsize=(6,4))
    plotted = False
    for gname, gdf in groups.items():
        if "bal" in gdf.columns and "num_accts" in gdf.columns:
            x = pd.to_numeric(gdf["num_accts"], errors="coerce")
            y = pd.to_numeric(gdf["bal"], errors="coerce")
            m = x.notna() & y.notna()
            if m.sum()>0:
                plt.scatter(x[m].values, y[m].values, alpha=0.4, label=gname, s=10)
                plotted = True
    if not plotted:
        plt.close(fig); return None
    plt.title(title); plt.xlabel("num_accts"); plt.ylabel("bal"); plt.legend(); plt.tight_layout()
    outpath = OUTDIR/filename
    plt.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return str(outpath)

def bar_logins_by_tenure_quantile(groups: dict, q: int=4, filename: str="bar_tenure_logins.png", title: str=""):
    rows = []
    for gname, gdf in groups.items():
        if "clnt_tenure_yr" not in gdf.columns or "logons_6_mnth" not in gdf.columns:
            continue
        ten = pd.to_numeric(gdf["clnt_tenure_yr"], errors="coerce")
        log = pd.to_numeric(gdf["logons_6_mnth"], errors="coerce")
        m = ten.notna() & log.notna()
        if m.sum()==0: 
            continue
        try:
            qbins = pd.qcut(ten[m], q, labels=False, duplicates="drop")
        except Exception:
            continue
        grp = pd.DataFrame({"q": qbins, "log": log[m]}).groupby("q")["log"].mean().reset_index()
        grp["group"] = gname
        rows.append(grp)
    if not rows:
        return None, None
    agg = pd.concat(rows, ignore_index=True)
    piv = agg.pivot(index="q", columns="group", values="log").sort_index()
    fig = plt.figure(figsize=(6,4))
    idx = np.arange(piv.shape[0])
    width = 0.8 / max(1, piv.shape[1])
    for i, col in enumerate(piv.columns):
        plt.bar(idx + i*width, piv[col].values, width=width, label=col)
    plt.xticks(idx + (piv.shape[1]-1)*width/2, [f"Q{int(i)+1}" for i in piv.index])
    plt.title(title); plt.ylabel("Mean logins (6m)"); plt.legend(); plt.tight_layout()
    outpath = OUTDIR/filename
    plt.savefig(outpath, dpi=150, bbox_inches="tight"); plt.close(fig)
    return str(outpath), agg

def generate_minimal_outputs(globals_ns: dict):
    groups = build_available_groups(globals_ns)
    if not groups:
        raise RuntimeError("No hay dataframes disponibles (df_demo_variation / df_demo_test / df_demo_control).")

    # 1) Tabla de frecuencias num_accts
    ft = freq_table_num_accts(groups)

    # 2) Resumen mediana/IQR/skew
    summary = summarize_groups(groups, ["bal","logons_6_mnth","calls_6_mnth","num_accts"])

    # 3) Gráficos (máximo, 5 figuras compactas)
    figs = {}
    p1 = boxplot_by_group(groups, "bal", "Balances por grupo (boxplot)", "box_bal.png")
    if p1: figs["box_bal"] = p1
    p2 = boxplot_by_group(groups, "calls_6_mnth", "Llamadas por grupo (boxplot)", "box_calls.png")
    if p2: figs["box_calls"] = p2
    p3 = overlay_hist(groups, "logons_6_mnth", "hist_logons.png", bins=30, title="Distribución de logins (6m) por grupo")
    if p3: figs["hist_logons"] = p3
    p4 = scatter_bal_vs_accounts(groups, "scatter_bal_num_accts.png", "Balance vs número de cuentas (por grupo)")
    if p4: figs["scatter_bal_num_accts"] = p4
    p5, agg = bar_logins_by_tenure_quantile(groups, q=4, filename="bar_tenure_logins.png", title="Logins medios por cuantil de Tenure (por grupo)")
    if p5: figs["bar_tenure_logins"] = p5

    # Guardar tablas
    if ft is not None:
        ft.to_csv(OUTDIR/"freq_num_accts.csv", index=False)
    summary.to_csv(OUTDIR/"summary_stats.csv", index=False)
    if 'agg' in locals() and isinstance(agg, pd.DataFrame):
        agg.to_csv(OUTDIR/"logins_by_tenure_quantile.csv", index=False)

    # Índice JSON para comodidad
    index = {
        "figures": figs,
        "tables": {
            "freq_num_accts": str((OUTDIR/"freq_num_accts.csv").resolve()) if ft is not None else None,
            "summary_stats": str((OUTDIR/"summary_stats.csv").resolve()),
            "logins_by_tenure_quantile": str((OUTDIR/"logins_by_tenure_quantile.csv").resolve()) if 'agg' in locals() and isinstance(agg, pd.DataFrame) else None
        }
    }
    with open(OUTDIR/"index.json","w") as f:
        import json; json.dump(index, f, indent=2)

    return groups, ft, summary, figs

# Helper para ejecución directa dentro de un notebook: 
# >> from vanguard_minimal import run_here
# >> out = run_here(globals())
def run_here(globals_ns: dict):
    return generate_minimal_outputs(globals_ns)
