#include <uwsgi.h>

/*
this alarm is pretty raw but is useful to store "alarms file" out of the namespace context
thanks to the openat() Linux-specific function

on startup (before the namespace is entered) a directory is opened and its fd stored in a global int

whenever an alarm is triggered an openat() call is made creating a file in this directory (even if it is out of the namespace)

the collector.pl daemon takes all the valid alarm files, store them in the uwsgi.it api and remove them.

For avoiding race conditions (like the collector getting files before they are completely written) renameat() is used too
*/

int openat_alarm_global_fd = -1;

static void openat_alarm_init(struct uwsgi_alarm_instance *uai) {
}

static void openat_alarm_func(struct uwsgi_alarm_instance *uai, char *msg, size_t len) {
	
}

static void register_openat_alarm() {
	uwsgi_register_alarm("openat_alarm", openat_alarm_init, openat_alarm_func);
}


struct uwsgi_plugin openat_alarm_plugin = {
	.name = "openat_alarm",
	.on_load = register_openat_alarm,
};
