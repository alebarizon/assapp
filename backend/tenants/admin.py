from django.contrib import admin

from tenants.models import Domain, Tenant

admin.site.register(Tenant)
admin.site.register(Domain)
