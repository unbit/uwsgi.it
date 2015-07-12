from django.contrib import admin
from django.forms import ModelForm,HiddenInput

# Register your models here.
from uwsgi_it_api.models import *

class ServerAdmin(admin.ModelAdmin):
    def memory_status(self):
        return "available:%d used:%d free:%d" % (self.memory, self.used_memory, self.free_memory)
    def storage_status(self):
        return "available:%d used:%d free:%d" % (self.storage, self.used_storage, self.free_storage)
    list_display = ('__unicode__', memory_status, storage_status, 'weight', 'owner', 'ctime', 'mtime')
    list_filter = ('datacenter',)
    

class ContainerAccounted(admin.SimpleListFilter):
    title = 'is accounted ?'
    parameter_name = 'is_accounted'
    def lookups(self, request, model_admin):
        return (('1', 'Yes'), ('0', 'No'))
    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(accounted=False, server__owner=None)
        elif self.value() == '1':
            return queryset.filter(accounted=True, server__owner=None)
        return queryset

class ContainerAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ContainerAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags'].queryset = Tag.objects.filter(customer=self.instance.customer)
            self.fields['custom_distro'].queryset = CustomDistro.objects.filter(container__server=self.instance.server, container__customer=self.instance.customer).exclude(container=self.instance)
        else:
            self.fields['tags'].widget = HiddenInput()
            self.fields['custom_distro'].widget = HiddenInput()

class ContainerAdmin(admin.ModelAdmin):
    def is_accounted(self):
        if self.accounted:
            return True
        if self.server and self.server.owner:
            return True
        return False
    is_accounted.boolean = True
    list_display = ('__unicode__', 'ip', 'hostname', 'customer', 'server', 'distro', 'memory', 'storage', is_accounted, 'ctime')
    list_filter = ('server', 'distro', ContainerAccounted)
    search_fields = ('name', 'customer__user__username', 'tags__name', 'admin_note', 'admin_order')

    form = ContainerAdminForm

class DomainAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DomainAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags'].queryset = Tag.objects.filter(customer=self.instance.customer)
        else:
            self.fields['tags'].widget = HiddenInput()
        

class DomainAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'customer')
    list_filter = ('customer',)
    search_fields = ('name',)

    form = DomainAdminForm

class ContainerMetricAdmin(admin.ModelAdmin):
    list_display = ('container', 'year', 'month', 'day')
    list_filter = ('year', 'month')

class DomainMetricAdmin(admin.ModelAdmin):
    list_display = ('domain', 'container', 'year', 'month', 'day')
    list_filter = ('year', 'month')

class LegionNodeInline(admin.TabularInline):
    model = LegionNode

class LegionAdmin(admin.ModelAdmin):
    def servers(self, obj):
        return ','.join([s.name for s in obj.nodes.all()])

    list_display = ('__unicode__', 'customer', 'servers', 'note')
    inlines = [ LegionNodeInline ]

class TagAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'customer')
    list_filter = ('customer',)
    search_fields = ('name',) 

class FloatingAddressAdmin(admin.ModelAdmin):
    list_display = ('address', 'mapped_to_server', 'legion', 'customer', 'note')

def _user__email(self):
    if self.user:
        return self.user.email
    return ''
_user__email.short_description = 'Email'

def _containers__count(self):
    return self.container_set.count()
_containers__count.short_description = 'Containers'

class CustomerContainerInline(admin.TabularInline):
    model = Container
    fields = ['name', 'server', 'memory', 'storage']
    readonly_fields = ['name', 'server', 'memory', 'storage']
    extra = 0
    can_delete = False
    max_num = 0

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', _user__email, 'company', 'vat', _containers__count)
    inlines = [CustomerContainerInline]
    search_fields = ('user__username', 'user__email', 'company', 'vat', 'admin_note')

class NewsAdmin(admin.ModelAdmin):
    list_display = ('content', 'ctime', 'public')

class LoopboxAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(LoopboxAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags'].queryset = Tag.objects.filter(customer=self.instance.container.customer)
        else:
            self.fields['tags'].widget = HiddenInput()

class LoopboxAdmin(admin.ModelAdmin):
    list_display = ('container', 'filename', 'mountpoint')

    form = LoopboxAdminForm

class AlarmAdmin(admin.ModelAdmin):
    list_display = ('container', 'vassal', 'level', 'unix', 'msg')
    list_filter = ('level',)
    search_fields = ('msg', '_class', 'vassal', 'color') 

class CustomDistroAdmin(admin.ModelAdmin):
    list_display = ('container', 'name', 'path')

class PortmapAdmin(admin.ModelAdmin):
    def _container__server(self):
        return self.container.server
    def _container__ip(self):
        return self.container.ip
    list_display = (_container__server, 'proto', 'public_port', 'container', _container__ip, 'private_port')
    

admin.site.register(Server, ServerAdmin)
admin.site.register(Distro)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Container, ContainerAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(Legion, LegionAdmin)
admin.site.register(ContainerLink)
admin.site.register(Datacenter)
admin.site.register(Tag, TagAdmin)
admin.site.register(CustomService)
admin.site.register(CustomerAttribute)

admin.site.register(FloatingAddress,FloatingAddressAdmin)

admin.site.register(NetworkRXContainerMetric,ContainerMetricAdmin)
admin.site.register(NetworkTXContainerMetric,ContainerMetricAdmin)
admin.site.register(CPUContainerMetric,ContainerMetricAdmin)
admin.site.register(MemoryContainerMetric,ContainerMetricAdmin)
admin.site.register(MemoryRSSContainerMetric,ContainerMetricAdmin)
admin.site.register(MemoryCacheContainerMetric,ContainerMetricAdmin)
admin.site.register(IOReadContainerMetric,ContainerMetricAdmin)
admin.site.register(IOWriteContainerMetric,ContainerMetricAdmin)
admin.site.register(QuotaContainerMetric,ContainerMetricAdmin)

admin.site.register(HitsDomainMetric,DomainMetricAdmin)
admin.site.register(NetworkRXDomainMetric,DomainMetricAdmin)
admin.site.register(NetworkTXDomainMetric,DomainMetricAdmin)

admin.site.register(News, NewsAdmin)
admin.site.register(Loopbox, LoopboxAdmin)

admin.site.register(Alarm, AlarmAdmin)

admin.site.register(CustomDistro, CustomDistroAdmin)

admin.site.register(Portmap, PortmapAdmin)
