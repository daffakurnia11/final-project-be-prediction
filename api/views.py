import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from datetime import timedelta
from .models import Sensor, Energy, PowerPrediction
from .serializers import (
    SensorSerializer,
    EnergySerializer,
    SensorEnergySerializer,
)
from django.core.cache import cache
from .utils import predict_energy, calculate_energy


class SensorList(generics.ListAPIView):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer

    def get_queryset(self):
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        return Sensor.objects.filter(created_at__gte=five_minutes_ago).order_by(
            "-created_at"
        )


class CheckPredictionLock(APIView):
    def get(self, request, *args, **kwargs):
        lock_key = "sensor_energy_prediction_lock"
        lock_status = cache.get(lock_key)

        is_prediction_running = lock_status is not None

        return Response(
            {
                "message": (
                    "Prediction process is currently running."
                    if is_prediction_running
                    else "Prediction process is not running."
                ),
                "is_prediction_running": is_prediction_running,
            },
            status=status.HTTP_200_OK,
        )


class CheckCalculateLock(APIView):
    def get(self, request, *args, **kwargs):
        lock_key = "sensor_energy_calculation_lock"
        lock_status = cache.get(lock_key)

        is_calculation_running = lock_status is not None

        return Response(
            {
                "message": (
                    "Calculation process is currently running."
                    if is_calculation_running
                    else "Calculation process is not running."
                ),
                "is_calculation_running": is_calculation_running,
            },
            status=status.HTTP_200_OK,
        )


class SensorEnergyPrediction(APIView):
    def post(self, request, *args, **kwargs):
        lock_key = "sensor_energy_prediction_lock"

        if cache.get(lock_key):
            return Response(
                {
                    "error": "Prediction process is already running. Please try again later."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.set(lock_key, True, timeout=600)

        try:
            serializer = SensorEnergySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            sensor_name = serializer.validated_data["sensor"]
            selected_date = serializer.validated_data.get("date", None)

            if not selected_date:
                selected_date = timezone.now().date()

            print("Selected date        :", selected_date)
            print("Sensor name          :", sensor_name)

            if not Energy.objects.filter(
                name=sensor_name, date=selected_date, predicted_energy__isnull=False
            ).exists():
                print("Predicting energy...")
                total_energy_predicted, predicted_data_rescaled = predict_energy(
                    sensor_name=sensor_name, selected_date=selected_date
                )

                energy_prediction = Energy.objects.filter(
                    name=sensor_name,
                    date=selected_date,
                ).first()

                if not energy_prediction:
                    energy_prediction = Energy(
                        name=sensor_name,
                        date=selected_date,
                        predicted_energy=total_energy_predicted,
                    )
                    energy_prediction.save()
                else:
                    energy_prediction.predicted_energy = total_energy_predicted
                    energy_prediction.save()

                power_predictions = [
                    PowerPrediction(energy=energy_prediction, power=predicted_power)
                    for predicted_power in predicted_data_rescaled.flatten()
                ]
                PowerPrediction.objects.bulk_create(power_predictions)

                return Response(status=status.HTTP_201_CREATED)

            else:
                return Response(
                    {
                        "error": f"Energy prediction for {sensor_name} on {selected_date} already exists."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        finally:
            cache.delete(lock_key)


class SensorEnergyCalculation(APIView):
    def post(self, request, *args, **kwargs):
        lock_key = "sensor_energy_calculation_lock"

        if cache.get(lock_key):
            return Response(
                {
                    "error": "Calculation process is already running. Please try again later."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.set(lock_key, True, timeout=600)

        try:
            serializer = SensorEnergySerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            sensor_name = serializer.validated_data["sensor"]
            selected_date = serializer.validated_data.get("date", None)

            if not selected_date:
                selected_date = timezone.now().date()

            print("Selected date        :", selected_date)
            print("Sensor name          :", sensor_name)

            if not Energy.objects.filter(
                name=sensor_name, date=selected_date, calculated_energy__isnull=False
            ).exists():
                print("Calculating energy...")
                total_energy_calculated = calculate_energy(
                    sensor_name=sensor_name, selected_date=selected_date
                )

                energy_calculation = Energy.objects.filter(
                    name=sensor_name,
                    date=selected_date,
                ).first()

                if not energy_calculation:
                    energy_calculation = Energy(
                        name=sensor_name,
                        date=selected_date,
                        calculated_energy=total_energy_calculated,
                    )
                    energy_calculation.save()
                else:
                    energy_calculation.calculated_energy = total_energy_calculated
                    energy_calculation.save()

                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {
                        "error": f"Energy calculation for {sensor_name} on {selected_date} already exists."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        finally:
            cache.delete(lock_key)
