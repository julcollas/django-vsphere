# -*- coding: utf-8 -*-
from django.contrib import admin
from vsphere.models import Datastore
from vsphere.models import Hypervisor
from vsphere.models import Disk
from vsphere.models import Guest
from vsphere.models import Network
from vsphere.models import Interface
from vsphere.models import VirtualNic
from vsphere.models import Vswitch


class DatastoreAdmin(admin.ModelAdmin):
    """
    DatastoreAdmin Class with display, filter and search settings
    """
    list_display = ['hypervisor', 'name', 'capacity']
    list_filter = ['hypervisor']
    search_fields = ['hypervisor']
    save_as = True


class DiskAdmin(admin.ModelAdmin):
    """
    DiskAdmin Class with display, filter and search settings
    """
    list_display = ['guest', 'name', 'size', 'datastore']
    list_filter = ['guest']
    search_fields = ['guest']
    save_as = True


class GuestAdmin(admin.ModelAdmin):
    """
    GuestAdmin Class with display, filter and search settings
    """
    list_display = ['name', 'hypervisor', 'vcpu', 'memory', 'resourcePool']
    list_filter = ['hypervisor', 'poweredOn', 'vcpu', 'memory', 'resourcePool']
    search_fields = ['name', 'hypervisor', 'resourcePool']
    save_as = True


class HypervisorAdmin(admin.ModelAdmin):
    """
    HypervisorAdmin Class with display, filter and search settings
    """
    list_display = ['name', 'datacenter', 'vendor', 'memorySize']
    list_filter = ['datacenter', 'vendor', 'memorySize']
    search_fields = ['name']
    save_as = True


class InterfaceAdmin(admin.ModelAdmin):
    """
    InterfaceAdmin Class with display, filter and search settings
    """
    list_display = ['hypervisor', 'name', 'vswitch']
    list_filter = ['hypervisor']
    search_fields = ['hypervisor']
    save_as = True


class VirtualNicAdmin(admin.ModelAdmin):
    """
    VirtualNicAdmin Class with display, filter and search settings
    """
    list_display = ['guest', 'name', 'mac', 'network']
    list_filter = ['guest']
    search_fields = ['guest', 'name', 'network']
    save_as = True


class VswitchAdmin(admin.ModelAdmin):
    """
    VirtualNicAdmin Class with display, filter and search settings
    """
    list_display = ['hypervisor', 'name']
    save_as = True


class NetworkAdmin(admin.ModelAdmin):
    """
    VirtualNicAdmin Class with display, filter and search settings
    """
    list_display = ['name', 'vlanId']
    save_as = True


admin.site.register(Datastore, DatastoreAdmin)
admin.site.register(Hypervisor, HypervisorAdmin)
admin.site.register(Disk, DiskAdmin)
admin.site.register(Guest, GuestAdmin)
admin.site.register(Interface, InterfaceAdmin)
admin.site.register(VirtualNic, VirtualNicAdmin)
admin.site.register(Vswitch, VswitchAdmin)
admin.site.register(Network, NetworkAdmin)
