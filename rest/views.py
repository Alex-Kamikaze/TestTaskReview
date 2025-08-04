import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from requests import get
from .serializers import (
    SearchHeroRequestSerializer,
    HeroModelSerializer,
    HeroResponseSerializer,
    HeroSearchRequestSerializer,
)
from .models import Hero
from .utils import add_numeric_filter


class HeroView(APIView):
    """Основное View для отправки/получения данных о героях"""

    def post(self, request, format=None):
        """Обработчик запроса на поиск по имени"""

        request_data = SearchHeroRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)

        hero_request = get(
            f"https://superheroapi.com/api/{settings.SUPERHERO_API_KEY}/search/{request_data.validated_data['name'].lower()}"
        )
        raw_response = json.loads(hero_request.text)
        if raw_response.get("response") == "error":
            return Response(
                f"Герой с именем {request_data.validated_data['name']} не найден!",
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            # т.к. приходит несколько разных вариаций одного и того же героя, то их всех записываем в базу
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
                serialized_hero.is_valid(raise_exception=True)
                serialized_hero.save()

        return Response(status=status.HTTP_200_OK)

    def get(self, request, format=None):
        serialized_request = HeroSearchRequestSerializer(data=request.query_params)
        serialized_request.is_valid(raise_exception=True)

        # Базовый queryset, от него отталкиваемся в дальнейшем при фильтрации
        queryset = Hero.objects.all()

        if serialized_request.validated_data.get("name"):
            queryset = queryset.filter(
                name=serialized_request.validated_data.get("name")
            )

        for param in ("intelligence", "strength", "speed", "power"):
            for suffix in ("", "_gte", "_lte"):
                param_value = serialized_request.validated_data.get(param + suffix)
                if param_value:
                    queryset = add_numeric_filter(queryset, param + suffix, param_value)

        if not queryset.exists():
            return Response(
                "Герой с указанными характеристиками не найден!",
                status=status.HTTP_404_NOT_FOUND,
            )

        response = HeroModelSerializer(queryset, many=True)
        return Response(response.data, status=status.HTTP_200_OK)
