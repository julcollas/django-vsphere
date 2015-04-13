#!/usr/bin/env python
from pysphere import VIServer, MORTypes, VIProperty
from optparse import OptionParser
from vsphere.models import VirtualNic
from vsphere.models import Hypervisor
from vsphere.models import Datastore
from vsphere.models import Interface
from vsphere.models import Vswitch
from vsphere.models import Network
from vsphere.models import Guest
from vsphere.models import Disk
from os.path import expanduser
from sys import exit
import ConfigParser
import re


def vmware_connect(host, user, password):
    """Return a VIServer conneciont"""
    s = VIServer()
    s.connect(host, user, password)
    return s


def get_disks(vm):
    """Return a list of disk dict with keys name, size, thin, raw, filename"""
    ret_val = []

    disks = [d for d in vm.properties.config.hardware.device
             if d._type == 'VirtualDisk' and d.backing._type in
             ['VirtualDiskFlatVer1BackingInfo',
              'VirtualDiskFlatVer2BackingInfo',
              'VirtualDiskRawDiskMappingVer1BackingInfo',
              'VirtualDiskSparseVer1BackingInfo',
              'VirtualDiskSparseVer2BackingInfo']]

    for disk in disks:
        name = disk.deviceInfo.label
        size = int(disk.deviceInfo.summary.replace(',', '').replace(' KB', ''))
        size /= 1024
        filename = disk.backing.fileName
        raw = thin = False
        if disk.backing._type == 'VirtualDiskRawDiskMappingVer1BackingInfo':
            raw = True
        if hasattr(disk.backing, "thinProvisioned"):
            thin = True
        ret_val.append({'name': name, 'size': size, 'thin': thin,
                        'raw': raw, 'filename': filename})
    return ret_val


def get_datastores(server):
    """Return a list of datastore dict with keys name, capacity, freeSpace"""
    ret_val = []
    for ds_mor, name in server.get_datastores().items():
        props = VIProperty(server, ds_mor)
        capacity = props.summary.capacity / 1024 / 1024
        freeSpace = props.summary.freeSpace / 1024 / 1024
        ret_val.append({'name': name,
                        'capacity': capacity,
                        'freeSpace': freeSpace})
    return ret_val


def get_networks(server):
    """Return a list a network dict with keys name, vlanId, vswitchName"""
    mor, name = server.get_hosts().items()[0]
    prop = VIProperty(server, mor)
    ret_val = []
    for network in prop.configManager.networkSystem.networkInfo.portgroup:
        name = network.spec.name
        vlanId = network.spec.vlanId
        vswitchName = network.spec.vswitchName
        ret_val.append({'name': name,
                        'vlanId': vlanId,
                        'vswitchName': vswitchName})

    return ret_val


def get_interfaces(prop):
    """Return a list of interface dict with keys driver, linkSpeed, mac,
    name"""
    ret_val = []
    for interface in prop.configManager.networkSystem.networkInfo.pnic:
        name = interface.device
        mac = interface.mac
        driver = interface.driver
        try:
            linkSpeed = interface.linkSpeed.speedMb
        except:
            try:
                linkSpeed = interface.spec.linkSpeed.speedMb
            except:
                linkSpeed = 0
        ret_val.append({'name': name,
                        'mac': mac,
                        'driver': driver,
                        'linkSpeed': linkSpeed})

    return ret_val


def get_vnics(vm):
    """Return a list of vnic dict with keys name, mac, type, network"""
    ret_val = []
    for v in vm.get_property("devices").values():
        if v.get('macAddress'):
            name = v.get('label')
            mac = v.get('macAddress')
            driver = v.get('type')
            network = v.get('summary')
            ret_val.append({'name': name,
                            'mac': mac,
                            'type': driver,
                            'network': network})

    return ret_val


def get_vswitch(server):
    """Return a list of vswitch dict with keys name, nicDevice"""
    mor, name = server.get_hosts().items()[0]
    prop = VIProperty(server, mor)
    ret_val = []
    for v in prop.configManager.networkSystem.networkConfig.vswitch:
        name = v.name
        nicDevice = v.spec.bridge.nicDevice  # this is a list
        ret_val.append({'name': name, 'nicDevice': nicDevice})

    return ret_val


