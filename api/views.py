import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from datetime import timedelta
from .models import Sensor, SensorPrediction, PowerPrediction
from .serializers import SensorSerializer, SensorEnergyPredictionSerializer
import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from django.conf import settings


class SensorList(generics.ListAPIView):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer

    def get_queryset(self):
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        return Sensor.objects.filter(created_at__gte=five_minutes_ago).order_by(
            "-created_at"
        )


class SensorEnergyPrediction(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SensorEnergyPredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sensor_name = serializer.validated_data["sensor"]
        predicted_date = serializer.validated_data.get("predicted_date", None)

        if not predicted_date:
            predicted_date = (timezone.now() - timedelta(days=1)).date()

        if SensorPrediction.objects.filter(
            name=sensor_name, prediction_date=predicted_date
        ).exists():
            return Response(
                {
                    "error": f"Sensor prediction for {sensor_name} on {predicted_date} already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        print("Predicted date   :", predicted_date)
        print("Sensor name      :", sensor_name)

        sensor_data = Sensor.objects.filter(
            created_at__date=predicted_date, name=sensor_name
        ).order_by("created_at")

        if not sensor_data:
            return Response(
                {"error": f"No sensor data available for {predicted_date}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        test_data = pd.DataFrame(list(sensor_data.values("created_at", "power")))
        test_data.set_index("created_at", inplace=True)

        scaler = MinMaxScaler(feature_range=(0, 1))
        test_data_scaled = scaler.fit_transform(test_data[["power"]])

        def create_sequences(data, time_steps=24):
            X = []
            for i in range(len(data) - time_steps):
                X.append(data[i : i + time_steps])
            return np.array(X)

        X_test = create_sequences(test_data_scaled, time_steps=24)
        X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

        print(f"Predicting {sensor_name}...")
        model_path = os.path.join(
            settings.MODEL_STORAGE_PATH, f"{sensor_name}_model.h5"
        )

        try:
            model = tf.keras.models.load_model(model_path)
        except Exception:
            return Response(
                {"error": f"Model for sensor '{sensor_name}' not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        predicted_data = model.predict(X_test)
        predicted_data_rescaled = scaler.inverse_transform(
            predicted_data.reshape(-1, 1)
        )

        total_energy_predicted = 0
        test_average_interval = (
            test_data.index.to_series().diff().dt.total_seconds().mean() / 3600
        )
        for predicted_power in predicted_data_rescaled.flatten():
            predicted_energy_value = (predicted_power * test_average_interval) / 1000
            total_energy_predicted += predicted_energy_value

        sensor_prediction = SensorPrediction.objects.create(
            name=sensor_name,
            prediction_date=predicted_date,
            prediction_power=total_energy_predicted,
        )

        print("Saving power predictions...")
        power_predictions = []
        for predicted_power in predicted_data_rescaled.flatten():
            predicted_energy_value = (predicted_power * test_average_interval) / 1000
            total_energy_predicted += predicted_energy_value

            power_predictions.append(
                PowerPrediction(
                    sensor_prediction=sensor_prediction, power=predicted_power
                )
            )

        PowerPrediction.objects.bulk_create(power_predictions)

        result = {
            "sensor_name": sensor_name,
            "predicted_date": predicted_date.strftime("%Y-%m-%d"),
            "total_energy_predicted_kWh": round(total_energy_predicted, 2),
            "predicted_power": predicted_data_rescaled.flatten().tolist(),
        }

        return Response(result, status=status.HTTP_200_OK)
