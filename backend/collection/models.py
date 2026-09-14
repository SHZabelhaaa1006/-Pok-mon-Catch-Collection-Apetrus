from django.contrib.auth.models import User
from django.db import models

class Pokemon(models.Model):
    name = models.CharField(max_length=120)
    pokedex_number = models.PositiveIntegerField(unique=True)
    type = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="pokemon/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["pokedex_number"]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    firebase_uid = models.CharField(max_length=128, unique=True)
    is_admin = models.BooleanField(default=False)

class AvailableRound(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="round")
    generated_at = models.DateTimeField()
    pokemons = models.ManyToManyField(Pokemon, related_name="available_rounds")

class CapturedPokemon(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="captures")
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, related_name="captured_by")
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "pokemon"], name="unique_profile_pokemon")]
        ordering = ["-captured_at"]
