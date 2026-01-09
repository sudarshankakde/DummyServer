"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path ,include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .ai_views import generate_json_ai

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Email verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('create-project/', views.create_project, name='create_project'),
    path('create-route/', views.create_route, name='create_route'),
    path('create-route/<int:project_id>/', views.create_route, name='create_route_for_project'),
    
    # Detail views
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('route/<int:route_id>/', views.route_detail, name='route_detail'),
    path('route/<int:route_id>/edit/', views.edit_route_form, name='edit_route'),
    
    # Delete operations
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('route/<int:route_id>/delete/', views.delete_route, name='delete_route'),
    
    # HTMX endpoints
    path('htmx/validate-email/', views.validate_email, name='validate_email'),
    path('htmx/validate-username/', views.validate_username, name='validate_username'),
    path('htmx/validate-json/', views.validate_json, name='validate_json'),
    path('htmx/generate-slug/', views.generate_slug, name='generate_slug'),
    path('htmx/routes-list/<int:project_id>/', views.routes_list_fragment, name='routes_list_fragment'),
    path('htmx/check-route-exists/', views.check_route_exists, name='check_route_exists'),
    # AI endpoints
    path('api/generate-json-ai/', generate_json_ai, name='generate_json_ai'),
    # Dynamic route handler: /<username>/<project-slug>/<rest-of-path>
    re_path(r'^(?P<username>\w+)/(?P<project_slug>[\w-]+)/(?P<rest_of_path>.*)$', views.dynamic_route_handler, name='dynamic_route'),
]

# Serve static and media files in production
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
