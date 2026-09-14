from django.contrib import admin
from .models import AvailableRound, CapturedPokemon, Pokemon, Profile

admin.site.register(Pokemon)
admin.site.register(Profile)
admin.site.register(AvailableRound)
admin.site.register(CapturedPokemon)
