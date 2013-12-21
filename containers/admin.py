from django.contrib import admin

# Register your models here.
from containers.models import *

class ServerAdmin(admin.ModelAdmin):
    def memory_status(self):
        return "available:%d used:%d free:%d" % (self.memory, self.used_memory, self.free_memory)
    def storage_status(self):
        return "available:%d used:%d free:%d" % (self.storage, self.used_storage, self.free_storage)
    list_display = ('__unicode__', memory_status, storage_status)

class ContainerAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'ip', 'hostname', 'customer', 'server', 'distro', 'memory', 'storage')
    list_filter = ('server', 'distro')
    search_fields = ('name',)

class DomainAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'customer')

admin.site.register(Server, ServerAdmin)
admin.site.register(Distro)
admin.site.register(Customer)
admin.site.register(Container, ContainerAdmin)
admin.site.register(Domain, DomainAdmin)
