"""
Serializers pentru autentificare și gestionarea utilizatorilor.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pentru User model.
    
    Include toate câmpurile relevante, inclusiv is_superuser pentru a identifica SUPERADMIN.
    """
    role = serializers.StringRelatedField(read_only=True)
    team = serializers.StringRelatedField(read_only=True)
    # Parola nu este inclusă în serializare pentru securitate
    # Vom folosi un serializer separat pentru schimbarea parolei
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_superuser',  # Important: indică dacă este SUPERADMIN
            'is_staff',
            'is_active',
            'role',
            'team',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'is_superuser',  # Nu poate fi modificat direct prin API
            'is_staff',
            'date_joined',
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pentru crearea unui nou utilizator.
    
    Doar SUPERADMIN poate crea utilizatori noi.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role',
            'team',
            'is_active',
        ]
    
    def validate(self, attrs):
        """Validează că parolele se potrivesc."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Parolele nu se potrivesc.'
            })
        return attrs
    
    def create(self, validated_data):
        """Creează utilizatorul cu parola hash-uită."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)  # Hash-uiește parola
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pentru actualizarea unui utilizator.
    
    Employee poate actualiza doar propriile câmpuri non-critice.
    SUPERADMIN poate actualiza orice.
    """
    
    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'role',
            'team',
            'is_active',
        ]
    
    def validate(self, attrs):
        """Validări suplimentare dacă e necesar."""
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pentru profilul utilizatorului curent (/api/me).
    
    Include informații complete despre utilizatorul autentificat.
    """
    role = serializers.StringRelatedField(read_only=True)
    team = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_superuser',
            'is_staff',
            'is_active',
            'role',
            'team',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'username',
            'is_superuser',
            'is_staff',
            'date_joined',
        ]

