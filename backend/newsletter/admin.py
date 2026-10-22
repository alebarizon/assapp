from django.contrib import admin

from .models import Campanha, Descadastro, EnvioRegua, Regua

admin.site.register(Campanha)
admin.site.register(Descadastro)
admin.site.register(Regua)
admin.site.register(EnvioRegua)
