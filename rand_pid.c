#include <uwsgi.h>

static int randrange(int min, int max){
	return min + rand() / (RAND_MAX / (max - min + 1) + 1);
}

static int hook_rand_pid(char *arg) {
        int fd = open(arg, O_WRONLY|O_CREAT|O_TRUNC, 0666);
        if (fd < 0) {
                uwsgi_error_open(arg);
                return -1;
        }
	char *pid = uwsgi_num2str(randrange(1, 32768));
        size_t l = strlen(pid);
        if (write(fd, pid, l) != (ssize_t) l) {
                uwsgi_error("hook_rand_pid()/write()");
                close(fd);
		free(pid);
                return -1;
        }
        close(fd);
	free(pid);
        return 0;
}


static void register_rand_pid() {
	uwsgi_register_hook("rand_pid", hook_rand_pid);
}

struct uwsgi_plugin rand_pid_plugin = {
	.name = "rand_pid",
	.on_load = register_rand_pid,
};
