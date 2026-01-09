from django.contrib import admin

from .models import Project, ApiRoute , EmailVerification


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "slug", "name", "created_at")
    list_filter = ("owner",)
    search_fields = ("slug", "name", "owner__username")
    ordering = ("-created_at",)


@admin.register(ApiRoute)
class ApiRouteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "method",
        "path",
        "status_code",
        "is_active",
        "updated_at",
    )
    list_filter = ("method", "is_active", "project")
    search_fields = ("path", "project__slug", "project__owner__username")
    ordering = ("project", "path")

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "token", "created_at", "expires_at", "verified")
    list_filter = ("verified",)
    search_fields = ("user__username", "user__email", "token")
    ordering = ("-created_at",)