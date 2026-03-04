""" Serializers for accounts app- used for user authentication and profile management."""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - used in profile responses."""

    class Meta:
        """Meta options for UserSerializer."""
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]


class LoginSerializer(serializers.Serializer):
    """Serializer for login endpoint."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError(
                "Both username and password are required."
            )

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response."""

    token = serializers.CharField()
    user = UserSerializer()

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance
