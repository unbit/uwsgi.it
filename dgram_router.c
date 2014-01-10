#include <uwsgi.h>

extern struct uwsgi_server uwsgi;

/*

	the datagram router (dgram_router) allows you to forward datagrams to one or more peers.
	It is used in the uwsgi.it infrastructure to forward subscription packets to the various fastrouters
	in the cluster

	uwsgi --dgram-router /subscribe/dgram --dgram-router-to 192.68.0.6:2100 --dgram-router-to 192.68.0.7:2100 --dgram-router-bind 192.68.0.5.2100

*/

static struct dgram_router {
	char *addr;
	struct uwsgi_string_list *to;
	char *bind;
	int fd;
	int bind_fd;
	int queue;
} dgr;

static struct uwsgi_option uwsgi_dgram_router_options[] = {
	{"dgram-router", required_argument, 0, "run the dgram router on the specified address", uwsgi_opt_set_str, &dgr.addr, 0},
	{"dgram-router-to", required_argument, 0, "forward each received dgram packet to the specified peer", uwsgi_opt_add_string_list, &dgr.to, 0},
	{"dgram-router-bind", required_argument, 0, "bind to the specified address when forwrding dgram packets", uwsgi_opt_set_str, &dgr.bind, 0},
	UWSGI_END_OF_OPTIONS
};

static void uwsgi_dgram_router_loop(int id, void *arg) {

	dgr.queue = event_queue_init();

	void *events = event_queue_alloc(64);
	if (event_queue_add_fd_read(dgr.queue, dgr.fd))
		exit(1);

	for (;;) {
		int i;
		int nevents = event_queue_wait_multi(dgr.queue, -1, events, 64);
		for (i = 0; i < nevents; i++) {
			int interesting_fd = event_queue_interesting_fd(events, i);
			if (interesting_fd == dgr.fd) {
				char buf[8192];
				ssize_t rlen = read(interesting_fd, buf, 8192);
				if (rlen < 0) {
					if (uwsgi_is_again()) continue;
					uwsgi_error("uwsgi_dgram_router_loop()/read()");
					exit(1);
				}

				if (rlen > 0) {
					struct uwsgi_string_list *usl;
					uwsgi_foreach(usl, dgr.to) {
						if (sendto((int) usl->custom, buf, rlen, 0, (const struct sockaddr *) usl->custom_ptr, (socklen_t) usl->custom2) < 0) {
							uwsgi_error("uwsgi_dgram_router_loop()/sendto()");
						}
					}
				}
			}

		}
	}
}

static int uwsgi_dgram_router_init() {

	if (!dgr.addr) return 0;

	char *colon = strchr(dgr.addr, ':');
	if (colon) {
		dgr.fd = bind_to_udp(dgr.addr, 0, 0);
	}
	else {
		dgr.fd = bind_to_unix_dgram(dgr.addr);
	}

	uwsgi_socket_nb(dgr.fd);

	dgr.bind_fd = -1;

	if (dgr.bind) {
		colon = strchr(dgr.bind, ':');
		if (colon) {
			dgr.bind_fd = bind_to_udp(dgr.bind, 0, 0);
        	}
        	else {
                	dgr.bind_fd = bind_to_unix_dgram(dgr.bind);
        	}
		uwsgi_socket_nb(dgr.bind_fd);
	}

	// prepare sockets and addresses
	struct uwsgi_string_list *usl;
        uwsgi_foreach(usl, dgr.to) {
		char *udp_port = strchr(usl->value, ':');
		if (udp_port) {
			*udp_port = 0;
			struct sockaddr_in *udp_addr = uwsgi_calloc(sizeof(struct sockaddr_in));
               		udp_addr->sin_family = AF_INET;
               		udp_addr->sin_port = htons(atoi(udp_port + 1));
               		udp_addr->sin_addr.s_addr = inet_addr(usl->value);
               		*udp_port = ':';
			if (dgr.bind_fd > -1) {
				usl->custom = (uint64_t) dgr.bind_fd;
			}
			else {
				int bfd = socket(AF_INET, SOCK_DGRAM, 0);
				if (bfd < 0) {
					uwsgi_error("uwsgi_dgram_router_init()/socket()");
					exit(1);
				}
				uwsgi_socket_nb(bfd);
				usl->custom = (uint64_t) bfd;
			}
			usl->custom_ptr = udp_addr;
			usl->custom2 = sizeof(struct sockaddr_in);
        	}
        	else {
			struct sockaddr_un *un_addr = uwsgi_calloc(sizeof(struct sockaddr_un));
               		un_addr->sun_family = AF_UNIX;
               		// use 102 as the magic number
               		strncat(un_addr->sun_path, usl->value, 102);
			if (dgr.bind_fd > -1) {
                        	usl->custom = (uint64_t) dgr.bind_fd;
                	}
                	else {
                        	int bfd = socket(AF_UNIX, SOCK_DGRAM, 0);
                        	if (bfd < 0) {
                                	uwsgi_error("uwsgi_dgram_router_init()/socket()");
                                	exit(1);
                        	}
				uwsgi_socket_nb(bfd);
                        	usl->custom = (uint64_t) bfd;
                	}
                	usl->custom_ptr = un_addr;
                	usl->custom2 = sizeof(struct sockaddr_un);
		}
	}

	if (register_gateway("uWSGI dgram router", uwsgi_dgram_router_loop, NULL) == NULL) {
		uwsgi_log("unable to register the dgram router gateway\n");
		exit(1);
	}

	return 0;
}

struct uwsgi_plugin dgram_router_plugin = {
	.name = "dgram_router",
	.options = uwsgi_dgram_router_options,
	.init = uwsgi_dgram_router_init,
};
