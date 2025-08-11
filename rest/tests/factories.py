from factory.django import DjangoModelFactory
from rest.models import Hero


class HeroModelFactory(DjangoModelFactory):
    class Meta:
        model = Hero

    id = 12
    name = "TestHero"
    intelligence = 90
    power = 50
    strength = 30
    speed = 12
