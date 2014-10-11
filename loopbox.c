#define _GNU_SOURCE
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/poll.h>
#include <linux/loop.h>
#include <stdarg.h>
#include <errno.h>
#include <sched.h>
#include <sys/mount.h>
#include <time.h>

#define UNBIT_EMPEROR_MAX_NS 64

void loopbox_error(char *fmt, ...) {
	time_t now = time(NULL);
	printf("%.*s - ", 24, ctime(&now));
	va_list arg;
	va_start(arg, fmt);
	vprintf(fmt, arg);
	va_end(arg);
	printf(": %s\n", strerror(errno));
}

int *emperor_ns_attach_fds(int fd) {

        ssize_t len;

        struct cmsghdr *cmsg;
        int *ret;
        int i;

        void *msg_control = malloc(CMSG_SPACE(sizeof(int) * UNBIT_EMPEROR_MAX_NS));
        memset(msg_control, 0, CMSG_SPACE(sizeof(int) * UNBIT_EMPEROR_MAX_NS));

        struct iovec iov;
	// uwsgi-setns + sizeof(int)
        iov.iov_base = malloc(11 + sizeof(int));
        iov.iov_len = 11 + sizeof(int);

        struct msghdr msg;
        memset(&msg, 0, sizeof(msg));

        msg.msg_name = NULL;
        msg.msg_namelen = 0;

        msg.msg_iov = &iov;
        msg.msg_iovlen = 1;

        msg.msg_control = msg_control;
        msg.msg_controllen = CMSG_SPACE(sizeof(int) * UNBIT_EMPEROR_MAX_NS);

        msg.msg_flags = 0;

        len = recvmsg(fd, &msg, 0);
	free(iov.iov_base);
        if (len <= 0) {
		free(msg_control);
                return NULL;
        }

        cmsg = CMSG_FIRSTHDR(&msg);
        if (!cmsg) {
		free(msg_control);
                return NULL;
	}

        if (cmsg->cmsg_level != SOL_SOCKET || cmsg->cmsg_type != SCM_RIGHTS) {
		free(msg_control);
                return NULL;
        }

        if ((size_t) (cmsg->cmsg_len - ((char *) CMSG_DATA(cmsg) - (char *) cmsg)) > (size_t) (sizeof(int) * (UNBIT_EMPEROR_MAX_NS + 1))) {
		free(msg_control);
                return NULL;
        }

        ret = malloc(sizeof(int) * (UNBIT_EMPEROR_MAX_NS + 1));
        for (i = 0; i < UNBIT_EMPEROR_MAX_NS + 1; i++) {
                ret[i] = -1;
        }
        memcpy(ret, CMSG_DATA(cmsg), cmsg->cmsg_len - ((char *) CMSG_DATA(cmsg) - (char *) cmsg));
        free(msg_control);

        return ret;
}


void enter_ns(char *setns_socket) {

	struct sockaddr_un sun;
	memset(&sun, 0, sizeof(struct sockaddr_un));
	sun.sun_family = AF_UNIX;
	// 102 is used in uWSGI as a platform independent limit
	strncpy(sun.sun_path, setns_socket, 102);

	int fd = socket(AF_UNIX, SOCK_STREAM|SOCK_NONBLOCK, 0);
	if (fd < 0) {
		exit(1);
	}

	struct pollfd upoll;
	upoll.fd = fd;
	upoll.events = POLLOUT;

	if (connect(fd, (struct sockaddr *)&sun, sizeof(struct sockaddr_un))) {
		exit(1);
	}

	// max 3 seconds
	int ret = poll(&upoll, 1, 3000);
	if (ret <= 0) {
		exit(1);
	}

	int soopt = 0;
	socklen_t solen = sizeof(int);

	if (getsockopt(fd, SOL_SOCKET, SO_ERROR, (void *) (&soopt), &solen) < 0) {
		exit(1);
	}

	if (soopt) {
		exit(1);
	}

	upoll.events = POLLIN;

	ret = poll(&upoll, 1, 3000);
        if (ret <= 0) {
		exit(1);
        }

	// get ns fds
	int *fds = emperor_ns_attach_fds(fd);
	close(fd);
	if (!fds) {
		exit(1);
	}

	// attach to namespace
	int i;
	int applied = 0;
	for(i=0;i<UNBIT_EMPEROR_MAX_NS;i++) {
		if (fds[i] == -1) {
			break;
		}
		applied++;
		// we are only interested in mount namespace
		if (setns(fds[i], CLONE_NEWNS) < 0) {
			if (errno != EINVAL) {
				exit(1);
			}
		}
	}

	free(fds);
	if (!applied) exit(1);

	// am i in the right mount namespace ?
	struct stat st;
	if (stat("/run/cgroup/tasks", &st)) {
		exit(1);
	}
}

