import streamlit as st
import pandas as pd
import os
import rasterio
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Geospatial AIOps Heatwave Dashboard",
    layout="wide"
)

st.title("🔥 Geospatial AIOps Heatwave Monitoring Dashboard")
st.markdown(
    """
    Real-time monitoring of heatwave conditions using:
    - Google Earth Engine
    - MODIS Land Surface Temperature
    - Machine Learning Forecasting
    - AIOps Automation
    """
)

csv_path = "outputs/daily_heatwave_report.csv"

if os.path.exists(csv_path):

    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    latest = df.iloc[-1]

    # =========================
    # KPI Metrics
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Current Mean Temp (°C)",
                f"{latest['current_mean_temp']:.2f}")

    col2.metric("Predicted Next Day (°C)",
                f"{latest['predicted_next_day_temp']:.2f}")

    col3.metric("Z-Score",
                f"{latest['z_score']:.2f}")

    col4.metric("Risk Level",
                latest["risk"])

    # =========================
    # Alert Banner
    # =========================
    if latest["risk"] in ["Severe", "Extreme"]:
        st.error(f"⚠️ Heatwave Alert: {latest['risk']}")
    elif latest["risk"] == "Moderate":
        st.warning("⚠️ Moderate heat stress")
    else:
        st.success("✅ Normal conditions")

    # =========================
    # Temperature Trend
    # =========================
    st.subheader("📈 Historical Temperature Trend")

    trend_df = df.set_index("timestamp")[
        ["current_mean_temp", "predicted_next_day_temp"]
    ]
    st.line_chart(trend_df)

    # =========================
    # Risk Distribution
    # =========================
    st.subheader("📊 Risk Distribution")
    st.bar_chart(df["risk"].value_counts())

    # =========================
    # Historical Table
    # =========================
    st.subheader("📋 Historical Records")
    st.dataframe(df, use_container_width=True)

    # Download CSV
    with open(csv_path, "rb") as f:
        st.download_button(
            "⬇ Download CSV",
            data=f,
            file_name="daily_heatwave_report.csv",
            mime="text/csv"
        )

    # =========================
    # Spatial Maps
    # =========================
    st.subheader("🗺 Spatial Heatwave Maps")

    def show_tif(path, title):
        if os.path.exists(path):
            with rasterio.open(path) as src:
                data = src.read(1)

            fig, ax = plt.subplots(figsize=(8, 5))
            im = ax.imshow(data)
            ax.set_title(title)
            ax.axis("off")
            plt.colorbar(im, ax=ax)
            st.pyplot(fig)
        else:
            st.info(f"{title} not available yet.")

    show_tif("outputs/current_lst.tif",
             "Current Land Surface Temperature")

    show_tif("outputs/anomaly.tif",
             "Temperature Anomaly")

    show_tif("outputs/heatwave_mask.tif",
             "Heatwave Mask")

else:
    st.warning("No output file found yet. Run GitHub Actions first.")
