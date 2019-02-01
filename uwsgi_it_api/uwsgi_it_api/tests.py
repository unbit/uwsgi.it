from django.contrib.auth.models import User
from django.contrib.sessions.backends.base import SessionBase
from django.test import TestCase
from django.test.client import RequestFactory
from uwsgi_it_api.views import *
from uwsgi_it_api.views_metrics import *
from uwsgi_it_api.views_private import *

import base64
import datetime
import json


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
        self.server_address = "10.0.0.1"

        # customer api
        self.server, _ = Server.objects.get_or_create(
            name="server",
            address=self.server_address,
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
        self.container2, _ = Container.objects.get_or_create(
            customer=self.customer,
            server=self.server,
            memory=10,
            storage=10,
            name="container2"
        )
        self.c_uid = self.container.uid
        self.domain, _ = Domain.objects.get_or_create(customer=self.customer,
                                                      name="domain")
        self.d_uuid = self.domain.uuid
        self.tag, _ = Tag.objects.get_or_create(customer=self.customer,
                                                name="tag")
        self.loopbox, _ = Loopbox.objects.get_or_create(
            container=self.container, filename='filename',
            mountpoint='mountpoint')
        self.loopbox2, _ = Loopbox.objects.get_or_create(
            container=self.container2, filename='filename2',
            mountpoint='mountpoint2')
        self.loopbox3, _ = Loopbox.objects.get_or_create(
            container=self.container, filename='filename3',
            mountpoint='mountpoint3')
        self.l_id = self.loopbox.id
        self.l2_id = self.loopbox2.id
        self.l3_id = self.loopbox3.id
        self.container.tags.add(self.tag)
        self.domain.tags.add(self.tag)
        self.loopbox.tags.add(self.tag)
        self.loopbox2.tags.add(self.tag)
        self.alarms = []
        for i in range(0, 10):
            a = Alarm(container=self.container, msg='test', level=1,
                      unix=datetime.datetime.now())
            a.save()
            self.alarms.append(a)
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

    def logged_get_response_for_view(self, path, view, kwargs=None, params={}):
        headers = {
            'HTTP_AUTHORIZATION': self.basic_auth,
            'HTTPS_DN': 'hithere',
            'REMOTE_ADDR': self.server_address,
        }
        request = self.factory.get(path, params, **headers)
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
        response = self.logged_get_response_for_view('/me/containers',
                                                     containers)
        self.assertEqual(response.status_code, 200)

    def test_containers(self):
        response = self.logged_get_response_for_view('/containers', containers)
        self.assertEqual(response.status_code, 200)

    def test_containers_filters_tags(self):
        response = self.logged_get_response_for_view('/containers', containers,
                                                     params={'tags': 'tag'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"uid": {}'.format(self.c_uid))
        response = self.logged_get_response_for_view('/containers', containers,
                                                     params={'tags': 'fail'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '"uid": {}'.format(self.c_uid))

    def test_container(self):
        response = self.logged_get_response_for_view('/containers/1',
                                                     container,
                                                     {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alarm_freq')

    def test_distros(self):
        response = self.logged_get_response_for_view('/distros', distros)
        self.assertEqual(response.status_code, 200)

    def test_domains(self):
        response = self.logged_get_response_for_view('/domains', domains)
        self.assertEqual(response.status_code, 200)

    def test_domains_filters_tags(self):
        response = self.logged_get_response_for_view('/domains', domains,
                                                     params={'tags': 'tag'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"uuid": "{}"'.format(self.d_uuid))
        response = self.logged_get_response_for_view('/domains', domains,
                                                     params={'tags': 'fail'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'uuid: "{}"'.format(self.d_uuid))

    def test_domain(self):
        response = self.logged_get_response_for_view('/domains/1', domain,
                                                     {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)

    def test_containers_per_domain(self):
        yesterday = today - datetime.timedelta(1)
        HitsDomainMetric.objects.create(
            domain=self.domain,
            container=self.container,
            year=yesterday.year,
            month=yesterday.month,
            day=yesterday.day,
        )
        response = self.logged_get_response_for_view('domains/1/containers', containers_per_domain, {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)

    def test_domains_in_container(self):
        yesterday = today - datetime.timedelta(1)
        HitsDomainMetric.objects.create(
            domain=self.domain,
            container=self.container,
            year=yesterday.year,
            month=yesterday.month,
            day=yesterday.day,
        )
        response = self.logged_get_response_for_view('container/1/domains', domains_in_container, {'id': self.container.pk})
        self.assertEqual(response.status_code, 200)

    def test_loopboxes(self):
        response = self.logged_get_response_for_view('/loopboxes', loopboxes)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"id": {}'.format(self.l_id))
        self.assertContains(response, '"id": {}'.format(self.l2_id))
        self.assertContains(response, '"id": {}'.format(self.l3_id))

    def test_loopboxes_filters_per_container(self):
        response = self.logged_get_response_for_view('/loopboxes', loopboxes,
                                                     params={
                                                         'container': self.c_uid})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"id": {}'.format(self.l_id))
        self.assertContains(response, '"id": {}'.format(self.l3_id))
        self.assertNotContains(response, '"id": {}'.format(self.l2_id))

    def test_loopboxes_filters_per_tag(self):
        response = self.logged_get_response_for_view('/loopboxes', loopboxes,
                                                     params={'tags': 'tag'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"id": {}'.format(self.l_id))
        self.assertContains(response, '"id": {}'.format(self.l2_id))
        self.assertNotContains(response, '"id": {}'.format(self.l3_id))

    def test_loopboxes_filters_per_tag_and_container(self):
        response = self.logged_get_response_for_view('/loopboxes', loopboxes,
                                                     params={'tags': 'tag',
                                                             'container': self.c_uid})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"id": {}'.format(self.l_id))
        self.assertNotContains(response, '"id": {}'.format(self.l2_id))
        self.assertNotContains(response, '"id": {}'.format(self.l3_id))

    def test_loopbox(self):
        response = self.logged_get_response_for_view(
            '/loopboxes/{}'.format(self.l_id), loopbox, {'id': self.l_id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"id": {}'.format(self.l_id))

    def test_alarms_range(self):
        response = self.logged_get_response_for_view('/alarms/', alarms,
                                                     params={'range': '6'})
        self.assertEqual(response.status_code, 200)
        a = json.loads(response.content)
        self.assertEqual(len(a), 6)
        for i in range(0, 6):
            self.assertEqual(a[i]['id'], self.alarms[9 - i].id)

    def test_alarms_range_throws_416(self):
        response = self.logged_get_response_for_view('/alarms/', alarms,
                                                     params={'range': '6-a'})
        self.assertEqual(response.status_code, 416)
        response = self.logged_get_response_for_view('/alarms/', alarms,
                                                     params={'range': '6-'})
        self.assertEqual(response.status_code, 416)
        response = self.logged_get_response_for_view('/alarms/', alarms,
                                                     params={'range': '-a'})
        self.assertEqual(response.status_code, 416)
        response = self.logged_get_response_for_view('/alarms/', alarms,
                                                     params={'range': 'a'})
        self.assertEqual(response.status_code, 416)
        response = self.logged_get_response_for_view('/alarms/', alarms,
                                                     params={'range': ''})
        self.assertEqual(response.status_code, 416)

    def test_alarms_range_between_two_values(self):
        response = self.logged_get_response_for_view('/alarms/', alarms,
                                                     params={'range': '3-6'})
        self.assertEqual(response.status_code, 200)
        a = json.loads(response.content)
        self.assertEqual(len(a), 3)
        for i in range(0, 3):
            self.assertEqual(a[i]['id'], self.alarms[6 - i].id)

    def test_alarms_range_between_two_value_reversed(self):
        response = self.logged_get_response_for_view('/alarms/', alarms,
                                                     params={'range': '6-3'})
        self.assertEqual(response.status_code, 200)
        a = json.loads(response.content)
        self.assertEqual(len(a), 3)
        for i in range(0, 3):
            self.assertEqual(a[i]['id'], self.alarms[3 + i].id)

    def test_tags(self):
        response = self.logged_get_response_for_view('/tags', tags)
        self.assertEqual(response.status_code, 200)

    def test_tag(self):
        response = self.logged_get_response_for_view('/tags/1', tag,
                                                     {'id': self.tag.pk})
        self.assertEqual(response.status_code, 200)

        response = self.logged_get_response_for_view(
            '/metrics/container.io.read/1', metrics_container_io_read,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_io_write(self):
        response = self.logged_get_response_for_view(
            '/metrics/container.io.write/1', metrics_container_io_write,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_net_rx(self):
        response = self.logged_get_response_for_view(
            '/metrics/container.net.rx/1', metrics_container_net_rx,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_net_tx(self):
        response = self.logged_get_response_for_view(
            '/metrics/container.net.tx/1', metrics_container_net_tx,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_cpu(self):
        response = self.logged_get_response_for_view(
            '/metrics/container.cpu/1', metrics_container_cpu,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_mem(self):
        response = self.logged_get_response_for_view(
            '/metrics/container.mem/1', metrics_container_mem,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_quota(self):
        response = self.logged_get_response_for_view(
            '/metrics/container.quota/1', metrics_container_quota,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 200)

    def test_domain_net_rx(self):
        response = self.logged_get_response_for_view(
            '/metrics/domain.net.txt/1', metrics_domain_net_rx,
            {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)

    def test_domain_net_tx(self):
        response = self.logged_get_response_for_view(
            '/metrics/domain.net.rx/1', metrics_domain_net_tx,
            {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)

    def test_domain_hits(self):
        response = self.logged_get_response_for_view('/metrics/domain.hits/1',
                                                     metrics_domain_hits,
                                                     {'id': self.domain.pk})
        self.assertEqual(response.status_code, 200)


class PrivateViewsTest(ViewsTest):
    def test_containers(self):
        response = self.logged_get_response_for_view('/private/containers/',
                                                     private_containers)
        self.assertEqual(response.status_code, 200)

    def test_container(self):
        response = self.logged_get_response_for_view(
            '/private/containers/1.ini', private_container_ini, {'id': 1})
        self.assertEqual(response.status_code, 403)

    def test_legion_nodes(self):
        response = self.logged_get_response_for_view('/private/legion/nodes/',
                                                     private_legion_nodes)
        self.assertEqual(response.status_code, 403)

    def test_nodes(self):
        response = self.logged_get_response_for_view('/private/nodes',
                                                     private_nodes)
        self.assertEqual(response.status_code, 200)

    def test_domains_rsa(self):
        response = self.logged_get_response_for_view('/private/domains/rsa/',
                                                     private_domains_rsa)
        self.assertEqual(response.status_code, 200)

    def custom_services(self):
        response = self.logged_get_response_for_view(
            '/private/custom_services/', private_custom_services)
        self.assertEqual(response.status_code, 200)

    def test_io_read(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/container.io.read/1',
            private_metrics_container_io_read, {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_io_write(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/container.io.write/1',
            private_metrics_container_io_write, {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_net_rx(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/container.net.rx/1',
            private_metrics_container_net_rx, {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_net_tx(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/container.net.tx/1',
            private_metrics_container_net_tx, {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_cpu(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/container.cpu/1', private_metrics_container_cpu,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_mem(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/container.mem/1', private_metrics_container_mem,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_quota(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/container.quota/1',
            private_metrics_container_quota, {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_domain_net_rx(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/domain.net.txt/1', private_metrics_domain_net_rx,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_domain_net_tx(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/domain.net.rx/1', private_metrics_domain_net_tx,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

    def test_domain_hits(self):
        response = self.logged_get_response_for_view(
            '/private/metrics/domain.hits/1', private_metrics_domain_hits,
            {'id': self.c_uid})
        self.assertEqual(response.status_code, 405)

