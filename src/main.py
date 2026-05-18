import os
import requests

# Read secrets from GitHub Actions environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
EE_PROJECT_ID = os.getenv("EE_PROJECT_ID", "ee-ranjeetramchandraug20")

print("Checking GitHub Secrets...")
print("TELEGRAM_BOT_TOKEN loaded:", TELEGRAM_BOT_TOKEN is not None)
print("TELEGRAM_CHAT_ID loaded:", TELEGRAM_CHAT_ID is not None)
print("EE_PROJECT_ID:", EE_PROJECT_ID)


import json
from google.oauth2 import service_account
import ee
# import geemap
import os

EE_PROJECT_ID = os.getenv("EE_PROJECT_ID")
EE_SERVICE_ACCOUNT_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")

credentials_info = json.loads(EE_SERVICE_ACCOUNT_JSON)

credentials = service_account.Credentials.from_service_account_info(
    credentials_info,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

ee.Initialize(
    credentials=credentials,
    project=EE_PROJECT_ID,
    opt_url="https://earthengine-highvolume.googleapis.com"
)

roi = ee.Geometry.Polygon([
    [
        [77.881397, 29.857022],
        [77.881397, 29.875704],
        [77.910503, 29.875704],
        [77.910503, 29.857022],
        [77.881397, 29.857022],
    ]
])

from datetime import datetime, timedelta

end_date = datetime.utcnow().date()
start_date = end_date - timedelta(days=16)  # ensures at least one recent MODIS image

collection = (
    ee.ImageCollection('MODIS/061/MOD11A2')
    .filterDate(start_date.isoformat(), end_date.isoformat())
    .select('LST_Day_1km')
)

print('Using MODIS data from', start_date, 'to', end_date)

def to_celsius(img):
    return img.multiply(0.02).subtract(273.15).copyProperties(img, ['system:time_start'])

lst = collection.map(to_celsius)

hist = (
    ee.ImageCollection('MODIS/061/MOD11A2')
    .filterDate('2015-04-01', '2024-06-30')
    .select('LST_Day_1km')
    .map(to_celsius)
)

mean_img = hist.mean()
std_img = hist.reduce(ee.Reducer.stdDev())

current = lst.mean()

anomaly = current.subtract(mean_img)

zscore = anomaly.divide(std_img)

heatwave = zscore.gt(2)

# Map = geemap.Map(center=[29.87, 77.89], zoom=8)
# Map.addLayer(current.clip(roi), {'min': 25, 'max': 50}, 'Current LST')
# Map.addLayer(anomaly.clip(roi), {'min': -5, 'max': 5}, 'Anomaly')
# Map.addLayer(heatwave.selfMask().clip(roi), {'palette': ['red']}, 'Heatwave')
# Map

stats = current.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=roi,
    scale=1000,
    maxPixels=1e13
)

stats_dict = stats.getInfo()
print(stats_dict)

current_mean = list(stats_dict.values())[0]
print(f"Current Mean Temperature: {current_mean:.2f} °C")

# geemap.ee_export_image_to_drive(
#     current.clip(roi),
#     description='current_lst',
#     folder='GEE_Outputs',
#     region=roi,
#     scale=1000
# )

from sklearn.ensemble import IsolationForest
import numpy as np

series = np.array([35, 36, 35.5, 37, 36.2, 45]).reshape(-1, 1)
model = IsolationForest(contamination=0.1, random_state=42)
labels = model.fit_predict(series)
print(labels)

historical_mean = 38
std = 2
z = (current_mean - historical_mean) / std
print('Z-score:', z)

if z > 2:
    print('Concept drift detected')

def generate_alert(mean_temp, z, pred_temp, risk):
    """
    Generate and send Telegram alert when severe heatwave is detected.
    """

    if risk in ["Severe", "Extreme"]:
        message = (
            f"🔥 Heatwave Alert!\n\n"
            f"Current Mean Temperature: {mean_temp:.2f} °C\n"
            f"Predicted Next-Day Temperature: {pred_temp:.2f} °C\n"
            f"Z-Score: {z:.2f}\n"
            f"Risk Level: {risk}\n"
            f"Timestamp (UTC): {datetime.utcnow().isoformat()}"
        )

        print(message)

        # Send to Telegram
        send_telegram_alert(message)

    else:
        print(f"No alert. Risk level = {risk}")

def send_telegram_alert(message):
    """
    Send alert message to Telegram.
    Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from GitHub Secrets.
    """

    if TELEGRAM_BOT_TOKEN is None or TELEGRAM_CHAT_ID is None:
        print("Telegram credentials not found. Alert not sent.")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload, timeout=30)

        if response.status_code == 200:
            print("Telegram alert sent successfully.")
        else:
            print("Failed to send Telegram alert.")
            print(response.text)

    except Exception as e:
        print("Telegram sending error:", e)

