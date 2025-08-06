""" Вся бизнес-логика приложения """
import json
from typing import Union
from requests import get
from requests.exceptions import ConnectionError
from .models import Hero
from .serializers import HeroResponseSerializer
from .service_models import ApiNotRespondedException, HeroNotFound


class HeroCreationService:
    """ Бизнес логика по поиску героя в SuperHero API и добавление его в базу нашего API """

    def find_hero(self, api_key: str, name: str) -> bool:
        """ Получаем информацию о герое """

        try:
            resp = get(f"https://superheroapi.com/api/{api_key}/search/{name.lower()}")
            raw_response = json.loads(resp.text)
            if raw_response.get("response") == "error":
                raise HeroNotFound()

            for hero_data in raw_response["results"]:
                if Hero.objects.filter(id=hero_data.get("id")).exists():
                    continue

                hero_dict = {
                    "id": int(hero_data.get("id")),
                    "name": hero_data.get("name"),
                    "intelligence": int(hero_data["powerstats"].get("intelligence", 0)),
                    "strength": int(hero_data["powerstats"].get("strength", 0)),
                    "power": int(hero_data["powerstats"].get("power", 0)),
                    "speed": int(hero_data["powerstats"].get("speed", 0)),
                }

                serialized_hero = HeroResponseSerializer(data=hero_dict)
                if serialized_hero.is_valid():
                    Hero.objects.create(**serialized_hero.validated_data)
        except ConnectionError:
            raise ApiNotRespondedException()