def get_guests(server):
    """Return a list of dict guest"""

    properties = [
        'name',
        'storage.perDatastoreUsage',
        'config.hardware.memoryMB',
        'config.hardware.numCPU'
    ]
    results = server._retrieve_properties_traversal(
        property_names=properties,
        obj_type=MORTypes.VirtualMachine
    )

    ret_val = []
    if not results:
        return ret_val

    for item in results:
        for p in item.PropSet:
            if p.Name == 'config.hardware.memoryMB':
                memory = int(p.Val)
            if p.Name == 'config.hardware.numCPU':
                vcpu = int(p.Val)
            if p.Name == 'name':
                name = p.Val
        try:
            vm = server.get_vm_by_name(name)
        except:
            poweredOn = False
            disks = {}
            osVersion = ''
            annotation = ''
            vnics = []
            resourcePool = vm.get_resource_pool_name()
        else:
            annotation = vm.properties.config.annotation
            osVersion = vm.get_property('guest_full_name')
            poweredOn = vm.is_powered_on()
            disks = get_disks(vm)
            vnics = get_vnics(vm)
            resourcePool = 'Default'

        ret_val.append({'name': name,
                        'vcpu': vcpu,
                        'memory': memory,
                        'disks': disks,
                        'vnics': vnics,
                        'poweredOn': poweredOn,
                        'resourcePool': resourcePool,
                        'annotation': annotation,
                        'osVersion': osVersion})

    return ret_val


def get_hardware(server):
    """Return a hardware dict"""

    mor, name = server.get_hosts().items()[0]
    prop = VIProperty(server, mor)
    overallMemoryUsage = prop.summary.quickStats.overallMemoryUsage
    overallCpuUsage = prop.summary.quickStats.overallCpuUsage
    numCpuThreads = prop.summary.hardware.numCpuThreads
    productName = prop.summary.config.product.name
    productVersion = prop.summary.config.product.version
    numCpuCores = prop.summary.hardware.numCpuCores
    numCpuPkgs = prop.summary.hardware.numCpuPkgs
    cpuModel = prop.summary.hardware.cpuModel
    numHBAs = prop.summary.hardware.numHBAs
    numNics = prop.summary.hardware.numNics
    cpuMhz = prop.summary.hardware.cpuMhz
    memorySize = prop.hardware.memorySize
    vendor = prop.summary.hardware.vendor
    model = prop.summary.hardware.model
    interfaces = get_interfaces(prop)
    datastores = get_datastores(server)

    return {
        'name': name,
        'overallCpuUsage': overallCpuUsage,
        'overallMemoryUsage': overallMemoryUsage,
        'memorySize': memorySize / 1024 / 1024,
        'cpuModel': ' '.join(cpuModel.split()),
        'vendor': vendor,
        'numCpuPkgs': numCpuPkgs,
        'numCpuCores': numCpuCores,
        'numCpuThreads': numCpuThreads,
        'productName': productName,
        'productVersion': productVersion,
        'numNics': numNics,
        'numHBAs': numHBAs,
        'model': model,
        'cpuMhz': cpuMhz,
        'interfaces': interfaces,
        'datastores': datastores,
    }


def create_hypervisor(hypervisor, datacenter, note=''):
    """Create an Hypervisor object from get_hardware and a datacenter"""
    h = Hypervisor()
    h.name = hypervisor.get('name')
    h.cpuModel = hypervisor.get('cpuModel')
    h.numCpuPkgs = hypervisor.get('numCpuPkgs')
    h.vendor = hypervisor.get('vendor')
    h.numCpuThreads = hypervisor.get('numCpuThreads')
    h.memorySize = hypervisor.get('memorySize')
    h.numCpuCores = hypervisor.get('numCpuCores')
    h.cpuMhz = hypervisor.get('cpuMhz')
    h.numHBAs = hypervisor.get('numHBAs')
    h.numNics = hypervisor.get('numNics')
    h.productName = hypervisor.get('productName')
    h.productVersion = hypervisor.get('productVersion')
    h.annotation = note
    h.datacenter = datacenter

    h.clean()
    h.save()
    return h


def create_datastore(datastore, hypervisor):
    """ Create a Datastore object from get_datastores and Hypervisor object"""
    d = Datastore()
    d.name = datastore.get('name')
    d.capacity = datastore.get('capacity')
    d.hypervisor_id = hypervisor.id

    d.clean()
    d.save()
    return d


def create_guest(guest, hypervisor):
    """Create Guest object from get_guests and Hypervisor object"""
    g = Guest()
    g.name = guest.get('name')
    g.memory = guest.get('memory')
    g.poweredOn = guest.get('poweredOn')
    g.vcpu = guest.get('vcpu')
    g.resourcePool = guest.get('resourcePool')
    g.annotation = guest.get('annotation')
    g.osVersion = guest.get('osVersion')
    g.hypervisor = hypervisor

    g.clean()
    g.save()
    return g


def create_disk(disk, datastore, guest):
    """Create a Disk object from get_disks, Datastore and Guest objects"""
    d = Disk()
    d.name = disk.get('name')
    d.size = disk.get('size')
    d.raw = disk.get('raw')
    d.guest = guest
    if not d.raw:
        d.datastore = datastore

    d.clean()
    d.save()
    return d


