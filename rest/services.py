""" Вся бизнес-логика приложения """
import json
from typing import Protocol
from dataclasses import dataclass
from requests.exceptions import ConnectionError
from .models import Hero
from .serializers import HeroResponseSerializer, HeroSearchRequestSerializer
from .exceptions import ApiNotRespondedException, HeroNotFound
from .filters import HeroFilter

class Response(Protocol):
    def json(self) -> dict: ...

class RequestClient(Protocol):
    def get(url: str) -> Response: ...

@dataclass
class HeroCreationService:
    """ Бизнес логика по поиску героя в SuperHero API и добавление его в базу нашего API """

    get: RequestClient
    api_key: str

    def __call__(self, name: str):
        resp = self.__call_external_api(name=name)
        hero_data = self.__process_hero_api_response(resp)
        self.___save_hero(hero_data=hero_data)

    def __call_external_api(self, name: str):
        """ Получаем инфу с SuperHeroAPI"""
        try:
            resp = self.get(f"https://superheroapi.com/api/{self.api_key}/search/{name.lower()}")
            return json.loads(resp.text)
        except ConnectionError:
            raise ApiNotRespondedException()

    def __process_hero_api_response(self, raw_response: dict) -> dict:
        """ Обработка ответа с внешнего API """
        if raw_response.get("response") == "error":
            raise HeroNotFound()
        else:
            return raw_response["results"]
        
    def ___save_hero(self, hero_data: dict):
        if Hero.objects.filter(id=hero_data.get("id")).exists():
            return
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
        
class HeroSearchService:
    """ Бизнес-логика обработки запроса по поиску героя """

    def filter_hero(self, hero_parameters: HeroSearchRequestSerializer):
        heroes_filtred = HeroFilter(hero_parameters.validated_data, queryset=Hero.objects.all())
        return heroes_filtred.qs