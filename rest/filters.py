from django_filters import rest_framework as filters
from .models import Hero


class HeroFilter(filters.FilterSet):
    class Meta:
        model = Hero
        fields = {
            "name": ["exact"],
            "intelligence": ["lt", "gt", "exact"],
            "strength": ["lt", "gt", "exact"],
            "power": ["lt", "gt", "exact"],
            "speed": ["lt", "gt", "exact"],
        }
