import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import streamlit as st


st.set_page_config(page_title="Taylor Blast Wave Explorer", layout="wide")

SCALE_BAR_PIXELS = 42
METRES_PER_PIXEL = 100 / SCALE_BAR_PIXELS
RHO_AIR = 1.2
TOLERANCE_PX = 1.5
PRACTICAL_YIELD_KT = 20.0


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

    # Keep the theoretical scaling fixed at r = k t^(2/5) and fit only k.
    k_fit = np.sum(data["radius_px"] * data["time_ms"] ** 0.4) / np.sum(
        data["time_ms"] ** 0.8
    )
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
mean_kt = data["E_est_kilotons_TNT"].mean()
median_kt = data["E_est_kilotons_TNT"].median()
mae_px = data["abs_error_px"].mean()
within_tol = int((data["abs_error_px"] <= TOLERANCE_PX).sum())
mean_delta_kt = mean_kt - PRACTICAL_YIELD_KT
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
    [
        "time_ms",
        "radius_px",
        "radius_px_pred",
        "residual_px",
        "radius_m",
        "E_est_kilotons_TNT",
    ]
].copy()
summary.columns = [
    "time_ms",
    "measured_radius_px",
    "predicted_radius_px",
    "residual_px",
    "measured_radius_m",
    "estimated_kilotons_TNT",
]

tab_graph, tab_image, tab_table = st.tabs(["Graph", "Image", "Summary"])

with tab_graph:
    st.pyplot(plot_best_fit(data, measurement_mode))

with tab_image:
    try:
        image = Image.open("blast.png")
        st.image(image, caption="Explosion contact sheet")
    except FileNotFoundError:
        st.warning("Could not find blast.png in the current folder.")

with tab_table:
    st.subheader("Frame-by-frame summary")
    st.dataframe(summary, use_container_width=True)
