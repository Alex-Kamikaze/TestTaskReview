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

    def get(self, request):
        valid_params = {'name'}
        numeric_params = {'intelligence', 'strength', 'speed', 'power'}
        valid_suffixes = {'', '_gte', '_lte'}

        for param in request.query_params:
            base_param = param.split('_')[0] if '_' in param else param
            suffix = param[len(base_param):] if '_' in param else ''
            if base_param not in valid_params and base_param not in numeric_params:
                return Response(
                    {"error": f"Неправильный параметр: {param}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if base_param in numeric_params and suffix not in valid_suffixes:
                return Response(
                    {"error": f"Неподдерживаемый суффикс у параметра: {param}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serialized_data = HeroSearchRequestSerializer(data=request.query_params)
        serialized_data.is_valid(raise_exception=True)
        
        name = serialized_data.validated_data.get("name")
        
        queryset = Hero.objects.all()

        
        if name:
            queryset = queryset.filter(name=name)

        for param in numeric_params:
            for suffix in valid_suffixes:
                param_value = request.query_params.get(param + suffix)
                if param_value:
                    queryset = add_numeric_filter(queryset, param + suffix, param_value)

        if not queryset.exists():
            return Response(
                "Не найдено героя, соответствующего указанным характеристикам",
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = HeroModelSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
