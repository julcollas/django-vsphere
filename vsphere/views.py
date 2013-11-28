from vsphere.models import Hypervisor, Guest, Datastore, Disk, Interface, VirtualNic, Network, Vswitch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse


def home(request):
    hypervisor_list = Hypervisor.objects.all()
    datacenter = [x.datacenter for x in hypervisor_list]
    datacenter = list(set(datacenter))

    ret_val = []
    for dc in datacenter:
        hypervisors = Hypervisor.objects.filter(datacenter=dc)
        num_vm = 0
        storage = 0
        storage_reserved = 0
        mem_reserved = 0
        mem = 0
        threads = 0
        vcpu_reserved = 0
        for hv in hypervisors:
            num_vm += hv.get_number_guest()
            storage += hv.get_datastores_size()
            storage_reserved += hv.diskReserved
            mem_reserved += hv.memoryReserved
            mem += hv.memorySize
            threads += hv.numCpuThreads
            vcpu_reserved += hv.vcpuReserved
        used_storage = int(100 * storage_reserved / storage)
        used_mem = int(100 * mem_reserved / mem)
        cpu_consolidation = float(vcpu_reserved) / threads

        info = {'name': dc,
                'nb_hv': len(hypervisors),
                'nb_guest': num_vm,
                'used_storage': used_storage,
                'used_mem': used_mem,
                'cpu_consolidation': cpu_consolidation
                }
        ret_val.append(info)

    data = {
        'datacenter': ret_val,
    }
    return render_to_response('home.html',
                              data,
                              context_instance=RequestContext(request))


def resourcepool_info(request):
    guest_list = Guest.objects.all()
    resource_pool = [x.resourcePool for x in guest_list]
    resource_pool = list(set(resource_pool))

    ret_val = []
    for rp in resource_pool:
        guests = Guest.objects.filter(resourcePool=rp)
        num_vm = len(guests)
        mem_reserved = 0
        vcpu_reserved = 0
        disk_reserved = 0
        for guest in guests:
            mem_reserved += guest.memory
            vcpu_reserved += guest.vcpu
            disk_reserved += guest.get_disk_reserved(raw=False)
        info = {'name': rp,
                'num_vm': num_vm,
                'mem_reserved': mem_reserved,
                'vcpu_reserved': vcpu_reserved,
                'disk_reserved': disk_reserved,
                }
        ret_val.append(info)

    data = {
        'resource_pool': ret_val,
    }
    return data


def resourcepool(request):
    data = resourcepool_info(request)
    return render_to_response('resourcepool.html',
                              data,
                              context_instance=RequestContext(request))


def top10(request):
    data = resourcepool_info(request)
    d = data['resource_pool']
    data['top10_mem'] = [x['name'] for x in sorted(d, key=lambda a: -a['mem_reserved'])][:10]
    data['top10_cpu'] = [x['name'] for x in sorted(d, key=lambda a: -a['vcpu_reserved'])][:10]
    data['top10_disk'] = [x['name'] for x in sorted(d, key=lambda a: -a['disk_reserved'])][:10]

    return render_to_response('top10.html',
                              data,
                              context_instance=RequestContext(request))


def hypervisors(request):
    hypervisor_list = Hypervisor.objects.all()
    hypervisor_list_sorted = sorted(hypervisor_list, key=lambda a: (a.memoryReserved, a.diskReserved))
    paginator = Paginator(hypervisor_list_sorted, 25)

    page = request.GET.get('page')
    try:
        hypervisors = paginator.page(page)
    except PageNotAnInteger:
        hypervisors = paginator.page(1)
    except EmptyPage:
        hypervisors = paginator.page(paginator.num_pages)

    data = {
        'hypervisor_list': hypervisors,
    }
    return render_to_response('hypervisors.html',
                              data,
                              context_instance=RequestContext(request))


def guests(request):
    guest_list = Guest.objects.all()
    guest_list = guest_list.order_by('name')
    paginator = Paginator(guest_list, 25)

    page = request.GET.get('page')
    try:
        guests = paginator.page(page)
    except PageNotAnInteger:
        guests = paginator.page(1)
    except EmptyPage:
        guests = paginator.page(paginator.num_pages)

    data = {
        'guest_list': guests,
    }
    return render_to_response('guests.html',
                              data,
                              context_instance=RequestContext(request))


def guest_info(request):
    if 'name' in request.GET and request.GET['name']:
        guest_name = request.GET['name']
        guest = Guest.objects.filter(name=guest_name)
        disks = Disk.objects.filter(guest=guest[0])
        vnics = VirtualNic.objects.filter(guest=guest[0])
        data = {
            'guest': guest[0],
            'disks': disks,
            'vnics': vnics,
        }
        return render_to_response('guest.html',
                                  data,
                                  context_instance=RequestContext(request))
    else:
        return HttpResponse('Please submit something !')


def hypervisor_info(request):
    if 'name' in request.GET and request.GET['name']:
        hypervisor_name = request.GET['name']
        hypervisor = Hypervisor.objects.filter(name=hypervisor_name)
        guests = Guest.objects.filter(hypervisor=hypervisor[0])
        datastores = Datastore.objects.filter(hypervisor=hypervisor[0])
        interfaces = Interface.objects.filter(hypervisor=hypervisor[0])
        vswitchs = Vswitch.objects.filter(hypervisor=hypervisor[0])
        networks = Network.objects.filter(vswitch__hypervisor=hypervisor[0])

        data = {
            'hypervisor':   hypervisor[0],
            'guests':       guests,
            'datastores':   datastores.order_by('name'),
            'interfaces':   interfaces,
            'vswitchs':     vswitchs,
            'networks':     networks,
        }
        return render_to_response('hypervisor.html',
                                  data,
                                  context_instance=RequestContext(request))
    else:
        return HttpResponse('Please submit something !')


def search(request):
    if 'filter' in request.GET and request.GET['filter']:
        field = request.GET['filter']
        hypervisors = Hypervisor.objects.filter(name__icontains=field)
        guests = Guest.objects.filter(name__icontains=field)

        data = {
            'hypervisor_list':  hypervisors,
            'guest_list':       guests,
        }
        return render_to_response('search.html',
                                  data,
                                  context_instance=RequestContext(request))
    else:
        return HttpResponse('Please submit something !')
