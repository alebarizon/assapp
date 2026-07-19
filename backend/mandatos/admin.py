from django.contrib import admin

from .models import (
    CargoMandato,
    Mandato,
    MandatoSnapshot,
    OnboardingEtapa,
    TransicaoMandato,
)


class CargoMandatoInline(admin.TabularInline):
    model = CargoMandato
    extra = 1


class SnapshotInline(admin.TabularInline):
    model = MandatoSnapshot
    extra = 0
    readonly_fields = ("hash", "created_at", "versao")
    can_delete = False


@admin.register(Mandato)
class MandatoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "status", "numero_sequencial", "data_inicio", "data_fim")
    list_filter = ("status",)
    search_fields = ("titulo",)
    inlines = [CargoMandatoInline, SnapshotInline]


class OnboardingEtapaInline(admin.TabularInline):
    model = OnboardingEtapa
    extra = 0
    readonly_fields = ("concluida_em",)


@admin.register(TransicaoMandato)
class TransicaoMandatoAdmin(admin.ModelAdmin):
    list_display = (
        "mandato_anterior",
        "mandato_novo",
        "status",
        "progresso_percentual",
        "data_inicio_transicao",
    )
    list_filter = ("status",)
    inlines = [OnboardingEtapaInline]


@admin.register(MandatoSnapshot)
class MandatoSnapshotAdmin(admin.ModelAdmin):
    list_display = ("mandato", "tipo", "versao", "hash", "created_at")
    list_filter = ("tipo",)
    readonly_fields = ("hash", "dados", "created_at")
