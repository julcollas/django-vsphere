from django.conf.urls import patterns, include, url
from vsphere.api import GuestResource

guest_resource = GuestResource()

urlpatterns = patterns('',
    url(r'^$', 'vsphere.views.home'),
    url(r'^hypervisors', 'vsphere.views.hypervisors'),
    url(r'^guests', 'vsphere.views.guests'),
    url(r'^hypervisor', 'vsphere.views.hypervisor_info'),
    url(r'^guest', 'vsphere.views.guest_info'),
    url(r'^search', 'vsphere.views.search'),
    url(r'^resourcepool', 'vsphere.views.resourcepool'),
    url(r'^top10', 'vsphere.views.top10'),
    url(r'^api/', include(guest_resource.urls)),
)