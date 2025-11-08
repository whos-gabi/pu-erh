"""
Permission classes pentru controlul accesului în API.
"""
from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permisiune care permite accesul doar utilizatorilor cu is_superuser=True.
    
    Utilizare:
        permission_classes = [IsSuperAdmin]
    """
    
    def has_permission(self, request, view):
        """Verifică dacă utilizatorul este SUPERADMIN."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsOwner(permissions.BasePermission):
    """
    Permisiune care permite accesul doar proprietarului obiectului.
    
    Presupune că obiectul are un câmp 'user' care este ForeignKey către User.
    
    Utilizare:
        permission_classes = [IsOwner]
    """
    
    def has_object_permission(self, request, view, obj):
        """Verifică dacă utilizatorul este proprietarul obiectului."""
        # Verifică dacă obiectul are atributul 'user'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsOwnerOrSuperAdmin(permissions.BasePermission):
    """
    Permisiune care permite accesul dacă utilizatorul este proprietar SAU SUPERADMIN.
    
    Utilizare:
        permission_classes = [IsOwnerOrSuperAdmin]
    """
    
    def has_permission(self, request, view):
        """Verifică dacă utilizatorul este autentificat."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Verifică dacă utilizatorul este proprietar sau SUPERADMIN."""
        # SUPERADMIN are acces la tot
        if request.user.is_superuser:
            return True
        
        # Verifică dacă utilizatorul este proprietar
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permisiune care permite:
    - Read (GET) pentru toți utilizatorii autentificați
    - Write (POST/PUT/PATCH/DELETE) doar pentru proprietar
    
    Utilizare:
        permission_classes = [IsOwnerOrReadOnly]
    """
    
    def has_permission(self, request, view):
        """Verifică dacă utilizatorul este autentificat."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Verifică permisiunile pe obiect."""
        # Read permissions pentru toți
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions doar pentru proprietar
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False

