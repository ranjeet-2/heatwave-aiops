import streamlit as st
import pandas as pd
import os
import rasterio
import matplotlib.pyplot as plt

st.set_page_config(page_title="Geospatial AIOps Heatwave Dashboard", layout="wide")

st.title("🔥 Geospatial AIOps Heatwave Monitoring Dashboard")
st.write("Real-time heatwave monitoring using Earth Observation and AIOps")

csv_path = "outputs/daily_heatwave_report.csv"

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    latest = df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Current Mean Temp (°C)", f"{latest['current_mean_temp']:.2f}")
    col2.metric("Predicted Next Day Temp (°C)", f"{latest['predicted_next_day_temp']:.2f}")
    col3.metric("Z-Score", f"{latest['z_score']:.2f}")
    col4.metric("Risk Level", latest['risk'])

    st.subheader("Latest Report")
    st.dataframe(df)

    st.subheader("Temperature Trend")
    st.line_chart(df[["current_mean_temp", "predicted_next_day_temp"]])

    # ======================================================
    # Spatial Maps
    # ======================================================
    st.subheader("Spatial Heatwave Maps")

    def show_tif(path, title):
        if os.path.exists(path):
            with rasterio.open(path) as src:
                data = src.read(1)

            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(data)
            ax.set_title(title)
            plt.colorbar(im, ax=ax)

            st.pyplot(fig)
        else:
            st.info(f"{title} not found yet.")

    show_tif("outputs/current_lst.tif", "Current Land Surface Temperature")
    show_tif("outputs/anomaly.tif", "Temperature Anomaly")
    show_tif("outputs/heatwave_mask.tif", "Heatwave Mask")

    if latest["risk"] in ["Severe", "Extreme"]:
        st.error(f"⚠️ Heatwave Alert: {latest['risk']}")
    elif latest["risk"] == "Moderate":
        st.warning("⚠️ Moderate heat stress")
    else:
        st.success("✅ Normal conditions")

else:
    st.warning("No output file found yet. Run GitHub Actions first.")
