from django.contrib import admin

from .models import StatsCharacter, zKillMonth

admin.site.register(StatsCharacter)


class month(admin.ModelAdmin):
    list_display = ('char', 'year', 'month', 'last_update')
    search_fields = ['char__character__character_name']
    ordering = ('char', '-year', 'month')


admin.site.register(zKillMonth, month)