def create_vswitch(vswitch, hypervisor):
    """Create a Vswitch object from get_vswitch"""
    v = Vswitch()
    v.name = vswitch.get('name')
    v.hypervisor = hypervisor

    v.clean()
    v.save()
    return v


def create_network(network, vswitch):
    """Create a Network object from get_networks and a vswitch object"""
    n = Network()
    n.name = network.get('name')
    n.vlanId = network.get('vlanId')
    n.vswitch = vswitch

    n.clean()
    n.save()
    return n


def create_interface(interface, hypervisor, vswitch=None):
    """Create an Interface object from get_interfaces,
    an Hypervisor and Vswitch objects"""
    i = Interface()
    i.name = interface.get('name')
    i.mac = interface.get('mac')
    i.driver = interface.get('driver')
    i.linkSpeed = interface.get('linkSpeed')
    if vswitch:
        i.vswitch = vswitch
    i.hypervisor = hypervisor

    i.clean()
    i.save()
    return i


def create_vnic(vnic, guest, network):
    """Create a VirtualNic object from get_vnics, an Guest
    and a Network object"""
    v = VirtualNic()
    v.name = vnic.get('name')
    v.mac = vnic.get('mac')
    v.driver = vnic.get('type')
    v.guest = guest
    v.network = network

    v.clean()
    v.save()
    return v


def create_full_hypervisor(server, datacenter, note):
    """Create a full hypervisor with Hardware, interface, network,
    guetst, ..."""
    HARDWARE = get_hardware(server)
    hypervisor = create_hypervisor(HARDWARE, datacenter, note)

    DATASTORES = HARDWARE.get('datastores')
    for ds in DATASTORES:
        create_datastore(ds, hypervisor)

    NETWORKS = get_networks(server)
    VSWITCHS = get_vswitch(server)
    for vswitch in VSWITCHS:
        create_vswitch(vswitch, hypervisor)
    for network in NETWORKS:
        n_vswitchName = network.get('vswitchName')
        n_vswitch = Vswitch.objects.get(name=n_vswitchName,
                                        hypervisor=hypervisor)
        create_network(network, n_vswitch)

    INTERFACES = HARDWARE.get('interfaces')
    for interface in INTERFACES:
        i_vs_name = ''
        i_name = interface.get('name')
        for x in VSWITCHS:
            if i_name in x.get('nicDevice'):
                i_vs_name = x.get('name')
        try:
            n_vswitch = Vswitch.objects.get(name=i_vs_name,
                                            hypervisor=hypervisor)
        except:
            create_interface(interface, hypervisor)
        else:
            create_interface(interface, hypervisor, n_vswitch)

    GUESTS = get_guests(server)
    for guest in GUESTS:
        g = create_guest(guest, hypervisor)

        DISKS = guest.get('disks')
        for disk in DISKS:
            disk_name = disk.get('filename')
            m = re.search(r"\[([A-Za-z0-9_]+)\]", disk_name)
            try:
                disk_ds_name = m.group(1)
                disk_ds = Datastore.objects.get(name=disk_ds_name,
                                                hypervisor=hypervisor)
                create_disk(disk, disk_ds, g)
            except:
                pass

        VNICS = guest.get('vnics')
        for vnic in VNICS:
            vnic_net_name = vnic.get('network')
            try:
                vnic_net = Network.objects.get(name=vnic_net_name,
                                               vswitch__hypervisor=hypervisor)
                create_vnic(vnic, g, vnic_net)
            except:
                pass


if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read(expanduser('~/.hypervisor.ini'))

    parser = OptionParser()
    parser.add_option('-H', '--hostname',
                      help='Host name, IP Address - mandatory')
    parser.add_option('-u', '--user', default='root',
                      help='User name [default: %default]')
    parser.add_option('-d', '--datacenter', default='',
                      help='Datacenter [default: %default]')
    parser.add_option('-p', '--password', type='string', default='',
                      help='Password to connect [default: %default]')
    parser.add_option('-a', '--anotation', type='string', default='',
                      help='Hypervisor Note [default: %default]')

    (options, args) = parser.parse_args()

    mandatories = ['hostname', 'datacenter']

    for m in mandatories:
        if getattr(options, m) is None:
            print '"%s" option is missing' % m
            parser.print_help()
            exit(-1)

    try:
        password = Config.get(options.user, 'password')
    except:
        password = ''

    if getattr(options, 'password'):
        password = options.password
    if not password:
        print '"password" option is missing'
        exit(-1)

    user = options.user
    hostname = options.hostname
    datacenter = options.datacenter
    note = options.anotation

    try:
        server = vmware_connect(hostname, user, password)
    except:
        exit(1)

    create_full_hypervisor(server, datacenter, note)

    server.disconnect()
