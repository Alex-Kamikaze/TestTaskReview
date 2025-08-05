from django.db import models


# Create your models here.
class Hero(models.Model):
    """Данные о герое"""

    id = models.IntegerField(unique=True, primary_key=True, verbose_name="ID героя")
    name = models.CharField(
        max_length=1024, null=False, blank=False, verbose_name="Имя героя"
    )
    intelligence = models.IntegerField(
        blank=True, null=True, verbose_name="Интеллект героя"
    )
    strength = models.IntegerField(blank=True, null=True, verbose_name="Сила героя")
    speed = models.IntegerField(blank=True, null=True, verbose_name="Скорость героя")
    power = models.IntegerField(blank=True, null=True, verbose_name="Мощь героя")

    class Meta:
        verbose_name = "Герой"
        verbose_name_plural = "Герои"
        ordering = ["id"]
        indexes = [
            models.Index(
                fields=["name", "intelligence", "strength", "speed", "power"],
                name="parameters_search_index",
            )
        ]

    def __str__(self):
        return self.name
