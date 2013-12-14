from vsphere.models import Hypervisor, Guest, Datastore, Disk, Interface, VirtualNic, Network, Vswitch
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render_to_response
from django.db.models import Min, Max, Avg, Sum
from django.template import RequestContext
from django.http import HttpResponse


def list_deviation(l):
    import math

    def average(s):
        return sum(s) * 1.0 / len(s)
    avg = average(l)
    variance = map(lambda x: (x - avg)**2, l)

    standard_deviation = math.sqrt(average(variance))
    return standard_deviation


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


def resourcepools_info(request):
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


def stats_by_resourcepool(request):
    data = resourcepools_info(request)
    return render_to_response('stats_by_resourcepool.html',
                              data,
                              context_instance=RequestContext(request))


def top10(request):
    data = resourcepools_info(request)
    d = data['resource_pool']
    data['top10_mem'] = [x['name'] for x in sorted(d, key=lambda a: -a['mem_reserved'])][:10]
    data['top10_cpu'] = [x['name'] for x in sorted(d, key=lambda a: -a['vcpu_reserved'])][:10]
    data['top10_disk'] = [x['name'] for x in sorted(d, key=lambda a: -a['disk_reserved'])][:10]

    return render_to_response('top10.html',
                              data,
                              context_instance=RequestContext(request))


def resourcepool_info(rp):

    guest_list = Guest.objects.filter(resourcePool=rp)

    memory_max = guest_list.filter(resourcePool=rp).aggregate(Max('memory'))
    memory_min = guest_list.filter(resourcePool=rp).aggregate(Min('memory'))
    memory_avg = guest_list.filter(resourcePool=rp).aggregate(Avg('memory'))
    memory_sum = guest_list.filter(resourcePool=rp).aggregate(Sum('memory'))
    memory_dev = list_deviation([x.memory for x in guest_list])
    vcpu_max = guest_list.filter(resourcePool=rp).aggregate(Max('vcpu'))
    vcpu_min = guest_list.filter(resourcePool=rp).aggregate(Min('vcpu'))
    vcpu_avg = guest_list.filter(resourcePool=rp).aggregate(Avg('vcpu'))
    vcpu_sum = guest_list.filter(resourcePool=rp).aggregate(Sum('vcpu'))
    vcpu_dev = list_deviation([x.vcpu for x in guest_list])
    storage_list = [x.get_disk_reserved() for x in guest_list]
    storage_max = max(storage_list)
    storage_min = min(storage_list)
    storage_avg = sum(storage_list) / float(len(storage_list))
    storage_sum = sum(storage_list)
    storage_dev = list_deviation(storage_list)

    dc_dict = {}
    for g in guest_list:
        dc = g.hypervisor.datacenter
        if dc not in dc_dict:
            dc_dict[dc] = 1
        else:
            dc_dict[dc] += 1
    dc_count_guest = []
    for dc in dc_dict:
        dc_count_guest.append({'name': dc, 'count': dc_dict.get(dc)})

    info = {
        'name': rp,
        'dc_count_guest': dc_count_guest,
        'guests': guest_list,
        'memory_max': memory_max.get('memory__max'),
        'memory_min': memory_min.get('memory__min'),
        'memory_avg': memory_avg.get('memory__avg'),
        'memory_sum': memory_sum.get('memory__sum'),
        'memory_dev': memory_dev,
        'vcpu_max': vcpu_max.get('vcpu__max'),
        'vcpu_min': vcpu_min.get('vcpu__min'),
        'vcpu_avg': vcpu_avg.get('vcpu__avg'),
        'vcpu_sum': vcpu_sum.get('vcpu__sum'),
        'vcpu_dev': vcpu_dev,
        'storage_max': storage_max,
        'storage_min': storage_min,
        'storage_avg': storage_avg,
        'storage_sum': storage_sum,
        'storage_dev': storage_dev,
    }

    return info


def resourcepool(request):
    rp = request.GET.get('name')
    info = resourcepool_info(rp)
    data = {
        'data': info,
    }
    return render_to_response('resourcepool.html',
                              data,
                              context_instance=RequestContext(request))


def resourcepool_info_list(rp):
    info = resourcepool_info(rp)
    return {
        'name': rp,
        'guests': info.get('guests'),
        'memory_avg': info.get('memory_avg'),
        'storage_avg': info.get('storage_avg'),
        'vcpu_avg': info.get('vcpu_avg'),
    }


def resourcepools(request):
    rp_list = [g.resourcePool for g in Guest.objects.all()]
    rp_list = list(set(rp_list))

    data = []
    for rp in rp_list:
        info = resourcepool_info_list(rp)
        data.append(info)

    paginator = Paginator(data, 25)

    page = request.GET.get('page')
    try:
        data_pag = paginator.page(page)
    except PageNotAnInteger:
        data_pag = paginator.page(1)
    except EmptyPage:
        data_pag = paginator.page(paginator.num_pages)

    data = {
        'resourcepool_list': data_pag,
    }

    return render_to_response('resourcepools.html',
                              data,
                              context_instance=RequestContext(request))


