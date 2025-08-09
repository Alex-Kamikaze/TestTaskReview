""" Тесты для вьюшек """
import pytest
import requests_mock
import re
import json
from django.urls import reverse
from rest.models import Hero
from rest.exceptions import ApiNotRespondedException, HeroNotFound
from .factories import HeroModelFactory

def test_view_with_api_not_responding(monkeypatch, mock_object, api_client, mocker):
    """Проверяем, что View выдает ошибку 408, если внешний API не отвечает"""

    # Создаем мок для экземпляра, который будет поднимать исключение при вызове
    mock_object.side_effect = ApiNotRespondedException

    # Создаем мок для класса, который возвращает наш экземпляр при инициализации
    mock_class = mocker.MagicMock(return_value=mock_object)
    monkeypatch.setattr("rest.views.HeroCreationService", mock_class)

    resp = api_client.post("/api/hero", data={"name": "superman"}, format="json")

    assert resp.status_code == 408
    assert resp.text == '"SuperHero API не отвечает!"'

def test_view_if_hero_is_not_found(monkeypatch, mock_object, api_client, mocker):
    mock_object.side_effect = HeroNotFound

    mock_class = mocker.MagicMock(return_value=mock_object)
    monkeypatch.setattr("rest.views.HeroCreationService", mock_class)

    resp = api_client.post("/api/hero", data={"name": "doNotExist"})

    assert resp.status_code == 404
    assert resp.text == '"Герой с именем doNotExist не найден!"'

@pytest.mark.django_db
def test_view_creates_hero_successfully(api_client):
    """Тестируем, что View возвращает 201 CREATED и герой добавляется в базу данных"""

    with requests_mock.Mocker() as m:
        m.get(
            re.compile(r"https://superheroapi\.com/api/.*"),
            text=json.dumps(
                {
                    "response": "success",
                    "results": [
                        {
                            "id": "1",
                            "name": "Superman",
                            "powerstats": {
                                "intelligence": "100",
                                "strength": "100",
                                "speed": "100",
                                "power": "100",
                            },
                        }
                    ],
                }
            ),
        )

        # Отправляем POST-запрос на View
        response = api_client.post(
            reverse("hero"), data={"name": "superman"}, format="json"
        )

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
def test_search_view_with_incorrect_name(api_client):
    """Тест view для поиска героя с неправильным именем"""

    resp = api_client.get("/api/hero?name=Unknown")
    assert resp.status_code == 404
    assert resp.text == '"Герой с указанными характеристиками не найден!"'


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
    assert resp.text == '"Герой с указанными характеристиками не найден!"'


@pytest.mark.django_db
def test_search_view_with_correct_filter(api_client):
    HeroModelFactory.create()

    resp = api_client.get("/api/hero?intelligence=90&power__gt=40")
    assert resp.status_code == 200