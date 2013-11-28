from django.core.validators import RegexValidator
from django.db import models
import re

name_regex = re.compile(r'^[a-zA-Z0-9\-\_\.]+$')


class Hypervisor(models.Model):
    name = models.CharField(max_length=100, unique=True,
                            validators=[RegexValidator(regex=name_regex)])
    cpuModel = models.CharField(max_length=100, blank=True, null=True)
    numCpuPkgs = models.IntegerField()
    vendor = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    numCpuThreads = models.IntegerField()
    memorySize = models.IntegerField()
    numCpuCores = models.IntegerField()
    cpuMhz = models.IntegerField()
    numHBAs = models.IntegerField()
    numNics = models.IntegerField()
    productName = models.CharField(max_length=100, blank=True, null=True)
    productVersion = models.CharField(max_length=20, blank=True, null=True)
    annotation = models.CharField(max_length=100, blank=True, null=True)
    datacenter = models.CharField(max_length=100, unique=False,
                                  validators=[RegexValidator(regex=name_regex)])

    def __unicode__(self):
        return u'%s' % self.name

    def get_number_guest(self):
        guest_list = Guest.objects.filter(hypervisor=self)
        return len(guest_list)

    def get_datastores_size(self):
        ds_list = Datastore.objects.filter(hypervisor=self)
        capacity = 0
        for ds in ds_list:
            capacity += int(ds.capacity)
        return capacity

    def get_mem_reserved(self):
        guest_list = Guest.objects.filter(hypervisor=self)
        mem_reserved = 0
        for guest in guest_list:
            mem_reserved += int(guest.memory)
        return mem_reserved
    memoryReserved = property(get_mem_reserved)

    def get_disk_reserved(self):
        ds_list = Datastore.objects.filter(hypervisor=self)
        disk_reserved = 0
        for ds in ds_list:
            disk_reserved += Datastore.get_reserved(ds)
        return disk_reserved
    diskReserved = property(get_disk_reserved)

    def get_vcpu_reserved(self):
        guest_list = Guest.objects.filter(hypervisor=self)
        vcpu_reserved = 0
        for guest in guest_list:
            vcpu_reserved += int(guest.vcpu)
        return vcpu_reserved
    vcpuReserved = property(get_vcpu_reserved)


class Guest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    poweredOn = models.BooleanField()
    vcpu = models.IntegerField()
    memory = models.IntegerField()
    resourcePool = models.CharField(max_length=100)
    annotation = models.CharField(max_length=100, blank=True, null=True)
    osVersion = models.CharField(max_length=100, blank=True, null=True)
    hypervisor = models.ForeignKey(Hypervisor, unique=False, null=False)

    def __unicode__(self):
        return u'%s.%s' % (self.hypervisor.name, self.name)

    def get_hypervisor_name(self):
        return self.hypervisor.name

    def get_disk_reserved(self):
        disk_list = Disk.objects.filter(guest=self)
        disk_reserved = 0
        for disk in disk_list:
            disk_reserved += int(disk.size)
        return disk_reserved


class Datastore(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    hypervisor = models.ForeignKey(Hypervisor, null=False)

    def __unicode__(self):
        return u'%s.%s' % (self.hypervisor.name, self.name)

    def get_reserved(self):
        vd_list = Disk.objects.filter(datastore=self)
        reserved = 0
        for vd in vd_list:
            if not vd.raw:
                reserved += int(vd.size)
        return reserved

    def get_guests(self):
        disk_list = Disk.objects.filter(datastore=self)
        list_guest = []
        for disk in disk_list:
            if disk.guest not in list_guest:
                list_guest.append(disk.guest)
        return list_guest


class Disk(models.Model):
    name = models.CharField(max_length=100)
    size = models.IntegerField()
    guest = models.ForeignKey(Guest, null=False)
    datastore = models.ForeignKey(Datastore, null=True)
    raw = models.BooleanField(default=False)
    thin = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s' % self.name


class Vswitch(models.Model):
    name = models.CharField(max_length=100)
    hypervisor = models.ForeignKey(Hypervisor, unique=False, null=False)

    def __unicode__(self):
        return u'%s' % self.name


class Network(models.Model):
    name = models.CharField(max_length=100)
    vlanId = models.IntegerField()
    vswitch = models.ForeignKey(Vswitch, unique=False, null=False)

    def __unicode__(self):
        return u'%s.%s' % (self.vswitch, self.name)

    def get_virtualnics(self):
        vnic_list = VirtualNic.objects.filter(network=self)
        return vnic_list


class Interface(models.Model):
    name = models.CharField(max_length=100)
    mac = models.CharField(max_length=100, blank=True, null=True)
    driver = models.CharField(max_length=100, blank=True, null=True)
    linkSpeed = models.IntegerField()
    vswitch = models.ForeignKey(Vswitch, unique=False, null=True)
    hypervisor = models.ForeignKey(Hypervisor, unique=False, null=False)

    def __unicode__(self):
        return u'%s.%s' % (self.hypervisor.name, self.name)


class VirtualNic(models.Model):
    name = models.CharField(max_length=100)
    mac = models.CharField(max_length=100, blank=True, null=True)
    driver = models.CharField(max_length=100, blank=True, null=True)
    guest = models.ForeignKey(Guest, unique=False, null=False)
    network = models.ForeignKey(Network, unique=False, null=False)

    def __unicode__(self):
        return u'%s.%s' % (self.guest.name, self.name)
