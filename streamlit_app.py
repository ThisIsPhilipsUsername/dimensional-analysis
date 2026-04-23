import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from PIL import Image
import streamlit as st


st.set_page_config(page_title="Taylor Blast Wave Explorer", layout="wide")

SCALE_BAR_PIXELS = 42
METRES_PER_PIXEL = 100 / SCALE_BAR_PIXELS
RHO_AIR = 1.2
TOLERANCE_PX = 1.5
PRACTICAL_YIELD_KT = 20.0

# 191 ms frame calibration (measured from the photograph's own scale bar)
FRAME_IMAGE      = "191ms.png"
FRAME_T_MS       = 19.1
FRAME_SCALE_X0   = 103      # left tick of the 100 m bar in 191ms.png
FRAME_SCALE_X1   = 178      # right tick
FRAME_SCALE_Y    = 42       # row of the scale bar line
FRAME_MPX        = 100 / (FRAME_SCALE_X1 - FRAME_SCALE_X0)   # m / px
FRAME_CX         = 141.4    # blast centre x (px)
FRAME_CY         = 196.75   # blast centre y (px)


def build_data(measurement_mode: str) -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "time_ms": [15.1, 17.0, 18.8, 20.7, 22.6, 24.4],
            "radius_px_sides": [58, 60, 62, 64, 66, 68],
            "radius_px_top": [40, 41, 42, 43, 44, 45],
        }
    )

    radius_col = f"radius_px_{measurement_mode}"
    data["time_s"] = data["time_ms"] / 1000
    data["radius_px"] = data[radius_col]
    data["radius_m"] = data["radius_px"] * METRES_PER_PIXEL

    k_fit = np.sum(data["radius_px"] * data["time_ms"] ** 0.4) / np.sum(
        data["time_ms"] ** 0.8
    )
    data["k_fit"] = k_fit
    data["radius_px_pred"] = k_fit * data["time_ms"] ** 0.4
    data["residual_px"] = data["radius_px"] - data["radius_px_pred"]
    data["abs_error_px"] = np.abs(data["residual_px"])
    data["radius_m_pred"] = data["radius_px_pred"] * METRES_PER_PIXEL

    data["E_est_J"] = RHO_AIR * data["radius_m"] ** 5 / data["time_s"] ** 2
    data["E_est_kilotons_TNT"] = data["E_est_J"] / 4.184e12
    return data


def plot_best_fit(data: pd.DataFrame, measurement_mode: str):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(data["time_ms"], data["radius_px"], label=f"measured {measurement_mode}")
    ax.plot(data["time_ms"], data["radius_px_pred"], label="best-fit theory")
    ax.fill_between(
        data["time_ms"],
        data["radius_px_pred"] - TOLERANCE_PX,
        data["radius_px_pred"] + TOLERANCE_PX,
        alpha=0.2,
        label=f"prediction +/- {TOLERANCE_PX:.1f} px",
    )
    ax.set_xlabel("time / ms")
    ax.set_ylabel("radius / px")
    ax.set_title(f"Best-fit r = k t^(2/5) using {measurement_mode} measurements")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return fig


def plot_frame_overlay(radius_m: float, r_theory_m: float) -> plt.Figure:
    frame = np.array(Image.open(FRAME_IMAGE).convert("RGB"))
    h, w = frame.shape[:2]

    r_px        = radius_m   / FRAME_MPX
    r_theory_px = r_theory_m / FRAME_MPX

    fig, ax = plt.subplots(figsize=(6.2, 5.0))
    ax.imshow(frame)

    # user-chosen radius arc
    ax.add_patch(Arc(
        (FRAME_CX, FRAME_CY), 2 * r_px, 2 * r_px,
        theta1=180, theta2=360, color="tab:orange", linewidth=2.5,
    ))
    ax.plot([FRAME_CX, FRAME_CX + r_px], [FRAME_CY, FRAME_CY],
            color="cyan", ls="--", lw=1.8)
    ax.plot([FRAME_CX, FRAME_CX], [FRAME_CY, FRAME_CY - r_px],
            color="cyan", ls="--", lw=1.8)

    # theoretical radius (dotted yellow arc for reference)
    ax.add_patch(Arc(
        (FRAME_CX, FRAME_CY), 2 * r_theory_px, 2 * r_theory_px,
        theta1=180, theta2=360, color="yellow", linewidth=1.5, linestyle="dotted",
    ))

    # 100 m scale bar overlay
    ax.plot([FRAME_SCALE_X0, FRAME_SCALE_X1], [FRAME_SCALE_Y, FRAME_SCALE_Y],
            color="lime", lw=2.5)
    for x in (FRAME_SCALE_X0, FRAME_SCALE_X1):
        ax.plot([x, x], [FRAME_SCALE_Y - 5, FRAME_SCALE_Y + 5], color="lime", lw=2.5)
    ax.text(
        (FRAME_SCALE_X0 + FRAME_SCALE_X1) / 2, FRAME_SCALE_Y - 7, "100 m",
        color="lime", fontsize=9, ha="center", va="bottom", fontweight="bold",
    )

    ax.text(
        4, 4, f"r = {radius_m:.0f} m",
        color="white", fontsize=10, va="top",
        bbox=dict(fc="black", alpha=0.6, ec="none"),
    )

    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    ax.set_title(f"19.1 ms frame  —  orange: selected  |  yellow dotted: theory ({r_theory_m:.0f} m)")
    return fig


# ── app ──────────────────────────────────────────────────────────────────────