// loopbox mount /containers/uid/run/ns.socket /dev/loopN /containers/uid/filename /containers/uid/mountpoint 0/1
// loopbox umount /containers/uid/run/ns.socket /containers/uid/mountpoint
// loopbox resize /containers/uid/run/ns.socket /dev/loopN /containers/uid/filename
int main(int argc, char *argv[]) {
	// not enough arguments
	if (argc < 4) exit(1);

	char *cmd = argv[1];
	
	// invalid command ?
	if (strcmp(cmd, "umount") &&
		strcmp(cmd, "mount")) {
		// resize is buggy and crash the kernel
		// && strcmp(cmd, "resize")) {
		exit(1);
	}
	
	char *setns_socket = argv[2];

	if (!strcmp(cmd, "umount")) {
		enter_ns(setns_socket);
		if (umount(argv[3])) {
			loopbox_error("[loopbox] error while unmounting %s", argv[3]);
			exit(1);
		}
		time_t now = time(NULL);
		printf("%.*s - [loopbox] %s unmounted\n", 24, ctime(&now), argv[3]);
		exit(0);
	}

	// resize the loop device (buggy)
/*
	if (!strcmp(cmd, "resize")) {
		// enough arguments ?
		if (argc < 5) exit(1);
		struct stat st;
		char *loop = argv[3];
		char *filename = argv[4];
		if (stat(filename, &st)) {
			loopbox_error("[loopbox] unable to resize loop device %s for %s", loop, filename);
			exit(1);
		}

		int loop_fd = open(loop, O_RDWR);
		if (loop_fd < 0) {
			loopbox_error("[loopbox] unable to resize loop device %s for %s", loop, filename);
			exit(1);
		}

		if (ioctl(loop_fd, LOOP_SET_CAPACITY, st.st_size) < 0) {
			loopbox_error("[loopbox] unable to resize loop device %s for %s", loop, filename);
			exit(1);
		}

		printf("[loopbox] loop device %s for %s resized to %llu bytes\n", loop, filename, (unsigned long long) st.st_size);
		exit(0);
	}
*/

	// mount a new loop device
	if (argc < 7) exit(1);
	char *loop = argv[3];
        char *filename = argv[4];
        char *mountpoint = argv[5];
	char *ro = argv[6];

	// get user id
	int uid = atoi(setns_socket + 12);
	if (uid < 30000) exit(1);

	// open /dev/loop-control
	int control_fd = open("/dev/loop-control", O_RDWR|O_CLOEXEC);
	if (control_fd < 0) {
		loopbox_error("[loopbox] unable to create new loop device %s for %s", loop, filename);
		exit(1);
	}

	// ask for /dev/loopN
	int loop_n = atoi(loop+9);
	if (loop_n < 1) exit(1);
	int ret = ioctl(control_fd, LOOP_CTL_ADD, loop_n);
	if (ret < 0) {
		if (errno == EEXIST) {
			int loop_fd = open(loop, O_RDWR|O_CLOEXEC);
			if (loop_fd >= 0) {
				// ignore return value
				ret = ioctl(loop_fd, LOOP_CLR_FD);
				close(loop_fd);
			}
			ret = ioctl(control_fd, LOOP_CTL_REMOVE, loop_n);
			if (ret < 0) {
				loopbox_error("[loopbox] unable to remove old loop device %s", loop);
				exit(1);
			}
			if (ioctl(control_fd, LOOP_CTL_ADD, loop_n) < 0) {
				loopbox_error("[loopbox] unable to create new loop device %s for %s", loop, filename);
				exit(1);
			}
		}
		else {
			loopbox_error("[loopbox] unable to create new loop device %s for %s", loop, filename);
			exit(1);
		}
	}

	// map it to filename

	int loop_fd = open(loop, O_RDWR|O_CLOEXEC);
	if (loop_fd < 0) {
		loopbox_error("[loopbox] unable to create new loop device %s for %s", loop, filename);
		exit(1);
	}

	int filename_fd = open(filename, O_RDWR|O_CLOEXEC);
	if (filename_fd < 0) {
		loopbox_error("[loopbox] unable to create new loop device %s for %s", loop, filename);
		exit(1);
	}

	ret = ioctl(loop_fd, LOOP_SET_FD, filename_fd);
	if (ret < 0) {
		loopbox_error("[loopbox] unable to create new loop device %s for %s", loop, filename);
		exit(1);
	}

	unsigned long mountflags = MS_NOATIME;

	struct loop_info64 li64;
	memset(&li64, 0, sizeof(struct loop_info64));

	strncpy(li64.lo_file_name, filename, LO_NAME_SIZE);
	if (!strcmp(ro, "true")) {
		li64.lo_flags = LO_FLAGS_READ_ONLY;
		mountflags |= MS_RDONLY;
	}

	ret = ioctl(loop_fd, LOOP_SET_STATUS64, &li64);
        if (ret < 0) {
		loopbox_error("[loopbox] unable to create new loop device %s for %s", loop, filename);
                exit(1);
        }


	// enter the namespace
	enter_ns(setns_socket);
	// now mount the device
	
	if (mount(loop, mountpoint, "ext4", mountflags, NULL)) {
		loopbox_error("[loopbox] unable to mount loop device %s to %s", loop, mountpoint);
                exit(1);
	}

	if (!(mountflags & MS_RDONLY)) {
		if (chown(mountpoint, uid, uid)) {
			loopbox_error("[loopbox] unable to chown mountpoint %s", mountpoint);
			umount(mountpoint);
                	exit(1);
		}
	}

	// enable autoclear (the loopback will be destroyed on container death)
	li64.lo_flags |= LO_FLAGS_AUTOCLEAR;
	ret = ioctl(loop_fd, LOOP_SET_STATUS64, &li64);
        if (ret < 0) {
		loopbox_error("[loopbox] unable to set autoclear flag on loop device %s (%s on %s)", loop, filename, mountpoint);
		umount(mountpoint);
		exit(1);
        }

	time_t now = time(NULL);
	printf("%.*s - [loopbox] mounted %s on %s\n", 24, ctime(&now), filename, mountpoint);

	return 0;
}
