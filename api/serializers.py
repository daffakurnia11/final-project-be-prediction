from rest_framework import serializers
from .models import Sensor, SensorPrediction, PowerPrediction
import pandas as pd


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = "__all__"


class SensorPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorPrediction
        fields = "__all__"


class PowerPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerPrediction
        fields = "__all__"


class SensorEnergyPredictionSerializer(serializers.Serializer):
    sensor = serializers.CharField(required=True)
    predicted_date = serializers.DateField(required=False, input_formats=["%Y-%m-%d"])

    def validate_predicted_date(self, value):
        if value:
            try:
                pd.to_datetime(value)
            except Exception as e:
                raise serializers.ValidationError(
                    "Invalid 'predicted_date' format. Use YYYY-MM-DD."
                )
        return value
