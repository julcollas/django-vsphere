from vsphere.api import GuestResource, HypervisorResource
from django.conf.urls import patterns, include, url
from tastypie.api import Api

v1_api = Api(api_name='v1')
v1_api.register(GuestResource())
v1_api.register(HypervisorResource())

urlpatterns = patterns(
    '',
    url(r'^$', 'vsphere.views.home'),
    url(r'^hypervisors$', 'vsphere.views.hypervisors'),
    url(r'^guests$', 'vsphere.views.guests'),
    url(r'^resourcepools$', 'vsphere.views.resourcepools'),
    url(r'^resourcepoolstats$', 'vsphere.views.stats_by_resourcepool'),
    url(r'^top10resourcepools$', 'vsphere.views.top10'),
    url(r'^physical$', 'vsphere.views.physical_statistics'),
    url(r'^datacenter$', 'vsphere.views.datacenter_statistics'),
    url(r'^hypervisor', 'vsphere.views.hypervisor_info'),
    url(r'^guest', 'vsphere.views.guest_info'),
    url(r'^resourcepool', 'vsphere.views.resourcepool'),
    url(r'^search', 'vsphere.views.search'),
    url(r'^api/', include(v1_api.urls)),
    )
