#include <uwsgi.h>

extern struct uwsgi_server uwsgi;

/*
this alarm is pretty raw but is useful to store "alarms file" out of the namespace context
thanks to the openat() Linux-specific function

on startup (before the namespace is entered) a directory is opened and its fd stored in a global int

whenever an alarm is triggered an openat() call is made creating a file in this directory (even if it is out of the namespace)

the collector.pl daemon takes all the valid alarm files, store them in the uwsgi.it api and remove them.

For avoiding race conditions (like the collector getting files before they are completely written) renameat() is used too
*/

char *openat_alarm_dir = NULL;
int openat_alarm_global_fd = -1;

static struct uwsgi_option openat_alarm_options[] = {
	{"openat-alarm-dir", required_argument, 0, "set the directory for openat-alarm", uwsgi_opt_set_str, &openat_alarm_dir, 0},
	UWSGI_END_OF_OPTIONS
};

static void openat_alarm_init(struct uwsgi_alarm_instance *uai) {
}

// the file format is a simple json:
/*
	{
		"container": xxxxx,
		"unix": yyyy,
		"msg": "...",
	}

	where "container" is the container uid, "unix" is the unix epoch time and "msg" is the raw alarm msg
*/
static void openat_alarm_func(struct uwsgi_alarm_instance *uai, char *msg, size_t len) {
	if (openat_alarm_global_fd < 0) return;
	// generate a uuid (36 bytes + \0 + ".tmp")
	char uuid_tmp[41], uuid[37];
	uwsgi_uuid(uuid_tmp);
	memcpy(uuid_tmp+36, ".tmp\0", 5);
	memcpy(uuid, uuid_tmp, 36);
	uuid[36] = 0;
	int fd = openat(openat_alarm_global_fd, uuid_tmp, O_CREAT|O_WRONLY|O_EXCL, S_IRUSR | S_IWUSR);
	if (fd < 0) {
		uwsgi_log("[alarm] unable to store alarm %.*s\n", 36, uuid_tmp);
		uwsgi_error("openat()");
		return;
	}

	// generate the json {"container":xxxxxx,"unix":yyyyyyyy,"msg":"zzz"}
	struct uwsgi_buffer *ub = uwsgi_buffer_new(uwsgi.page_size);
	if (uwsgi_buffer_append(ub, "{\"container\":", 13)) goto error;
	if (uwsgi_buffer_num64(ub, (int64_t) getuid())) goto error;
	if (uwsgi_buffer_append(ub, ",\"unix\":", 8)) goto error;
	if (uwsgi_buffer_num64(ub, (int64_t) uwsgi_now())) goto error;
	if (uwsgi_buffer_append(ub, ",\"msg\":\"", 8)) goto error;
	if (uwsgi_buffer_append_json(ub, msg, len)) goto error;
	if (uwsgi_buffer_append(ub, "\"}", 2)) goto error;

	ssize_t wlen;
	int attempts = 0;
retry:
	// write the json
	wlen = write(fd, ub->buf, ub->pos);
	// end of memory ?
	if (attempts < 3 && wlen < 0 && errno == ENOMEM) {
		attempts++;
		sleep(1);
		goto retry;
	}
	if (wlen <= 0) {
		uwsgi_error("openat_alarm_func()/write()");
		goto error;
	}

	if ((size_t) wlen != ub->pos) {
		uwsgi_error("openat_alarm_func()/write()");
		goto error;
	}
	
	// close the file
	close(fd);
	uwsgi_buffer_destroy(ub);

	// rename it (remove .tmp suffix)
	if (renameat(openat_alarm_global_fd, uuid_tmp, openat_alarm_global_fd, uuid)) {
		uwsgi_error("openat_alarm_func()/renameat()");
		// do not check for errors
		unlinkat(openat_alarm_global_fd, uuid_tmp, 0);
                goto error;
	}

	return;
error:
	uwsgi_buffer_destroy(ub);
	close(fd);
}

static void register_openat_alarm() {
	uwsgi_register_alarm("openat_alarm", openat_alarm_init, openat_alarm_func);
}

static void openat_alarm_setup() {
	if (!openat_alarm_dir) return;
	openat_alarm_global_fd = open(openat_alarm_dir, O_RDONLY);
	if (openat_alarm_global_fd < 0) {
		uwsgi_error("openat_alarm_init()/open()");
		exit(1);
	}
	struct stat st;
	if (fstat(openat_alarm_global_fd, &st)) {
		uwsgi_error("openat_alarm_init()/fstat()");
		exit(1);
	}

	if (!S_ISDIR(st.st_mode)) {
		uwsgi_log("openat_alarm_dir must be a directory !!!\n");
		exit(1);
	}
}

struct uwsgi_plugin openat_alarm_plugin = {
	.name = "openat_alarm",
	.options = openat_alarm_options,
	.on_load = register_openat_alarm,
	.jail = openat_alarm_setup,
};
