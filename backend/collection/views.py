from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AvailableRound, CapturedPokemon, Pokemon
from .permissions import IsAdminProfile
from .serializers import CapturedPokemonSerializer, PokemonSerializer

ROUND_LENGTH = timedelta(minutes=30)
ROUND_SIZE = 5
POKEDEX_LIMIT = 20


class PokemonViewSet(viewsets.ModelViewSet):
    queryset = Pokemon.objects.all()
    serializer_class = PokemonSerializer
    permission_classes = [IsAuthenticated, IsAdminProfile]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({"email": request.user.email, "is_admin": request.user.profile.is_admin})


def _get_current_round(profile):
    now = timezone.now()
    with transaction.atomic():
        round_obj, created = AvailableRound.objects.select_for_update().get_or_create(
            profile=profile, defaults={"generated_at": now}
        )
        if created or now - round_obj.generated_at >= ROUND_LENGTH:
            round_obj.generated_at = now
            round_obj.save(update_fields=["generated_at"])
            round_obj.pokemons.set(list(Pokemon.objects.order_by("?")[:ROUND_SIZE]))
    return round_obj


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def available(request):
    round_obj = _get_current_round(request.user.profile)
    expires_at = round_obj.generated_at + ROUND_LENGTH
    seconds_remaining = max(0, int((expires_at - timezone.now()).total_seconds()))
    return Response({
        "round_started_at": round_obj.generated_at,
        "expires_at": expires_at,
        "seconds_remaining": seconds_remaining,
        "pokemons": PokemonSerializer(round_obj.pokemons.all(), many=True, context={"request": request}).data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def claim(request):
    ids = request.data.get("pokemon_ids")
    if not isinstance(ids, list) or not 1 <= len(ids) <= ROUND_SIZE or len(set(ids)) != len(ids):
        return Response({"detail": "Informe de 1 a 5 IDs distintos."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ids = [int(item) for item in ids]
    except (TypeError, ValueError):
        return Response({"detail": "Os IDs devem ser numericos."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        profile = request.user.profile.__class__.objects.select_for_update().get(pk=request.user.profile.pk)
        round_obj = _get_current_round(profile)
        available_ids = set(round_obj.pokemons.values_list("id", flat=True))
        if not set(ids).issubset(available_ids):
            return Response({"detail": "Um ou mais Pokemon nao estao disponiveis nesta rodada."}, status=400)
        captured_count = CapturedPokemon.objects.filter(profile=profile).count()
        if captured_count + len(ids) > POKEDEX_LIMIT:
            return Response({"detail": f"Sua Pokedex tem limite de {POKEDEX_LIMIT} Pokemon."}, status=400)
        if CapturedPokemon.objects.filter(profile=profile, pokemon_id__in=ids).exists():
            return Response({"detail": "Voce ja capturou um dos Pokemon selecionados."}, status=400)
        CapturedPokemon.objects.bulk_create([CapturedPokemon(profile=profile, pokemon_id=pk) for pk in ids])
    return Response({"detail": "Pokemon capturados com sucesso.", "captured": len(ids)}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_pokedex(request):
    captures = CapturedPokemon.objects.filter(profile=request.user.profile)
    return Response({
        "count": captures.count(), "limit": POKEDEX_LIMIT,
        "pokemons": CapturedPokemonSerializer(captures, many=True, context={"request": request}).data,
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def release(request, pk):
    deleted, _ = CapturedPokemon.objects.filter(profile=request.user.profile, pokemon_id=pk).delete()
    if not deleted:
        return Response({"detail": "Pokemon nao encontrado na sua Pokedex."}, status=404)
    return Response(status=204)