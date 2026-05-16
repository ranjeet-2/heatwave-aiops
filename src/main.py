!pip install earthengine-api geemap

import ee
import geemap

ee.Authenticate()
ee.Initialize(
    project = "ee-ranjeetramchandraug20",
    opt_url='https://earthengine-highvolume.googleapis.com'
)



map = geemap.Map()
map

roi = map.draw_last_feature.geometry()
roi

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

Map = geemap.Map(center=[29.87, 77.89], zoom=8)
Map.addLayer(current.clip(roi), {'min': 25, 'max': 50}, 'Current LST')
Map.addLayer(anomaly.clip(roi), {'min': -5, 'max': 5}, 'Anomaly')
Map.addLayer(heatwave.selfMask().clip(roi), {'palette': ['red']}, 'Heatwave')
Map

stats = current.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=roi,
    scale=1000,
    maxPixels=1e13
)
print(stats.getInfo())

geemap.ee_export_image_to_drive(
    current.clip(roi),
    description='current_lst',
    folder='GEE_Outputs',
    region=roi,
    scale=1000
)

from sklearn.ensemble import IsolationForest
import numpy as np

series = np.array([35, 36, 35.5, 37, 36.2, 45]).reshape(-1, 1)
model = IsolationForest(contamination=0.1, random_state=42)
labels = model.fit_predict(series)
print(labels)

historical_mean = 38
current_mean = 43
std = 2
z = (current_mean - historical_mean) / std
print('Z-score:', z)

if z > 2:
    print('Concept drift detected')

def generate_alert(mean_temp, z):
    if z > 2:
        print(f'ALERT: Heatwave detected! Mean Temp = {mean_temp:.2f}°C, z = {z:.2f}')

generate_alert(current_mean, z)

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
recent_temps = np.array([39.1, 39.5, 40.2, 41.0, 41.3, 42.0, 42.5, 42.7, 43.1, 43.4])

X = np.arange(len(recent_temps)).reshape(-1, 1)
y = recent_temps

model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X, y)

# Predict next 3 days
future_X = np.arange(len(recent_temps), len(recent_temps) + 3).reshape(-1, 1)
predictions = model.predict(future_X)

for i, temp in enumerate(predictions, start=1):
    print(f'Day +{i} predicted temperature: {temp:.2f} °C')

pred_temp = predictions[0]

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

import pandas as pd
from datetime import datetime

record = pd.DataFrame([{
    'timestamp': datetime.utcnow().isoformat(),
    'current_mean_temp': current_mean,
    'predicted_next_day_temp': pred_temp,
    'z_score': z,
    'risk': risk
}])

record.to_csv('daily_heatwave_report.csv', index=False)

!pip install schedule

import schedule
import time
from datetime import datetime

def run_pipeline():
    print('=' * 60)
    print('Running Geospatial AIOps Pipeline at', datetime.utcnow())
    print('=' * 60)

    # 1. Fetch latest EO data
    # 2. Compute LST and anomalies
    # 3. Predict next 1-3 days
    # 4. Detect concept drift
    # 5. Classify risk
    # 6. Generate alerts
    # 7. Save outputs

    print('Pipeline completed successfully')

# Run every 6 hours (matching GFS forecast cycle)
schedule.every(6).hours.do(run_pipeline)

# For Colab demonstration
run_pipeline()

# Optional continuous loop (uncomment for long-running environments)
# while True:
#     schedule.run_pending()
#     time.sleep(60)


def main():
    print("Running Geospatial AIOps Pipeline...")
    # Paste all your code here

if __name__ == "__main__":
    main()
