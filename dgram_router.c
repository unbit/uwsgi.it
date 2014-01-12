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
	char *psk_in;
	char *psk_out;
	EVP_CIPHER_CTX *encrypt_ctx;
	EVP_CIPHER_CTX *decrypt_ctx;
	char *encrypt_buf;
	char *decrypt_buf;
} dgr;

static struct uwsgi_option uwsgi_dgram_router_options[] = {
	{"dgram-router", required_argument, 0, "run the dgram router on the specified address", uwsgi_opt_set_str, &dgr.addr, 0},
	{"dgram-router-to", required_argument, 0, "forward each received dgram packet to the specified peer", uwsgi_opt_add_string_list, &dgr.to, 0},
	{"dgram-router-bind", required_argument, 0, "bind to the specified address when forwrding dgram packets", uwsgi_opt_set_str, &dgr.bind, 0},
	{"dgram-router-psk-in", required_argument, 0, "set a preshared key for decrypting incoming traffic (syntax: algo:secret [iv])", uwsgi_opt_set_str, &dgr.psk_in, 0},
	{"dgram-router-psk-out", required_argument, 0, "set a preshared key for encrypting outgoing traffic (syntax: algo:secret [iv])", uwsgi_opt_set_str, &dgr.psk_out, 0},
	UWSGI_END_OF_OPTIONS
};

static const EVP_CIPHER *setup_secret_and_iv(char *arg, char **secret, char **iv) {

	char *colon = strchr(arg, ':');
	if (!colon) {
		uwsgi_log("invalid dgram-router psk syntax, must be: <algo>:<secret> [iv]\n");
		exit(1);
	}

	*colon = 0;

	const EVP_CIPHER *cipher = EVP_get_cipherbyname(arg);
        if (!cipher) {
                uwsgi_log("unable to find algorithm/cipher %s\n", arg);
                exit(1);
        }

	*colon = ':';

	*secret = colon+1;
	*iv = NULL;

	char *space = strchr(colon+1, ' ');
	if (space) {
		*space = 0;
		*iv = space+1;
	}

	int cipher_len = EVP_CIPHER_key_length(cipher);
        size_t s_len = strlen(*secret);
        if ((unsigned int) cipher_len > s_len) {
                char *secret_tmp = uwsgi_malloc(cipher_len);
                memcpy(secret_tmp, *secret, s_len);
                memset(secret_tmp + s_len, 0, cipher_len - s_len);
                *secret = secret_tmp;
        }

        int iv_len = EVP_CIPHER_iv_length(cipher);
        size_t s_iv_len = 0;

        if (*iv) {
                s_iv_len = strlen(*iv);
        }

        if ((unsigned int) iv_len > s_iv_len) {
                char *secret_tmp = uwsgi_malloc(iv_len);
                memcpy(secret_tmp, *iv, s_iv_len);
                memset(secret_tmp + s_iv_len, '0', iv_len - s_iv_len);
                *iv = secret_tmp;
        }

	if (space) *space = ' ';

	return cipher;
}

static ssize_t encrypt_packet(char *buf, size_t len) {

        if (EVP_EncryptInit_ex(dgr.encrypt_ctx, NULL, NULL, NULL, NULL) <= 0) {
                uwsgi_error("EVP_EncryptInit_ex()");
		return -1;
        }

        int e_len = 0;
        if (EVP_EncryptUpdate(dgr.encrypt_ctx, (unsigned char *) dgr.encrypt_buf, &e_len, (unsigned char *) buf, len) <= 0) {
                uwsgi_error("EVP_EncryptUpdate()");
		return -1;
        }

        int tmplen = 0;
        if (EVP_EncryptFinal_ex(dgr.encrypt_ctx, (unsigned char *) (dgr.encrypt_buf + e_len), &tmplen) <= 0) {
                uwsgi_error("EVP_EncryptFinal_ex()");
		return -1;
        }

	return e_len + tmplen;
}

static ssize_t decrypt_packet(char *buf, size_t len) {

        if (EVP_DecryptInit_ex(dgr.decrypt_ctx, NULL, NULL, NULL, NULL) <= 0) {
                uwsgi_error("EVP_DecryptInit_ex()");
                return -1;
        }

        int d_len = 0;
        if (EVP_DecryptUpdate(dgr.decrypt_ctx, (unsigned char *)dgr.decrypt_buf, &d_len, (unsigned char *) buf, len) <= 0) {
                uwsgi_error("EVP_DecryptUpdate()");
                return -1;
        }

        int tmplen = 0;
        if (EVP_DecryptFinal_ex(dgr.decrypt_ctx, (unsigned char *) (dgr.decrypt_buf + d_len), &tmplen) <= 0) {
                uwsgi_error("EVP_DecryptFinal_ex()");
                return -1;
        }

        return d_len + tmplen;
}


static void uwsgi_dgram_router_loop(int id, void *arg) {

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

				char *buf2 = buf;

				if (dgr.psk_in) {
					rlen = decrypt_packet(buf, rlen);
					if (rlen < 0) continue;
					buf2 = dgr.decrypt_buf;
				}

				if (dgr.psk_out) {
					rlen = encrypt_packet(buf2, rlen);
					if (rlen < 0) continue;
					buf2 = dgr.encrypt_buf;	
				}

				if (rlen > 0) {
					struct uwsgi_string_list *usl;
					uwsgi_foreach(usl, dgr.to) {
						if (sendto((int) usl->custom, buf2, rlen, 0, (const struct sockaddr *) usl->custom_ptr, (socklen_t) usl->custom2) < 0) {
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

	if (dgr.psk_in) {
		if (!uwsgi.ssl_initialized) uwsgi_ssl_init();	
		char *secret = NULL;
		char *iv = NULL;
		dgr.decrypt_ctx = uwsgi_malloc(sizeof(EVP_CIPHER_CTX));
		EVP_CIPHER_CTX_init(dgr.decrypt_ctx);
		const EVP_CIPHER *cipher = setup_secret_and_iv(dgr.psk_in, &secret, &iv);
		if (EVP_DecryptInit_ex(dgr.decrypt_ctx, cipher, NULL, (const unsigned char *) secret, (const unsigned char *) iv) <= 0) {
                	uwsgi_error("EVP_DecryptInit_ex()");
                	exit(1);
        	}
		dgr.decrypt_buf = uwsgi_malloc(8192 + EVP_MAX_BLOCK_LENGTH);
	}

	if (dgr.psk_out) {
		if (!uwsgi.ssl_initialized) uwsgi_ssl_init();	
		char *secret = NULL;
		char *iv = NULL;
                dgr.encrypt_ctx = uwsgi_malloc(sizeof(EVP_CIPHER_CTX));
                EVP_CIPHER_CTX_init(dgr.encrypt_ctx);
                const EVP_CIPHER *cipher = setup_secret_and_iv(dgr.psk_out, &secret, &iv);
                if (EVP_EncryptInit_ex(dgr.encrypt_ctx, cipher, NULL, (const unsigned char *) secret, (const unsigned char *) iv) <= 0) {
                        uwsgi_error("EVP_EncryptInit_ex()");
                        exit(1);
                }
		dgr.encrypt_buf = uwsgi_malloc(8192 + EVP_MAX_BLOCK_LENGTH);
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
