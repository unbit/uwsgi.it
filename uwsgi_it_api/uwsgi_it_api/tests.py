from django.contrib.auth.models import User
from django.contrib.sessions.backends.base import SessionBase
from django.test import TestCase
from django.test.client import RequestFactory

from uwsgi_it_api.views import *
from uwsgi_it_api.views_metrics import *
from uwsgi_it_api.views_private import *

import base64
import datetime

class FakeSession(SessionBase):
    def create(self):
        return

    def delete(self, key=None):
        return

class ViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test', email='test@uwsgi.it', password='top_secret')
        self.basic_auth = 'basic %s' % (base64.b64encode('test:top_secret'))

        # customer api
        self.server, _ = Server.objects.get_or_create(
            name="server",
            address="10.0.0.1",
            hd="hd",
            memory=100,
            storage=100
        )
        self.customer, _ = Customer.objects.get_or_create(user=self.user)
        self.container, _ = Container.objects.get_or_create(
            customer=self.customer,
            server=self.server,
            memory=10,
            storage=10,
            name="container"
        )
        self.c_uid = self.container.uid
        self.domain, _ = Domain.objects.get_or_create(customer=self.customer, name="domain")
        self.tag, _ = Tag.objects.get_or_create(customer=self.customer, name="tag")

        # metrics
        today = datetime.datetime.today()
        NetworkRXContainerMetric.objects.create(
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        NetworkTXContainerMetric.objects.create(
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        CPUContainerMetric.objects.create(
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        MemoryContainerMetric.objects.create(
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        IOReadContainerMetric.objects.create(
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        IOWriteContainerMetric.objects.create(
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        QuotaContainerMetric.objects.create(
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        HitsDomainMetric.objects.create(
            domain=self.domain,
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        NetworkRXDomainMetric.objects.create(
            domain=self.domain,
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )
        NetworkTXDomainMetric.objects.create(
            domain=self.domain,
            container=self.container,
            year=today.year,
            month=today.month,
            day=today.day,
        )

        self.factory = RequestFactory()

    def logged_get_response_for_view(self, path, view, kwargs=None):
        request = self.factory.get(path, {}, HTTP_AUTHORIZATION=self.basic_auth)
        request.user = self.user
        request.session = FakeSession()
        if kwargs is None:
            kwargs = {}
        return view(request, **kwargs)

class ApiTest(ViewsTest):
    def test_me(self):
        response = self.logged_get_response_for_view('/me', me)
        self.assertEqual(response.status_code, 200)

    def test_me_containers(self):
        response = self.logged_get_response_for_view('/me/containers', containers)
        self.assertEqual(response.status_code, 200)

    def test_containers(self):
        response = self.logged_get_response_for_view('/containers', containers)
        self.assertEqual(response.status_code, 200)

    def test_container(self):
        response = self.logged_get_response_for_view('/containers/1', container, {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_distros(self):
        response = self.logged_get_response_for_view('/distros', distros)
        self.assertEqual(response.status_code, 200)

    def test_domains(self):
        response = self.logged_get_response_for_view('/domains', domains)
        self.assertEqual(response.status_code, 200)

    def test_domain(self):
        response = self.logged_get_response_for_view('/domains/1', domain, {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)

    def test_tags(self):
        response = self.logged_get_response_for_view('/tags', tags)
        self.assertEqual(response.status_code, 200)

    def test_tag(self):
        response = self.logged_get_response_for_view('/tags/1', tag, {'id': self.tag.pk})
        self.assertEqual(response.status_code, 200)

        response = self.logged_get_response_for_view('/metrics/container.io.read/1', metrics_container_io_read, {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_io_write(self):
        response = self.logged_get_response_for_view('/metrics/container.io.write/1', metrics_container_io_write, {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_net_rx(self):
        response = self.logged_get_response_for_view('/metrics/container.net.rx/1', metrics_container_net_rx, {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_net_tx(self):
        response = self.logged_get_response_for_view('/metrics/container.net.tx/1', metrics_container_net_tx, {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_cpu(self):
        response = self.logged_get_response_for_view('/metrics/container.cpu/1', metrics_container_cpu, {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_mem(self):
        response = self.logged_get_response_for_view('/metrics/container.mem/1', metrics_container_mem, {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_quota(self):
        response = self.logged_get_response_for_view('/metrics/container.quota/1', metrics_container_quota, {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_domain_net_rx(self):
        response = self.logged_get_response_for_view('/metrics/domain.net.txt/1', metrics_domain_net_rx, {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)

    def test_domain_net_tx(self):
        response = self.logged_get_response_for_view('/metrics/domain.net.rx/1', metrics_domain_net_tx, {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)

    def test_domain_hits(self):
        response = self.logged_get_response_for_view('/metrics/domain.hits/1', metrics_domain_hits, {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)

class PrivateViewsTest(ViewsTest):
    def test_containers(self):
        response = self.logged_get_response_for_view('/private/containers/', private_containers)
        self.assertEqual(response.status_code, 403)

    def test_container(self):
        response = self.logged_get_response_for_view('/private/containers/1.ini', private_container_ini, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_legion_nodes(self):
        response = self.logged_get_response_for_view('/private/legion/nodes/', private_legion_nodes)
        self.assertEqual(response.status_code, 403)

    def test_nodes(self):
        response = self.logged_get_response_for_view('/private/nodes', private_nodes)
        self.assertEqual(response.status_code, 403)

    def test_domains_rsa(self):
        response = self.logged_get_response_for_view('/private/domains/rsa/', private_domains_rsa)
        self.assertEqual(response.status_code, 403)

    def custom_services(self):
        response = self.logged_get_response_for_view('/private/custom_services/', private_custom_services)
        self.assertEqual(response.status_code, 200)

    def test_io_read(self):
        response = self.logged_get_response_for_view('/private/metrics/container.io.read/1', private_metrics_container_io_read, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_io_write(self):
        response = self.logged_get_response_for_view('/private/metrics/container.io.write/1', private_metrics_container_io_write, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_net_rx(self):
        response = self.logged_get_response_for_view('/private/metrics/container.net.rx/1', private_metrics_container_net_rx, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_net_tx(self):
        response = self.logged_get_response_for_view('/private/metrics/container.net.tx/1', private_metrics_container_net_tx, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_cpu(self):
        response = self.logged_get_response_for_view('/private/metrics/container.cpu/1', private_metrics_container_cpu, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_mem(self):
        response = self.logged_get_response_for_view('/private/metrics/container.mem/1', private_metrics_container_mem, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_quota(self):
        response = self.logged_get_response_for_view('/private/metrics/container.quota/1', private_metrics_container_quota, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_domain_net_rx(self):
        response = self.logged_get_response_for_view('/private/metrics/domain.net.txt/1', private_metrics_domain_net_rx, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_domain_net_tx(self):
        response = self.logged_get_response_for_view('/private/metrics/domain.net.rx/1', private_metrics_domain_net_tx, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_domain_hits(self):
        response = self.logged_get_response_for_view('/private/metrics/domain.hits/1', private_metrics_domain_hits, {'id': 1})
        self.assertEqual(response.status_code, 403)

