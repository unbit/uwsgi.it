from django.db import models
from django.contrib.auth.models import User
import calendar
import ipaddress
import uuid
from django.core.exceptions import ValidationError
import string
from Crypto.PublicKey import RSA
from uwsgi_it_api.config import UWSGI_IT_BASE_UID
import random
import datetime
import os.path


# Create your models here.

generate_uuid = lambda: str(uuid.uuid4())

def generate_rsa():
    return RSA.generate(2048).exportKey()

class Customer(models.Model):
    user = models.OneToOneField(User)
    vat = models.CharField(max_length=255,blank=True,null=True)
    company = models.CharField(max_length=255,blank=True,null=True)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    rsa_key = models.TextField(default=generate_rsa, unique=True)

    @property
    def rsa_key_lines(self):
        return self.rsa_key.split('\n')

    @property
    def rsa_pubkey(self):
        return RSA.importKey(self.rsa_key).publickey().exportKey()

    @property
    def rsa_pubkey_lines(self):
        return self.rsa_pubkey.split('\n')

    def __unicode__(self):
        return self.user.username

class CustomerAttribute(models.Model):
    customer = models.ForeignKey(Customer)
    namespace = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    value = models.TextField(blank=True)

    class Meta:
        unique_together = ( 'customer', 'namespace', 'key')

class Datacenter(models.Model):
    name = models.CharField(max_length=255,unique=True)
    description = models.TextField(blank=True,null=True)
    note = models.TextField(blank=True,null=True)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

class Server(models.Model):
    name = models.CharField(max_length=255,unique=True)
    address = models.GenericIPAddressField()

    hd = models.CharField(max_length=255)

    memory = models.PositiveIntegerField("Memory MB")
    storage = models.PositiveIntegerField("Storage MB")

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    etc_resolv_conf = models.TextField("/etc/resolv.conf", default='',blank=True)
    etc_hosts = models.TextField("/etc/hosts", default='',blank=True)

    weight = models.PositiveIntegerField(default=9999)

    datacenter = models.ForeignKey('Datacenter',null=True,blank=True)

    note = models.TextField(blank=True,null=True)

    owner = models.ForeignKey(Customer,null=True,blank=True)

    ssd = models.BooleanField('SSD', default=False)

    @property
    def used_memory(self):
        n = self.container_set.all().aggregate(models.Sum('memory'))['memory__sum']
        if not n: return 0
        return n

    @property
    def used_storage(self):
        n = self.container_set.all().aggregate(models.Sum('storage'))['storage__sum']
        if not n: return 0
        return n

    @property
    def free_memory(self):
        return self.memory - self.used_memory

    @property
    def free_storage(self):
        return self.storage - self.used_storage

    def __unicode__(self):
        features = []
        if self.ssd:
            features.append('SSD')
        if self.owner:
            features.append('dedicated')
        space = ''
        if features:
            space = ' '
        return "%s - %s%s%s" % (self.name, self.address, space, ','.join(features))

    @property
    def etc_resolv_conf_lines(self):
        return self.etc_resolv_conf.replace('\r', '\n').replace('\n\n', '\n').split('\n')

    @property
    def etc_hosts_lines(self):
        return self.etc_hosts.replace('\r', '\n').replace('\n\n', '\n').split('\n')

    @property
    def munix(self):
        return calendar.timegm(self.mtime.utctimetuple())

class Legion(models.Model):
    name = models.CharField(max_length=255,unique=True)
    address = models.GenericIPAddressField()

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    note = models.TextField(blank=True,null=True)

    customer = models.ForeignKey(Customer,null=True,blank=True)

    key = models.CharField(max_length=64)

    nodes = models.ManyToManyField(Server, through='LegionNode')

    quorum = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return "%s - %s " % (self.name, self.address)

class LegionNode(models.Model):
    legion = models.ForeignKey(Legion)
    server = models.ForeignKey(Server)
    weight = models.PositiveIntegerField(default=9999)

    def __unicode__(self):
        return "%s on %s " % (self.server, self.legion)

