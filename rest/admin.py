from django.contrib import admin
from .models import Hero


# Register your models here.
@admin.register(Hero)
class HeroAdminModel(admin.ModelAdmin):
    search_fields = ["id", "name", "intelligence", "power", "strength", "speed"]
