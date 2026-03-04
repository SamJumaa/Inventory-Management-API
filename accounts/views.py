"""Views for accounts app (authentication endpoints)."""

from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import LoginSerializer, UserSerializer


class AuthViewSet(viewsets.ViewSet):
    """
    Authentication endpoints:
    - POST /api/v1/auth/login/  -> obtain token
    - POST /api/v1/auth/logout/ -> delete token
    - GET  /api/v1/auth/me/     -> get current user
    """

    def get_permissions(self):
        if self.action == "login":
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        """
        Body: {"username": "...", "password": "..."}
        Response: {"token": "...", "user": {...}}
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Because LoginSerializer.validate() authenticates the user:
        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)  # type: ignore[attr-defined]

        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated()])
    def logout(self, request):
        """
        Deletes the current user's auth token.
        """
        if hasattr(request.user, "auth_token"):
            request.user.auth_token.delete()

        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated()])
    def me(self, request):
        """
        Returns the authenticated user's profile.
        """
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
