"""
URL configuration for Office Smart Appointments project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.routers import DefaultRouter
from apps.core.api import (
    RoleViewSet,
    TeamViewSet,
    RoomCategoryViewSet,
    RoomViewSet,
    ItemCategoryViewSet,
    ItemViewSet,
)
from apps.core.viewsets import (
    RequestViewSet,
    AppointmentViewSet,
    AvailabilityViewSet,
)
from apps.core.policy_views import (
    OrgPolicyViewSet,
)
from apps.core.auth_views import (
    MeViewSet,
    UserViewSet,
    CustomTokenObtainPairView,
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
# Autentificare și profil
router.register(r'me', MeViewSet, basename='me')
# Utilizatori
router.register(r'users', UserViewSet, basename='user')
# Policy organizațională
router.register(r'policy', OrgPolicyViewSet, basename='policy')
# Resurse principale
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'room-categories', RoomCategoryViewSet, basename='roomcategory')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'item-categories', ItemCategoryViewSet, basename='itemcategory')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'availability', AvailabilityViewSet, basename='availability')

urlpatterns = [
    path('admin/', admin.site.urls),
    # OpenAPI Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # Autentificare JWT
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # API endpoints
    path('api/', include(router.urls)),
]

