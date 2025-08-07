import pytest
import json
from unittest.mock import MagicMock
import requests_mock
import re
from requests.exceptions import ConnectionError
from rest_framework.test import APIClient
from django.urls import reverse
from .models import Hero
from .services import HeroCreationService, HeroSearchService
from .exceptions import HeroNotFound, ApiNotRespondedException
from .factories import HeroModelFactory

@pytest.fixture
def mock_object():
    return MagicMock()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def search_service():
    return HeroSearchService()


def test_invalid_hero_name(mock_object):
    """ Тест бизнес-логики с вариантом, когда имя героя не найдено """

    mock_response = {"response": "error"} # Имя героя не нашлось
    mock_object.return_value.text = json.dumps(mock_response)
    mock_object.return_value.status_code = 200 # В SuperHeroAPI почему-то всегда возвращается код 200

    service = HeroCreationService(get = mock_object, api_key="TEST_API_KEY")
    with pytest.raises(HeroNotFound):
        service(name="InvalidHero")

def test_api_is_not_responding(mock_object):
    mock_object.side_effect = ConnectionError
    service = HeroCreationService(get = mock_object, api_key="test_api_key")
    with pytest.raises(ApiNotRespondedException):
        service(name="unknown")

@pytest.mark.django_db
def test_correct_hero_is_found(mock_object):
    """ Тест для бизнес-логики, случай когда герой успешно найден в SuperHero API """
    mock_response = {
        "response": "success",
        "results": [{"id": "2", "name": "Batman", "powerstats": {"intelligence": "100", "strength": "30", "speed": "50", "power": "40"}}]
    }
    mock_object.return_value.text = json.dumps(mock_response)
    mock_object.return_value.status_code = 200

    service = HeroCreationService(get = mock_object, api_key="TEST_API_KEY")
    service(name="batman")

    hero = Hero.objects.get(id=2)
    assert hero.name == "Batman"
    assert hero.intelligence == 100
    assert hero.strength == 30
    assert hero.speed == 50
    assert hero.power == 40

def test_view_with_api_not_responding(monkeypatch, mock_object, api_client):
    """ Проверяем, что View выдает ошибку 408, если внешний API не отвечает """

    # Создаем мок для экземпляра, который будет поднимать исключение при вызове
    mock_object.side_effect = ApiNotRespondedException

    # Создаем мок для класса, который возвращает наш экземпляр при инициализации
    mock_class = MagicMock(return_value=mock_object)
    monkeypatch.setattr("rest.views.HeroCreationService", mock_class)

    resp = api_client.post("/api/hero", data={"name": "superman"}, format="json")

    assert resp.status_code == 408
    assert resp.text == "\"SuperHero API не отвечает!\""

def test_view_if_hero_is_not_found(monkeypatch, mock_object, api_client):
    mock_object.side_effect = HeroNotFound

    mock_class = MagicMock(return_value = mock_object)
    monkeypatch.setattr("rest.views.HeroCreationService", mock_class)

    resp = api_client.post("/api/hero", data={"name": "doNotExist"})

    assert resp.status_code == 404
    assert resp.text == "\"Герой с именем doNotExist не найден!\""

@pytest.mark.django_db
def test_view_creates_hero_successfully(api_client):
    """Тестируем, что View возвращает 201 CREATED и герой добавляется в базу данных"""

    with requests_mock.Mocker() as m:
        m.get(re.compile(r"https://superheroapi\.com/api/.*"), text=json.dumps({"response": "success", "results": [{"id": "1", "name": "Superman", "powerstats": {"intelligence": "100", "strength": "100", "speed": "100", "power": "100"}}]}))

        # Отправляем POST-запрос на View
        response = api_client.post(reverse("hero"), data={"name": "superman"}, format="json")

        # Проверяем, что View возвращает статус 201 CREATED
        assert response.status_code == 201

        # Проверяем, что герой добавлен в базу данных
        assert Hero.objects.filter(id=1, name="Superman").exists()

        # Получаем героя из базы данных и проверяем его атрибуты
        hero = Hero.objects.get(id=1)
        assert hero.name == "Superman"
        assert hero.intelligence == 100
        assert hero.strength == 100
        assert hero.speed == 100
        assert hero.power == 100

@pytest.mark.django_db
def test_search_service_with_incorrect_name(search_service: HeroSearchService):
    """ Тест сервиса поиска героя в базе, проверяем выдачу при несуществующем имени """

    with pytest.raises(HeroNotFound):
        search_service.filter_hero({"name": "Unknown"})

@pytest.mark.django_db
def test_search_service_with_correct_name(search_service: HeroSearchService):
    """ Тестируем сервис поиска героя на нахождения героя с корректным именем """

    HeroModelFactory.create()
    result = search_service.filter_hero({"name": "TestHero"})
    hero = result.first()

    assert len(result) > 0
    assert hero.name == "TestHero"
    assert hero.id == 12

@pytest.mark.django_db
def test_search_service_with_incorrect_filters(search_service: HeroSearchService):
    """ Тест сервиса поиска на ошибки, если герой не найден """
    HeroModelFactory.create()

    with pytest.raises(HeroNotFound):
        search_service.filter_hero({"intelligence": "101"})
        search_service.filter_hero({"intelligence__lt": "50"})
        search_service.filter_hero({"intelligence__gt": "110"})

@pytest.mark.django_db
def test_search_service_with_correct_filters(search_service: HeroSearchService):
    """ Тест сервиса поиска с правильными фильтрами"""
    HeroModelFactory.create()

    hero = search_service.filter_hero({"intelligence": "90", "speed__gt": "10", "power__lt": "70"}).first()
    assert hero.id == 12
    assert hero.name == "TestHero"

@pytest.mark.django_db
def test_search_view_with_incorrect_name(api_client):
    """ Тест view для поиска героя с неправильным именем """

    resp = api_client.get("/api/hero?name=Unknown")
    assert resp.status_code == 404
    assert resp.text == "\"Герой с указанными характеристиками не найден!\""

@pytest.mark.django_db
def test_search_view_with_correct_name(api_client):

    HeroModelFactory.create()
    resp = api_client.get("/api/hero?name=TestHero")
    assert resp.status_code == 200
    assert resp.text != ""

@pytest.mark.django_db
def test_search_view_with_incorrect_filter(api_client):

    HeroModelFactory.create()

    resp = api_client.get("/api/hero?intelligence=110")
    assert resp.status_code == 404
    assert resp.text == "\"Герой с указанными характеристиками не найден!\""

@pytest.mark.django_db
def test_search_view_with_correct_filter(api_client):

    HeroModelFactory.create()

    resp = api_client.get("/api/hero?intelligence=90&power__gt=40")
    assert resp.status_code == 200