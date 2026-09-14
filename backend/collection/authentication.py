import os
from pathlib import Path
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
from .models import Profile


def _firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()
    path = Path(os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_service_account.json"))
    if not path.exists():
        raise AuthenticationFailed("Credenciais do Firebase Admin nao configuradas.")
    return firebase_admin.initialize_app(credentials.Certificate(str(path)))

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None
        try:
            decoded = firebase_auth.verify_id_token(header[7:].strip(), app=_firebase_app())
        except Exception as exc:
            raise AuthenticationFailed(f"Token Firebase invalido: {exc}")
        uid = decoded["uid"]
        email = decoded.get("email", f"{uid}@firebase.local")
        user, _ = User.objects.get_or_create(username=uid, defaults={"email": email})
        profile, _ = Profile.objects.get_or_create(firebase_uid=uid, defaults={"user": user})
        if profile.user_id != user.id:
            profile.user = user
            profile.save(update_fields=["user"])
        user.is_staff = profile.is_admin
        user.save(update_fields=["is_staff"])
        return user, decoded
