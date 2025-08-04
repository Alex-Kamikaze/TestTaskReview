from django.test import TestCase
from rest_framework.test import APIClient
from .models import Hero


# Create your tests here.


class HeroCreationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_incorrect_hero_throws_404(self):
        """Проверяем, что если героя нет в SuperHero API, то View кидает ошибку 404"""
        response = self.client.post("/api/hero", {"name": "Didn'tExistingHero"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.text, '"Герой с именем Didn\'tExistingHero не найден!"'
        )

    def test_correct_hero_is_created(self):
        """Проверяем, что при запросе существующего героя из SuperHero API, мы действительно записываем инфу в базу"""
        response = self.client.post("/api/hero", {"name": "batman"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Hero.objects.filter(name__contains="Batman").exists(), True)


class HeroSearchTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_hero = Hero.objects.create(
            id=1, name="TestHero", intelligence=90, power=87, strength=92, speed=56
        )

    def test_hero_is_found_by_name(self):
        """Проверяем поиск в базе по имени"""
        response = self.client.get("/api/hero", {"name": "TestHero"})
        self.assertEqual(response.status_code, 200)

    def test_incorrect_hero_is_not_found(self):
        """Проверяем, что при поиске несуществующего героя нам выдаст 404"""
        test_response = self.client.get("/api/hero", {"name": "3271563156"})
        self.assertEqual(test_response.status_code, 404)

    def test_incorrect_params_is_not_found(self):
        """Проверяем, что при некорректно введенных характеристиках выбивает ошибку 404"""
        response = self.client.get("/api/hero", {"intelligence": 101})
        self.assertEqual(response.status_code, 404)

    def test_hero_with_correct_params_is_found(self):
        """Проверяем поиск героя по характеристикам"""

        response = self.client.get("/api/hero", {"intelligence": 90})
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/hero", {"intelligence__gte": 70})
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/hero", {"intelligence__lte": 100})
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/hero", {"intelligence__gte": 87})
        self.assertEqual(response.status_code, 200)