class FloatingAddress(models.Model):
    address = models.GenericIPAddressField()
    customer = models.ForeignKey(Customer,null=True,blank=True)
    legion = models.ForeignKey(Legion,null=True,blank=True)
    mapped_to_server = models.ForeignKey(Server,null=True,blank=True)

    note = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return "%s - %s" % (self.address, self.mapped_to_server)

    class Meta:
        verbose_name_plural = 'Floating Addresses'

class Distro(models.Model):
    name = models.CharField(max_length=255,unique=True)
    path = models.CharField(max_length=255,unique=True)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    note = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return self.name


def start_of_epoch():
    return datetime.datetime.fromtimestamp(1)

class Container(models.Model):
    name = models.CharField(max_length=255)
    ssh_keys_raw = models.TextField("SSH keys", blank=True,null=True)
    distro = models.ForeignKey(Distro,null=True,blank=True)
    server = models.ForeignKey(Server)
    # in megabytes
    memory = models.PositiveIntegerField("Memory MB")
    storage = models.PositiveIntegerField("Storage MB")
    customer = models.ForeignKey(Customer)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid, unique=True)

    jid = models.CharField(max_length=255,blank=True,null=True)
    jid_secret = models.CharField(max_length=255,blank=True,null=True)
    jid_destinations = models.CharField(max_length=255,blank=True,null=True)

    quota_threshold = models.PositiveIntegerField("Quota threshold", default=90)

    tags = models.ManyToManyField('Tag', blank=True)

    nofollow = models.BooleanField(default=False)

    note = models.TextField(blank=True,null=True)

    accounted = models.BooleanField(default=False)

    stackedfs_dir = models.CharField(max_length=255,blank=True,null=True)

    last_reboot = models.DateTimeField(default=start_of_epoch)

    ssh_keys_mtime = models.DateTimeField(default=start_of_epoch)

    max_alarms = models.PositiveIntegerField(default=100)

    alarm_key = models.CharField(max_length=36, null=True, blank=True)

    def __unicode__(self):
        return "%d (%s)" % (self.uid, self.name)

    # do not allow over-allocate memory or storage
    def clean(self):
        # hack for empty server value
        try:
            if self.server is None: return
        except:
            return
        current_storage = self.server.container_set.all().aggregate(models.Sum('storage'))['storage__sum']
        current_memory = self.server.container_set.all().aggregate(models.Sum('memory'))['memory__sum']
        if not current_storage: current_storage = 0
        if not current_memory: current_memory = 0
        if self.pk:
            orig = Container.objects.get(pk=self.pk)
            current_storage -= orig.storage
            current_memory -= orig.memory
        if current_storage+self.storage > self.server.storage:
            raise ValidationError('the requested storage size is not available on the specified server')
        if current_memory+self.memory > self.server.memory:
            raise ValidationError('the requested memory size is not available on the specified server')
        if self.stackedfs_dir:
            if os.path.abspath(os.path.join('/', self.stackedfs_dir)) == '/':
                raise ValidationError('invalid stackedfs_dir')

    # force a reboot if required
    def save(self, *args, **kwargs):
        interesting_fields = ('name',
                              'distro', 
                              'server', 
                              'memory', 
                              'storage', 
                              'customer', 
                              'jid', 
                              'jid_secret', 
                              'jid_destinations', 
                              'quota_threshold', 
                              'stackedfs_dir', 
                              'nofollow')
        if self.pk is not None:
            orig = Container.objects.get(pk=self.pk)
            set_reboot = False
            for field in interesting_fields:
                if getattr(self, field) != getattr(orig, field):
                    set_reboot = True
                    break
            if set_reboot:
                self.last_reboot = datetime.datetime.now()
            if self.ssh_keys_raw != orig.ssh_keys_raw:
                self.ssh_keys_mtime = datetime.datetime.now()
        super(Container, self).save(*args, **kwargs)

    @property
    def rand_pid(self):
        return random.randrange(1, 32768)

    @property
    def uid(self):
        return UWSGI_IT_BASE_UID+self.pk

    @property
    def hostname(self):
        h = ''
        allowed = string.ascii_letters + string.digits + '-'
        for char in self.name:
            if char in allowed:
                h += char
            else:
                h += '-'
        return h

    @property
    def ip(self):
        # skip the first two addresses (10.0.0.1 for the gateway, 10.0.0.2 for the api)
        addr = self.pk + 2
        addr0 = 0x0a000000;
        return ipaddress.IPv4Address(addr0 | (addr & 0x00ffffff))

    @property
    def munix(self):
        return calendar.timegm(self.last_reboot.utctimetuple())

    @property
    def ssh_keys_munix(self):
        return calendar.timegm(self.ssh_keys_mtime.utctimetuple())

    @property
    def ssh_keys(self):
        # try to generate a clean list of ssh keys
        if not self.ssh_keys_raw: return []
        cleaned = self.ssh_keys_raw.replace('\r', '\n').replace('\n\n', '\n')
        return cleaned.split('\n')

    @property
    def quota(self):
        return self.storage * (1024*1024)

    @property
    def memory_limit_in_bytes(self):
        return self.memory * (1024*1024)

    @property
    def links(self):
        l = []
        for link in self.containerlink_set.all():
            direction_in = {'direction': 'in', 'src': link.to.ip, 'src_mask': 32, 'dst': link.container.ip, 'dst_mask': 32, 'action': 'allow', 'target': ''}
            direction_out = {'direction': 'out','src': link.container.ip, 'src_mask': 32, 'dst': link.to.ip, 'dst_mask': 32, 'action': 'allow', 'target': ''}
            if link.container.server != link.to.server:
                direction_out['action'] = 'gateway'
                direction_out['target'] = "%s:999" % link.to.server.address
            l.append(direction_in)
            l.append(direction_out)
        return l

    @property
    def linked_to(self):
        return [l.to.uid for l in self.containerlink_set.all()]


