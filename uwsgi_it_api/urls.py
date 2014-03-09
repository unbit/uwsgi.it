from django.conf.urls import patterns

urlpatterns = patterns('uwsgi_it_api.views',
    (r'^private/containers/$', 'private_containers'),
    (r'^private/containers/(\d+)\.ini$', 'private_container_ini'),
    (r'^private/legion/nodes/$', 'private_legion_nodes'),
    (r'^private/nodes/$', 'private_nodes'),
    (r'^private/domains/rsa/$', 'private_domains_rsa'),
    (r'^private/custom_services/$', 'private_custom_services'),
    (r'^private/metrics/container.io.read/(\d+)$', 'private_metrics_container_io_read'),
    (r'^private/metrics/container.io.write/(\d+)$', 'private_metrics_container_io_write'),
    (r'^private/metrics/container.net.rx/(\d+)$', 'private_metrics_container_net_rx'),
    (r'^private/metrics/container.net.tx/(\d+)$', 'private_metrics_container_net_tx'),
    (r'^private/metrics/container.cpu/(\d+)$', 'private_metrics_container_cpu'),
    (r'^private/metrics/container.mem/(\d+)$', 'private_metrics_container_mem'),
    (r'^private/metrics/container.quota/(\d+)$', 'private_metrics_container_quota'),

    (r'^me/?$', 'me'),
    (r'^me/containers/?$', 'containers'),
    (r'^containers/?$', 'containers'),
    (r'^containers/(\d+)$', 'container'),
    (r'^distros/?$', 'distros'),
    (r'^domains/?$', 'domains'),
    (r'^domains/(\d+)$', 'domain'),

    (r'^containers/(\d+)/metrics/cpu$', 'container_metrics_cpu'),

    (r'^tags/?$', 'tags'),
    (r'^tags/(\d+)$', 'tag'),
)
