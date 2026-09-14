from rest_framework import serializers
from .models import CapturedPokemon, Pokemon

class PokemonSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Pokemon
        fields = ["id", "name", "pokedex_number", "type", "description", "image", "image_url"]
    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request and obj.image else None

class CapturedPokemonSerializer(serializers.ModelSerializer):
    pokemon = PokemonSerializer(read_only=True)
    class Meta:
        model = CapturedPokemon
        fields = ["id", "pokemon", "captured_at"]
