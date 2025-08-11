"""Вся бизнес-логика приложения"""

from typing import Protocol, Dict, List, TypedDict
from dataclasses import dataclass
import json
from requests.exceptions import ConnectionError
from .models import Hero
from .exceptions import ApiNotRespondedException, HeroNotFound
from .filters import HeroFilter


class HeroPowerstats(TypedDict):
    stat: str
    value: int


class HeroServiceModel(TypedDict):
    id: str
    name: str
    powerstats: HeroPowerstats


class Response(Protocol):
    def json(self) -> dict: ...


class RequestClient(Protocol):
    def __call__(url: str) -> Response: ...


@dataclass
class HeroCreationService:
    """Бизнес логика по поиску героя в SuperHero API и добавление его в базу нашего API"""

    get: RequestClient
    api_key: str

    def __call__(self, name: str):
        resp = self._call_external_api(name=name)
        hero_data = self._process_hero_api_response(resp)
        self._save_hero(hero_data=hero_data)

    def _call_external_api(self, name: str) -> dict[str, str]:
        """Получаем инфу с SuperHeroAPI"""
        try:
            resp = self.get(
                f"https://superheroapi.com/api/{self.api_key}/search/{name.lower()}"
            )
            return json.loads(resp.text)
        except ConnectionError:
            raise ApiNotRespondedException()

    def _process_hero_api_response(
        self, raw_response: dict[str, str]
    ) -> list[HeroServiceModel]:
        """Обработка ответа с внешнего API"""
        if raw_response.get("response") == "error":
            raise HeroNotFound()
        else:
            return raw_response["results"]

    def _save_hero(self, hero_data: list[HeroServiceModel]):
        for hero in hero_data:
            if Hero.objects.filter(id=hero.get("id")).exists():
                continue

            hero_dict = {
                "id": int(hero.get("id")),
                "name": hero.get("name"),
                "intelligence": int(hero["powerstats"].get("intelligence", 0)),
                "strength": int(hero["powerstats"].get("strength", 0)),
                "power": int(hero["powerstats"].get("power", 0)),
                "speed": int(hero["powerstats"].get("speed", 0)),
            }
            Hero.objects.create(**hero_dict)


class HeroSearchService:
    """Бизнес-логика обработки запроса по поиску героя"""

    def filter_hero(self, hero_parameters: dict[str, str]):
        heroes_filtred = HeroFilter(hero_parameters, queryset=Hero.objects.all())
        if len(heroes_filtred.qs) == 0:
            raise HeroNotFound()
        else:
            return heroes_filtred.qs
