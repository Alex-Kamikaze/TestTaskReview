import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    SearchHeroRequestSerializer,
    HeroModelSerializer,
    HeroResponseSerializer,
    HeroSearchRequestSerializer,
)
from .models import Hero
from .utils import add_numeric_filter
from .services import HeroCreationService
from .service_models import ApiNotRespondedException, HeroNotFound


class HeroView(APIView):
    """Основное View для отправки/получения данных о героях"""

    def post(self, request):
        """Обработчик запроса на поиск по имени"""

        request_data = SearchHeroRequestSerializer(data=request.data)
        request_data.is_valid(raise_exception=True)

        try:
            HeroCreationService.find_hero(
                settings.SUPERHERO_API_KEY, request_data.validated_data.get("name")
            )
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
            return Response(status=status.HTTP_200_OK)

    def get(self, request):
        valid_params = {"name"}
        numeric_params = {"intelligence", "strength", "speed", "power"}
        valid_suffixes = {"", "_gte", "_lte"}

        for param in request.query_params:
            base_param = param.split("_")[0] if "_" in param else param
            suffix = param[len(base_param) :] if "_" in param else ""
            if base_param not in valid_params and base_param not in numeric_params:
                return Response(
                    {"error": f"Неправильный параметр: {param}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if base_param in numeric_params and suffix not in valid_suffixes:
                return Response(
                    {"error": f"Неподдерживаемый суффикс у параметра: {param}"},
                    status=status.HTTP_400_BAD_REQUEST,
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
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HeroModelSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
