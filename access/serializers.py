from rest_framework import serializers
from .models import User, Role


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = User
        fields = ('email', 'password', 'role')

    def validate_role(self, value):
        if value not in Role.values:
            raise serializers.ValidationError(
                f'Invalid role. Choose from: {Role.values}'
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()   # role_id auto-generated in model's save()
        return user


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model  = User
        fields = ('id', 'email', 'role', 'role_display', 'role_id', 'created_at')
        read_only_fields = ('id', 'role_id', 'created_at')


class TokenPayloadSerializer(serializers.Serializer):
    valid   = serializers.BooleanField()
    sub     = serializers.CharField()
    email   = serializers.EmailField()
    role    = serializers.CharField()
    role_id = serializers.CharField()