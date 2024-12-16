from django.urls import path
from api.views import SensorList, SensorEnergyPrediction

app_name = "api"

urlpatterns = [
    path("sensors/", SensorList.as_view(), name="sensor-list"),
    path(
        "sensors/energy_prediction/",
        SensorEnergyPrediction.as_view(),
        name="sensor-energy-prediction",
    ),
]
