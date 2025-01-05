from django.urls import path
from api.views import (
    CheckPredictionLock,
    CheckCalculateLock,
    SensorList,
    SensorEnergyPrediction,
    SensorEnergyCalculation,
)

app_name = "api"

urlpatterns = [
    path("sensors/", SensorList.as_view(), name="sensor-list"),
    path(
        "energy/prediction/",
        SensorEnergyPrediction.as_view(),
        name="sensor-energy-prediction",
    ),
    path(
        "energy/prediction/status/",
        CheckPredictionLock.as_view(),
        name="prediction-status",
    ),
    path(
        "energy/calculation/",
        SensorEnergyCalculation.as_view(),
        name="sensor-energy-calculation",
    ),
    path(
        "energy/calculation/status/",
        CheckCalculateLock.as_view(),
        name="calculation-status",
    ),
]