class ContainerLink(models.Model):
    container = models.ForeignKey(Container)
    to = models.ForeignKey(Container,related_name='+')

    def __unicode__(self):
        return "%s --> %s" % (self.container, self.to)

    class Meta:
        unique_together = ( 'container', 'to')

    def clean(self):
        if self.container == self.to:
            raise ValidationError("cannot link with myself")


class Loopbox(models.Model):
    container = models.ForeignKey(Container)
    filename = models.CharField(max_length=64)
    mountpoint = models.CharField(max_length=255)
    ro = models.BooleanField(default=False)

    tags = models.ManyToManyField('Tag', blank=True)

    def clean(self):
        checks = ('..', './', '/.', '//')
        starts = ('/',)
        ends = ('/',)
        equals = ('etc', 'logs', 'run', 'tmp', 'vassals')
        for check in checks:
            if check in self.filename:
                raise ValidationError("invalid filename")
            if check in self.mountpoint:
                raise ValidationError("invalid mountpoint")
        for start in starts:
            if self.filename.startswith(start):
                raise ValidationError("invalid filename")
            if self.mountpoint.startswith(start):
                raise ValidationError("invalid mountpoint")
        for end in ends:
            if self.filename.endswith(end):
                raise ValidationError("invalid filename")
            if self.mountpoint.endswith(end):
                raise ValidationError("invalid mountpoint")
        for equal in equals:
            if self.filename == equal:
                raise ValidationError("invalid filename")
            if self.mountpoint == equal:
                raise ValidationError("invalid mountpoint")

    class Meta:
        verbose_name_plural = 'Loopboxes'
        unique_together = (('container', 'filename'), ('container', 'mountpoint'))


