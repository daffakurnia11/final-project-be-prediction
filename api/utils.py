# utils.py
import os
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from django.conf import settings
from .models import Sensor
from datetime import timedelta
from rest_framework.response import Response
from rest_framework import status


def load_model(sensor_name: str):
    model_path = os.path.join(settings.MODEL_STORAGE_PATH, f"{sensor_name}_model.h5")
    try:
        model = tf.keras.models.load_model(model_path)
        return model
    except Exception:
        raise FileNotFoundError(f"Model for sensor '{sensor_name}' not found.")


def create_sequences(data: np.array, time_steps: int = 24):
    X = []
    for i in range(len(data) - time_steps):
        X.append(data[i : i + time_steps])
    return np.array(X)


def predict_energy(sensor_name, selected_date):
    predicted_dataset = selected_date - timedelta(days=0)

    sensor_data = Sensor.objects.filter(
        created_at__date=predicted_dataset, name=sensor_name
    ).order_by("created_at")

    if not sensor_data:
        return Response(
            {"error": f"No sensor data available for {selected_date}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    first_row = sensor_data.first().created_at
    last_row = sensor_data.last().created_at
    print(f"Predicting {sensor_name} from {first_row} to {last_row}...")

    data_prediction = pd.DataFrame(list(sensor_data.values("created_at", "power")))
    data_prediction.set_index("created_at", inplace=True)

    scaler = MinMaxScaler(feature_range=(0, 1))
    data_prediction_scaled = scaler.fit_transform(data_prediction[["power"]])

    X_test = create_sequences(data_prediction_scaled)
    X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

    model = load_model(sensor_name)
    predicted_data = model.predict(X_test)
    predicted_data_rescaled = scaler.inverse_transform(predicted_data.reshape(-1, 1))

    total_energy_predicted = 0
    predicted_average_interval = (
        data_prediction.index.to_series().diff().dt.total_seconds().mean() / 3600
    )  # hours

    for predicted_power in predicted_data_rescaled.flatten():
        predicted_energy_value = (
            predicted_power * predicted_average_interval
        ) / 1000  # kWh
        total_energy_predicted += predicted_energy_value

    return total_energy_predicted, predicted_data_rescaled


def calculate_energy(sensor_name, selected_date):
    sensor_data = Sensor.objects.filter(
        created_at__date=selected_date, name=sensor_name
    ).order_by("created_at")

    if not sensor_data:
        return Response(
            {"error": f"No sensor data available for {selected_date}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    first_row = sensor_data.first().created_at
    last_row = sensor_data.last().created_at
    print(f"Calculating energy for {sensor_name} from {first_row} to {last_row}...")

    data_calculation = pd.DataFrame(list(sensor_data.values("created_at", "power")))
    data_calculation.set_index("created_at", inplace=True)

    total_energy_calculated = 0
    calculated_average_interval = (
        data_calculation.index.to_series().diff().dt.total_seconds().mean() / 3600
    )  # hours
    print(f"Average interval: {calculated_average_interval} hours")

    for sensor in sensor_data:
        calculated_energy_value = (
            sensor.power * calculated_average_interval
        ) / 1000  # kWh
        total_energy_calculated += calculated_energy_value

    return total_energy_calculated