def hypervisors(request):
    hypervisor_list = Hypervisor.objects.all()
    hypervisor_list_sorted = sorted(hypervisor_list,
                                    key=lambda a: (a.memoryReserved - a.memorySize,
                                                   a.diskReserved - a.get_datastores_size()))
    paginator = Paginator(hypervisor_list_sorted, 25)

    page = request.GET.get('page')
    try:
        hypervisors_pag = paginator.page(page)
    except PageNotAnInteger:
        hypervisors_pag = paginator.page(1)
    except EmptyPage:
        hypervisors_pag = paginator.page(paginator.num_pages)

    data = {
        'hypervisor_list': hypervisors_pag,
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
        hypervisor_list = Hypervisor.objects.filter(name__icontains=field)
        guest_list = Guest.objects.filter(name__icontains=field)
        resourcepool_list = [g.resourcePool for g in Guest.objects.all()]
        resourcepool_list = list(set(resourcepool_list))

        data = []
        for rp in [rp for rp in resourcepool_list if field.lower() in rp.lower()]:
            info = resourcepool_info_list(rp)
            data.append(info)

        data = {
            'hypervisor_list':  hypervisor_list,
            'guest_list':       guest_list,
            'resourcepool_list': data,
        }
        return render_to_response('search.html',
                                  data,
                                  context_instance=RequestContext(request))
    else:
        return HttpResponse('Please submit something !')


def interface_statistics(hv):
    inter_list = Interface.objects.filter(
        hypervisor=hv).exclude(vswitch=None)
    ret_val = {}
    for i in inter_list:
        if i.linkSpeed in ret_val:
            ret_val[i.linkSpeed] += 1
        else:
            ret_val[i.linkSpeed] = 1

    return ret_val


def sum_list_dict(l):
    ret_val = {}
    for d in l:
        for k, v in d.items():
            if k not in ret_val:
                ret_val[k] = v
            else:
                ret_val[k] += v
    return ret_val


def datacenter_info(request):
    hypervisor_list = Hypervisor.objects.all()
    ret_val = {}
    for hv in hypervisor_list:
        datacenter = hv.datacenter
        if datacenter not in ret_val:
            ret_val[datacenter] = {'threads': 0, 'vcpu_reserved': 0,
                                   'memory': 0, 'mem_reserved': 0, 'guest': 0,
                                   'hypervisor': 0, 'storage': 0,
                                   'esxiversion': [], 'disk_reserved': 0,
                                   'linkspeed': []}
        ret_val[datacenter]['hypervisor'] += 1
        ret_val[datacenter]['threads'] += hv.numCpuThreads
        ret_val[datacenter]['vcpu_reserved'] += hv.vcpuReserved
        ret_val[datacenter]['memory'] += hv.memorySize
        ret_val[datacenter]['mem_reserved'] += hv.memoryReserved
        ret_val[datacenter]['storage'] += hv.get_datastores_size()
        ret_val[datacenter]['disk_reserved'] += hv.diskReserved
        ret_val[datacenter]['guest'] += hv.get_number_guest()
        ret_val[datacenter]['linkspeed'].append(interface_statistics(hv))
        ret_val[datacenter]['esxiversion'].append({str(hv.productVersion): 1})

    datacenter = []
    for dc in ret_val:
        datacenter.append({
            'datacenter': dc,
            'hypervisor': ret_val[dc]['hypervisor'],
            'storage': ret_val[dc]['storage'],
            'threads': ret_val[dc]['threads'],
            'guest': ret_val[dc]['guest'],
            'vcpu_reserved': ret_val[dc]['vcpu_reserved'],
            'mem_reserved': ret_val[dc]['mem_reserved'],
            'disk_reserved': ret_val[dc]['disk_reserved'],
            'memory': ret_val[dc]['memory'],
            'linkspeed': reduce(lambda x, y: dict((k, v + y[k])
                                                  for k, v in x.iteritems()),
                                ret_val[dc]['linkspeed']),
            'esxiversion': sum_list_dict(ret_val[dc]['esxiversion']),
        })
    data = {
        'data': datacenter,
    }
    return data


def physical_statistics(request):
    data = datacenter_info(request)
    data['esxiversion'] = sum_list_dict([x['esxiversion'] for x in data['data']])
    data['linkspeed'] = sum_list_dict([x['linkspeed'] for x in data['data']])

    return render_to_response('physical.html', data,
                              context_instance=RequestContext(request))


def datacenter_statistics(request):
    data = datacenter_info(request)
    guest_list = Guest.objects.all()

    guest_rp_dc = {}
    for guest in guest_list:
        rp = guest.resourcePool
        dc = guest.hypervisor.datacenter
        if dc not in guest_rp_dc.keys():
            guest_rp_dc[dc] = {}
        if rp not in guest_rp_dc[dc]:
            guest_rp_dc[dc][rp] = 0

        guest_rp_dc[dc][rp] += 1
    u = []
    for dc in guest_rp_dc:
        temp = guest_rp_dc[dc]
        temp['name'] = dc
        u.append(temp)
    data['guest_rp_dc'] = u
    return render_to_response('datacenter.html', data,
                              context_instance=RequestContext(request))
