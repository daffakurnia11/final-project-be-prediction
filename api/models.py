from django.db import models
import uuid


class Sensor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    name = models.TextField()
    voltage = models.FloatField()
    current = models.FloatField()
    power = models.FloatField()
    power_factor = models.FloatField()
    frequency = models.FloatField()
    energy = models.FloatField()
    apparent_power = models.FloatField()
    reactive_power = models.FloatField()

    class Meta:
        db_table = "sensor_electrics"

    def __str__(self):
        return f"Sensor {self.name} ({self.id})"


class Energy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    name = models.TextField()
    date = models.TextField()
    calculated_energy = models.FloatField(null=True, blank=True)
    predicted_energy = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "energies"

    def __str__(self):
        return f"Calculation for {self.name} on {self.date}"


class PowerPrediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    energy = models.ForeignKey(
        Energy,
        related_name="power_predictions",
        on_delete=models.CASCADE,
    )
    power = models.FloatField()

    class Meta:
        db_table = "power_predictions"

    def __str__(self):
        return (
            f"Power prediction for {self.energy.name} on {self.energy.prediction_date}"
        )
