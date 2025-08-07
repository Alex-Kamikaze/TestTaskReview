from rest_framework import serializers
from .models import Hero


class HeroModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Hero


class SearchHeroRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=1024)

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Поле name не может быть пустым!")
        return value
    
class HeroSearchRequestSerializer(serializers.Serializer):
    """ Сериализатор запроса поиска героя по базе """

    name = serializers.CharField(max_length = 1024, required=False)
    intelligence = serializers.IntegerField(required=False)
    strength = serializers.IntegerField(required=False)
    power = serializers.IntegerField(required=False)
    speed = serializers.IntegerField(required=False)