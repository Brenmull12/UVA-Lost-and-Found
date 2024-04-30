from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ["email", "email", "first_name", "last_name", "is_site_admin", "is_superuser"]
    list_filter = ["email", "last_name", "is_site_admin", "is_superuser"]
    search_fields = ["email"]


admin.site.register(User, UserAdmin)
