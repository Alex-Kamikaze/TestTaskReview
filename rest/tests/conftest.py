import pytest
from rest_framework.test import APIClient
from rest.services import HeroSearchService

@pytest.fixture
def mock_object(mocker):
    return mocker.MagicMock()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def search_service():
    return HeroSearchService()