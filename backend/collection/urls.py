from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PokemonViewSet, available, claim, me, my_pokedex, release

router = DefaultRouter()
router.register("pokemons", PokemonViewSet, basename="pokemon")

urlpatterns = [
    path("", include(router.urls)),
    path("catch/available/", available),
    path("catch/claim/", claim),
    path("me/", me),
    path("my-pokedex/", my_pokedex),
    path("my-pokedex/<int:pk>/", release),
]