class Alarm(models.Model):
    container = models.ForeignKey(Container)
    unix = models.DateTimeField()
    level = models.PositiveIntegerField(choices=((0,'system'), (1, 'user'), (2, 'exception'), (3, 'traceback'), (4, 'log')))
    # in the format #xxxxxx
    color = models.CharField(max_length=7, default='#ffffff')
    msg = models.TextField()

    line = models.PositiveIntegerField(null=True, blank=True)
    func = models.CharField(max_length=255, null=True, blank=True)
    filename = models.CharField(max_length=255, null=True, blank=True)

    _class = models.CharField('class', max_length=255,blank=True,null=True)
    vassal = models.CharField(max_length=255,blank=True,null=True)

    def save(self, *args, **kwargs):
        if len(self.color) != 7:
            raise ValidationError('invalid color')
        if not self.color.startswith('#'):
            raise ValidationError('invalid color')
        # how many alarms ?
        alarms = self.container.alarm_set.count()
        if alarms + 1 > self.container.max_alarms:
            oldest = self.container.alarm_set.all().order_by('unix')[0]
            oldest.delete()
        super(Alarm, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-unix']


"""
domains are mapped to customers, each container of the customer
can subscribe to them
"""
class Domain(models.Model):
    name = models.CharField(max_length=255,unique=True)
    customer = models.ForeignKey(Customer)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    uuid = models.CharField(max_length=36, default=generate_uuid,unique=True)

    note = models.TextField(blank=True,null=True)

    tags = models.ManyToManyField('Tag', blank=True)

    def __unicode__(self):
        return self.name

    @property
    def munix(self):
        return calendar.timegm(self.mtime.utctimetuple())

class Tag(models.Model):
    name = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer)

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    note = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'customer')

class News(models.Model):
    content = models.TextField()
    public = models.BooleanField(default=False)
    
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-ctime']
        verbose_name_plural = 'News'

"""
Pretty low level model for storing customer configurations out of
the container concept (like rawrouter services or https non-sni proxies)
"""
class CustomService(models.Model):
    name = models.CharField(max_length=255,unique=True)
    customer = models.ForeignKey(Customer)
    server = models.ForeignKey(Server)

    config = models.TextField()

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    @property
    def munix(self):
        return calendar.timegm(self.mtime.utctimetuple())

"""
each metric is stored in a different table
"""
class ContainerMetric(models.Model):

    container = models.ForeignKey(Container)

    year = models.PositiveIntegerField(null=True)
    month = models.PositiveIntegerField(null=True)
    day = models.PositiveIntegerField(null=True)

    # this ia blob containing raw metrics
    json = models.TextField(null=True)

    def __unicode__(self):
        return "%s-%s-%s" % (self.year, self.month, self.day)

    class Meta:
        abstract = True
        unique_together = ('container', 'year', 'month', 'day')

class DomainMetric(models.Model):

    domain = models.ForeignKey(Domain)
    container = models.ForeignKey(Container)
    year = models.PositiveIntegerField(null=True)
    month = models.PositiveIntegerField(null=True)
    day = models.PositiveIntegerField(null=True)

    # this ia blob containing raw metrics
    json = models.TextField(null=True)

    def __unicode__(self):
        return "%s-%s-%s" % (self.year, self.month, self.day)

    class Meta:
        abstract = True
        unique_together = ('domain', 'container', 'year', 'month', 'day')

"""
real metrics now
"""

# stores values from the tuntap router
class NetworkRXContainerMetric(ContainerMetric):
    pass

# stores values from the tuntap router
class NetworkTXContainerMetric(ContainerMetric):
    pass

# stores values from the container cgroup
class CPUContainerMetric(ContainerMetric):
    pass

# stores values from the container cgroup
class MemoryContainerMetric(ContainerMetric):
    pass

# stores values from the container cgroup
class IOReadContainerMetric(ContainerMetric):
    pass

# stores values from the container cgroup
class IOWriteContainerMetric(ContainerMetric):
    pass

# uses perl Quota package
class QuotaContainerMetric(ContainerMetric):
    pass

class HitsDomainMetric(DomainMetric):
    pass

class NetworkRXDomainMetric(DomainMetric):
    pass

class NetworkTXDomainMetric(DomainMetric):
    pass

