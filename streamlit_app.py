import streamlit as st
import pandas as pd
import os

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

    # =========================================================
    # Spatial Heatwave Maps Section
    # =========================================================
    st.subheader("Spatial Heatwave Maps")

    for file_name, title in [
        ("outputs/current_lst.png", "Current Land Surface Temperature"),
        ("outputs/anomaly.png", "Temperature Anomaly"),
        ("outputs/heatwave_mask.png", "Heatwave Mask")
    ]:
        if os.path.exists(file_name):
            st.image(
                file_name,
                caption=title,
                use_container_width=True
            )
        else:
            st.info(f"{title} image not found yet.")

    # =========================================================
    # Risk Alert Section
    # =========================================================
    if latest["risk"] in ["Severe", "Extreme"]:
        st.error(f"⚠️ Heatwave Alert: {latest['risk']}")
    elif latest["risk"] == "Moderate":
        st.warning("⚠️ Moderate heat stress")
    else:
        st.success("✅ Normal conditions")

else:
    st.warning("No output file found yet. Run GitHub Actions first.")
