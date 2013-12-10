from tastypie.resources import ModelResource
from vsphere.models import Guest, Hypervisor
from tastypie import fields


class GuestResource(ModelResource):
    hypervisor = fields.CharField(attribute="hypervisor")

    class Meta:
        queryset = Guest.objects.all()
        include_resource_uri = False
        resource_name = 'guest'
        ordering = ['name']
        limit = 0
        filtering = {
            'name': ('exact', 'startswith', 'icontains'),
        }

    def determine_format(self, request):
        return 'application/json'


class HypervisorResource(ModelResource):

    class Meta:
        queryset = Hypervisor.objects.all()
        include_resource_uri = False
        resource_name = 'hypervisor'
        ordering = ['name']
        limit = 0
        filtering = {
            'name': ('exact', 'startswith', 'icontains'),
        }

    def determine_format(self, request):
        return 'application/json'