def safe_run(func, retries=3):
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            print(f'Retry {i+1}:', e)
    print('Pipeline failed after retries')

import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Example extracted recent temperatures (replace with actual EO-derived time series)
# --------------------------------------------------
# Forecast using actual historical observations
# --------------------------------------------------
csv_path = "outputs/daily_heatwave_report.csv"

if os.path.exists(csv_path):
    hist_df = pd.read_csv(csv_path)

    if len(hist_df) >= 5:
        recent_temps = hist_df["current_mean_temp"].tail(20).values
    else:
        recent_temps = np.array([
            current_mean,
            current_mean - 0.5,
            current_mean + 0.3,
            current_mean - 0.2,
            current_mean
        ])
else:
    recent_temps = np.array([
        current_mean,
        current_mean - 0.5,
        current_mean + 0.3,
        current_mean - 0.2,
        current_mean
    ])

print("Recent temperatures used for forecasting:")
print(recent_temps)

X = np.arange(len(recent_temps)).reshape(-1, 1)
y = recent_temps

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42
)
model.fit(X, y)

future_X = np.arange(
    len(recent_temps),
    len(recent_temps) + 3
).reshape(-1, 1)

predictions = model.predict(future_X)

for i, temp in enumerate(predictions, start=1):
    print(f"Day +{i} predicted temperature: {temp:.2f} °C")

pred_temp = float(predictions[0])

def classify_risk(temp, z):
    if z > 3 or temp > 45:
        return 'Extreme'
    elif z > 2 or temp > 42:
        return 'Severe'
    elif z > 1:
        return 'Moderate'
    else:
        return 'Normal'

risk = classify_risk(pred_temp, z)
print('Forecast Risk:', risk)

generate_alert(
    mean_temp=current_mean,
    z=z,
    pred_temp=pred_temp,
    risk=risk
)

import pandas as pd
from datetime import datetime

record = pd.DataFrame([{
    'timestamp': datetime.utcnow().isoformat(),
    'current_mean_temp': current_mean,
    'predicted_next_day_temp': pred_temp,
    'z_score': z,
    'risk': risk
}])

os.makedirs("outputs", exist_ok=True)

csv_path = "outputs/daily_heatwave_report.csv"

if os.path.exists(csv_path):
    existing = pd.read_csv(csv_path)
    updated = pd.concat([existing, record], ignore_index=True)

    # Remove duplicate timestamps if any
    updated = updated.drop_duplicates(subset=["timestamp"], keep="last")
else:
    updated = record

updated.to_csv(csv_path, index=False)
print(f"Saved historical report to {csv_path}")

def export_map(image, filename):
    """
    Export Earth Engine image as GeoTIFF.
    If export fails due to permissions, continue without stopping pipeline.
    """
    import requests
    import os

    os.makedirs("outputs", exist_ok=True)

    try:
        url = image.clip(roi).getDownloadURL({
            "scale": 1000,
            "region": roi,
            "format": "GEO_TIFF"
        })

        response = requests.get(url, timeout=300)
        response.raise_for_status()

        with open(filename, "wb") as f:
            f.write(response.content)

        print(f"Saved: {filename}")

    except Exception as e:
        print(f"Map export failed for {filename}: {e}")
        print("Continuing pipeline without this map.")

export_map(current, "outputs/current_lst.tif")
export_map(anomaly, "outputs/anomaly.tif")
export_map(heatwave.selfMask(), "outputs/heatwave_mask.tif")

# export_map(current, "outputs/current_lst.png")
# export_map(anomaly, "outputs/anomaly.png")
# export_map(heatwave.selfMask(), "outputs/heatwave_mask.png")

# from datetime import datetime

# def run_pipeline():
#     print('=' * 60)
#     print('Running Geospatial AIOps Pipeline at', datetime.utcnow())
#     print('=' * 60)

#     # 1. Fetch latest EO data
#     # 2. Compute LST and anomalies
#     # 3. Predict next 1-3 days
#     # 4. Detect concept drift
#     # 5. Classify risk
#     # 6. Generate alerts
#     # 7. Save outputs

#     print('Pipeline completed successfully')

# Run every 6 hours (matching GFS forecast cycle)
# schedule.every(6).hours.do(run_pipeline)

# For Colab demonstration
# run_pipeline()

# Optional continuous loop (uncomment for long-running environments)
# while True:
#     schedule.run_pending()
#     time.sleep(60)


def main():
    print("=" * 60)
    print("Starting Geospatial AIOps Heatwave Pipeline")
    print("=" * 60)

    # Put the complete pipeline code here

    print("=" * 60)
    print("Pipeline completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
