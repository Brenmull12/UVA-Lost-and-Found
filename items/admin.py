from django.contrib import admin
from .models import Item, ItemFile, Location, Location_Category


class FileInLine(admin.TabularInline):
    model = ItemFile
    extra = 0


class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'user', 'status', 'tag')
    list_filter = ('user', 'status', 'tag')
    date_hierarchy = 'date'
    search_fields = ('item_name',)

    inlines = [FileInLine]


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')


class LocationInLine(admin.TabularInline):
    model = Location
    extra = 1


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )
    inlines = [LocationInLine]


admin.site.register(Item, ItemAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Location_Category, CategoryAdmin)