st.title("Taylor Blast Wave: Top vs Side Radius")
st.write(
    "Toggle between measuring the fireball radius to the **sides** or to the **top**. "
    "The app updates the best-fit theoretical curve with fixed $t^{2/5}$ scaling and the "
    "resulting kiloton estimate, then compares that theory-based estimate with the practical "
    "reference value of 20 kt."
)

measurement_mode = st.radio(
    "Measurement mode",
    options=["sides", "top"],
    horizontal=True,
)

data = build_data(measurement_mode)
k_fit       = data["k_fit"].iloc[0]
k_fit_m     = k_fit * METRES_PER_PIXEL                    # m / ms^0.4
r_theory_m  = k_fit_m * FRAME_T_MS ** 0.4                # theoretical radius at 19.1 ms

mean_kt     = data["E_est_kilotons_TNT"].mean()
median_kt   = data["E_est_kilotons_TNT"].median()
mae_px      = data["abs_error_px"].mean()
within_tol  = int((data["abs_error_px"] <= TOLERANCE_PX).sum())
mean_delta_kt  = mean_kt - PRACTICAL_YIELD_KT
mean_delta_pct = 100 * mean_delta_kt / PRACTICAL_YIELD_KT

metric_cols = st.columns(5)
metric_cols[0].metric("Theory estimate", f"{mean_kt:.2f} kt TNT")
metric_cols[1].metric("Practical yield", f"{PRACTICAL_YIELD_KT:.2f} kt TNT")
metric_cols[2].metric("Theory vs practical", f"{mean_delta_kt:+.2f} kt", f"{mean_delta_pct:+.1f}%")
metric_cols[3].metric("Median estimated yield", f"{median_kt:.2f} kt TNT")
metric_cols[4].metric("Mean absolute fit error", f"{mae_px:.2f} px")

st.metric("Points within tolerance", f"{within_tol}/{len(data)}")

st.caption(
    f"Calibration: 100 m = {SCALE_BAR_PIXELS} px, so 1 px = {METRES_PER_PIXEL:.2f} m. "
    f"Tolerance band = +/- {TOLERANCE_PX:.1f} px."
)

st.info(
    f"Practical comparison uses a reference yield of {PRACTICAL_YIELD_KT:.0f} kt. "
    f"With the current {measurement_mode} measurements, the theory-based mean estimate is "
    f"{mean_kt:.2f} kt."
)

summary = data[
    ["time_ms", "radius_px", "radius_px_pred", "residual_px", "radius_m", "E_est_kilotons_TNT"]
].copy()
summary.columns = [
    "time_ms", "measured_radius_px", "predicted_radius_px",
    "residual_px", "measured_radius_m", "estimated_kilotons_TNT",
]

tab_graph, tab_image, tab_explorer, tab_table = st.tabs(
    ["Graph", "Image", "Frame Explorer", "Summary"]
)

with tab_graph:
    st.pyplot(plot_best_fit(data, measurement_mode))

with tab_image:
    try:
        image = Image.open("blast.png")
        st.image(image, caption="Explosion contact sheet")
    except FileNotFoundError:
        st.warning("Could not find blast.png in the current folder.")

with tab_explorer:
    st.subheader("19.1 ms frame — interactive blast radius & energy")
    st.write(
        "Drag the slider to resize the blast radius. "
        "The **yellow dotted arc** shows the theoretical prediction; "
        "the **orange arc** follows your slider. "
        "Energy scales as $E \\sim \\rho\\, r^5 / t^2$."
    )

    radius_m = st.slider(
        "Blast radius (m)",
        min_value=50, max_value=300,
        value=int(round(r_theory_m)),
        step=1,
    )

    t_s   = FRAME_T_MS / 1000
    E_J   = RHO_AIR * radius_m ** 5 / t_s ** 2
    E_kt  = E_J / 4.184e12
    E_theory_J  = RHO_AIR * r_theory_m ** 5 / t_s ** 2
    E_theory_kt = E_theory_J / 4.184e12

    col1, col2, col3 = st.columns(3)
    col1.metric("Selected radius",   f"{radius_m} m",       f"{radius_m - r_theory_m:+.0f} m vs theory")
    col2.metric("Estimated energy",  f"{E_kt:.1f} kt TNT",  f"{E_kt - E_theory_kt:+.1f} kt vs theory")
    col3.metric("Theory energy",     f"{E_theory_kt:.1f} kt TNT")

    # colour-coded energy gauge (green → red)
    MAX_GAUGE_KT = 120.0
    frac = min(E_kt / MAX_GAUGE_KT, 1.0)
    r_val = int(255 * frac)
    g_val = int(255 * (1 - frac))
    hex_color = f"#{r_val:02x}{g_val:02x}00"
    st.markdown(
        f"""
        <div style="background:#222;border-radius:6px;padding:4px 8px;margin-bottom:8px">
          <div style="width:{frac*100:.1f}%;background:{hex_color};
                      border-radius:4px;padding:4px 0;text-align:center;
                      color:white;font-weight:bold;font-size:14px;min-width:60px">
            {E_kt:.1f} kt
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Gauge max = {MAX_GAUGE_KT:.0f} kt  |  theory = {E_theory_kt:.1f} kt (yellow dotted arc)")

    try:
        fig = plot_frame_overlay(radius_m, r_theory_m)
        col_img, _ = st.columns([1, 1])
        with col_img:
            st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except FileNotFoundError:
        st.warning("Could not find 191ms.png in the current folder.")

with tab_table:
    st.subheader("Frame-by-frame summary")
    st.dataframe(summary, use_container_width=True)
