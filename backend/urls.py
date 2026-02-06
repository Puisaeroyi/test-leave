"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from users.views import get_entity_options


def api_root(request):
    """API root endpoint showing available endpoints"""
    return JsonResponse({
        'message': 'Leave Management System API',
        'version': 'v1',
        'endpoints': {
            'auth': '/api/v1/auth/',
            'leaves': '/api/v1/leaves/',
            'notifications': '/api/v1/notifications/',
            'organizations': '/api/v1/organizations/',
        },
        'docs': {
            'swagger': '/api/docs/',
            'redoc': '/api/redoc/',
        },
        'admin': '/admin/',
    })


urlpatterns = [
    # Root
    path('', api_root, name='api_root'),
    path('api/', api_root, name='api_index'),
    path('api/v1/', api_root, name='api_v1_root'),

    # Admin helpers
    path('admin/get-entity-options/', get_entity_options, name='admin_entity_options'),

    # Admin
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/organizations/', include('organizations.urls')),
    path('api/v1/leaves/', include('leaves.urls')),
    path('api/v1/notifications/', include('core.urls')),
]

# API Documentation (development only)
if settings.DEBUG:
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]

# Serve media and static files in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
