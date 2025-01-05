from rest_framework import serializers
from .models import Sensor, Energy, PowerPrediction
import pandas as pd


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = "__all__"


class EnergySerializer(serializers.ModelSerializer):
    class Meta:
        model = Energy
        fields = "__all__"


class PowerPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerPrediction
        fields = "__all__"


class SensorEnergySerializer(serializers.Serializer):
    sensor = serializers.CharField(required=True)
    date = serializers.DateField(required=False, input_formats=["%Y-%m-%d"])

    def validate_predicted_date(self, value):
        if value:
            try:
                pd.to_datetime(value)
            except Exception as e:
                raise serializers.ValidationError(
                    "Invalid 'date' format. Use YYYY-MM-DD."
                )
        return value
