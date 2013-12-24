#include <uwsgi.h>

uint32_t unbit_ip(pid_t pid, uid_t uid, gid_t gid) {
        if (uid < 30000) return 0;
        // skip the first address as it is always 10.0.0.1
        uint32_t addr = (uid - 30000)+2;
        uint32_t addr0 = 0x0a000000;
        return htonl(addr0 | (addr & 0x00ffffff));
}

struct uwsgi_plugin calc_ip_plugin = {
	.name = "calc_ip",
};
