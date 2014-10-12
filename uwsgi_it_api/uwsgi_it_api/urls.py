from django.conf.urls import patterns

urlpatterns = patterns('uwsgi_it_api.views_private',
    (r'^private/containers/$', 'private_containers'),
    (r'^private/containers/(\d+)\.ini$', 'private_container_ini'),
    (r'^private/ssh_keys/(\d+)$', 'private_container_ssh_keys'),
    (r'^private/legion/nodes/$', 'private_legion_nodes'),
    (r'^private/nodes/$', 'private_nodes'),
    (r'^private/domains/rsa/$', 'private_domains_rsa'),
    (r'^private/custom_services/$', 'private_custom_services'),
    (r'^private/loopboxes/$', 'private_loopboxes'),

    (r'^private/metrics/container.io.read/(\d+)$', 'private_metrics_container_io_read'),
    (r'^private/metrics/container.io.write/(\d+)$', 'private_metrics_container_io_write'),
    (r'^private/metrics/container.net.rx/(\d+)$', 'private_metrics_container_net_rx'),
    (r'^private/metrics/container.net.tx/(\d+)$', 'private_metrics_container_net_tx'),
    (r'^private/metrics/container.cpu/(\d+)$', 'private_metrics_container_cpu'),
    (r'^private/metrics/container.mem/(\d+)$', 'private_metrics_container_mem'),
    (r'^private/metrics/container.quota/(\d+)$', 'private_metrics_container_quota'),

    (r'^private/metrics/domain.net.rx/(\d+)$', 'private_metrics_domain_net_rx'),
    (r'^private/metrics/domain.net.tx/(\d+)$', 'private_metrics_domain_net_tx'),
    (r'^private/metrics/domain.hits/(\d+)$', 'private_metrics_domain_hits'),
)

urlpatterns += patterns('uwsgi_it_api.views',
    (r'^me/?$', 'me'),

    (r'^me/containers/?$', 'containers'),
    (r'^containers/?$', 'containers'),
    (r'^containers/(\d+)$', 'container'),

    (r'^distros/?$', 'distros'),

    (r'^domains/?$', 'domains'),
    (r'^domains/(\d+)$', 'domain'),

    (r'^tags/?$', 'tags'),
    (r'^tags/(\d+)$', 'tag'),

    (r'^news/?$', 'news'),

    (r'^loopboxes/?$', 'loopboxes'),
    (r'^loopboxes/(\d+)$', 'loopbox'),
)

urlpatterns += patterns('uwsgi_it_api.views_metrics',
    (r'^metrics/container.io.read/(\d+)$', 'metrics_container_io_read'),
    (r'^metrics/container.io.write/(\d+)$', 'metrics_container_io_write'),
    (r'^metrics/container.net.rx/(\d+)$', 'metrics_container_net_rx'),
    (r'^metrics/container.net.tx/(\d+)$', 'metrics_container_net_tx'),
    (r'^metrics/container.cpu/(\d+)$', 'metrics_container_cpu'),
    (r'^metrics/container.mem/(\d+)$', 'metrics_container_mem'),
    (r'^metrics/container.quota/(\d+)$', 'metrics_container_quota'),

    (r'^metrics/domain.net.rx/(\d+)$', 'metrics_domain_net_rx'),
    (r'^metrics/domain.net.tx/(\d+)$', 'metrics_domain_net_tx'),
    (r'^metrics/domain.hits/(\d+)$', 'metrics_domain_hits'),

)
