import pytest
import json
from requests.exceptions import ConnectionError
from rest.services import HeroCreationService, HeroSearchService
from rest.exceptions import HeroNotFound, ApiNotRespondedException
from rest.models import Hero
from .factories import HeroModelFactory

def test_invalid_hero_name(mock_object):
    """Тест бизнес-логики с вариантом, когда имя героя не найдено"""

    mock_response = {"response": "error"}  # Имя героя не нашлось
    mock_object.return_value.text = json.dumps(mock_response)
    mock_object.return_value.status_code = (
        200  # В SuperHeroAPI почему-то всегда возвращается код 200
    )

    service = HeroCreationService(get=mock_object, api_key="TEST_API_KEY")
    with pytest.raises(HeroNotFound):
        service(name="InvalidHero")

def test_api_is_not_responding(mock_object):
    mock_object.side_effect = ConnectionError
    service = HeroCreationService(get=mock_object, api_key="test_api_key")
    with pytest.raises(ApiNotRespondedException):
        service(name="unknown")

@pytest.mark.django_db
def test_correct_hero_is_found(mock_object):
    """Тест для бизнес-логики, случай когда герой успешно найден в SuperHero API"""
    mock_response = {
        "response": "success",
        "results": [
            {
                "id": "2",
                "name": "Batman",
                "powerstats": {
                    "intelligence": "100",
                    "strength": "30",
                    "speed": "50",
                    "power": "40",
                },
            }
        ],
    }
    mock_object.return_value.text = json.dumps(mock_response)
    mock_object.return_value.status_code = 200

    service = HeroCreationService(get=mock_object, api_key="TEST_API_KEY")
    service(name="batman")

    hero = Hero.objects.get(id=2)
    assert hero.name == "Batman"
    assert hero.intelligence == 100
    assert hero.strength == 30
    assert hero.speed == 50
    assert hero.power == 40

@pytest.mark.django_db
def test_search_service_with_incorrect_name(search_service: HeroSearchService):
    """Тест сервиса поиска героя в базе, проверяем выдачу при несуществующем имени"""

    with pytest.raises(HeroNotFound):
        search_service.filter_hero({"name": "Unknown"})

@pytest.mark.django_db
def test_search_service_with_correct_name(search_service: HeroSearchService):
    """Тестируем сервис поиска героя на нахождения героя с корректным именем"""

    HeroModelFactory.create()
    result = search_service.filter_hero({"name": "TestHero"})
    hero = result.first()

    assert len(result) > 0
    assert hero.name == "TestHero"
    assert hero.id == 12


@pytest.mark.django_db
def test_search_service_with_incorrect_filters(search_service: HeroSearchService):
    """Тест сервиса поиска на ошибки, если герой не найден"""
    HeroModelFactory.create()

    with pytest.raises(HeroNotFound):
        search_service.filter_hero({"intelligence": "101"})
        search_service.filter_hero({"intelligence__lt": "50"})
        search_service.filter_hero({"intelligence__gt": "110"})


@pytest.mark.django_db
def test_search_service_with_correct_filters(search_service: HeroSearchService):
    """Тест сервиса поиска с правильными фильтрами"""
    HeroModelFactory.create()

    hero = search_service.filter_hero(
        {"intelligence": "90", "speed__gt": "10", "power__lt": "70"}
    ).first()
    assert hero.id == 12
    assert hero.name == "TestHero"