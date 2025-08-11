from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from .serializers import (
    SearchHeroRequestSerializer,
    HeroModelSerializer,
    HeroSearchRequestSerializer,
)
from .services import HeroCreationService, HeroSearchService
from .exceptions import ApiNotRespondedException, HeroNotFound


class HeroView(APIView):
    """Основное View для отправки/получения данных о героях"""

    def post(self, request):
        """Обработчик запроса на поиск по имени"""

        request_data = SearchHeroRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)
        service = HeroCreationService(
            get=requests.get, api_key=settings.SUPERHERO_API_KEY
        )

        try:
            service(name=request_data.validated_data.get("name"))
        except ApiNotRespondedException:
            return Response(
                "SuperHero API не отвечает!", status=status.HTTP_408_REQUEST_TIMEOUT
            )
        except HeroNotFound:
            return Response(
                f"Герой с именем {request_data.validated_data['name']} не найден!",
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            return Response(status=status.HTTP_201_CREATED)

    def get(self, request):
        """Обработчик поиска по характеристикам (Знали бы вы, как я хотел это реализовать через ListAPIView....)"""

        request_data = HeroSearchRequestSerializer(data=request.query_params)
        request_data.is_valid(raise_exception=True)
        service = HeroSearchService()

        try:
            heroes = service.filter_hero(hero_parameters=request_data.validated_data)
            serialized_heroes = HeroModelSerializer(heroes, many=True)
            return Response(serialized_heroes.data, status=status.HTTP_200_OK)
        except HeroNotFound:
            return Response(
                "Герой с указанными характеристиками не найден!",
                status=status.HTTP_404_NOT_FOUND,
            )
