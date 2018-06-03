use bigint;
use LWP::UserAgent;
use JSON -support_by_pp;
use Config::IniFiles;
use POSIX qw(strftime);
use IO::Socket::INET;

# required for --log-master
STDOUT->autoflush(1);

$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME}=0;

my $cfg = Config::IniFiles->new( -file => "/etc/uwsgi/local.ini" );

my $base_url = 'https://'.$cfg->val('uwsgi', 'api_domain').'/api/private';
my $ssl_key = $cfg->val('uwsgi', 'api_client_key_file');
my $ssl_cert = $cfg->val('uwsgi', 'api_client_cert_file');

my $timeout = 30;

for(;;) {
        my $ua = LWP::UserAgent->new;
        $ua->ssl_opts(
                SSL_key_file => $ssl_key,
                SSL_cert_file => $ssl_cert,
        );
        $ua->timeout($timeout);

        my $response =  $ua->get($base_url.'/loopboxes/');

        if ($response->is_error or $response->code != 200 ) {
                print date().' oops: '.$response->code.' '.$response->message."\n";
                exit;
        }

        my $loopboxes = decode_json($response->decoded_content);

        my $containers_json = undef;
        # get json stats from the Emperor stats
        my $s = IO::Socket::INET->new(PeerAddr => '127.0.0.1:5001');
        if ($s) {
                my $json = '';
                for(;;) {
                        $s->recv(my $buf, 8192);
                        last unless $buf;
                        $json .= $buf;
                }
                $containers_json = decode_json($json);
        }

        foreach my $lb (@{$loopboxes}) {
                my $pid = get_container_pid($lb->{uid}, $containers_json->{vassals});
                next unless $pid;
                if (check_mountpoint($pid, $lb->{uid}, $lb->{id}, $lb->{filename}, $lb->{mountpoint}, $loopboxes)) {
			my $cmd = '/etc/uwsgi/loopbox mount /containers/'.$lb->{uid}.'/run/ns.socket /dev/loop'.$lb->{id}.' /containers/'.$lb->{uid}.'/'.$lb->{filename}.' /containers/'.$lb->{uid}.'/'.$lb->{mountpoint}.' '.$lb->{ro};
			print date().' running '.$cmd."\n";	
			system($cmd.' >> /containers/'.$lb->{uid}.'/logs/emperor.log');
                }
        }

	
	foreach(@{$containers_json->{vassals}}) {
		if (!$_->{checked}) {
			unmount_all($_);
		}
	}

        sleep(30);
}

sub date {
        return strftime "%Y-%m-%d %H:%M:%S", localtime;
}

sub get_container_pid {
        my ($uid, $vassals) = @_;
        foreach(@{$vassals}) {
                if ($uid.'.ini' eq $_->{id}) {
			$_->{checked} = 1;
                        return $_->{pid};
                }
        }

}
sub unmount_all {
	my ($vassal) = @_;
	open MOUNTS,'/proc/'.$vassal->{pid}.'/mounts';
        while(<MOUNTS>) {
                my ($device, $dir) = split /\s+/;
                if ($device =~ /\/dev\/loop\d+/) {
			my $uid = $vassal->{id};
			$uid =~ s/\.ini$//;
			umount($uid, $dir);
		}
	}
	close(MOUNTS);
}

sub check_mountpoint {
        my ($pid, $uid, $id, $filename, $mountpoint, $loopboxes) = @_;
        my $ret = 1;
        # first check if we need to umount devices
        open MOUNTS,'/proc/'.$pid.'/mounts';
        while(<MOUNTS>) {
                my ($device, $dir) = split /\s+/;
                if ($device =~ /\/dev\/loop(\d+)/) {
                        my $loop = $1;
                        my $found = 0;
                        foreach(@{$loopboxes}) {
                                if ($loop eq $_->{id}) {
                                        $found = 1;
                                        last;
                                }
                        }
                        unless($found) {
				umount($uid, $dir);
                        }
		}
	}
	close(MOUNTS);

	open MOUNTS,'/proc/'.$pid.'/mounts';
	while(<MOUNTS>) {
                my ($device, $dir) = split /\s+/;
		if ($device =~ /\/dev\/loop(\d+)/) {
                        my $loop = $1;
                        my $found = 0;
                        foreach(@{$loopboxes}) {
                                if ($loop eq $_->{id}) {
                                        $found = 1;
                                        last;
                                }
                        }
			# exit in case of incongruence
                        last unless($found);

                        if ($device eq '/dev/loop'.$id) {
				# check if the size of the file is changed
				open SYSFS, '/sys/class/block/loop'.$id.'/size';
				my $sectors = <SYSFS>;
				close SYSFS;	
				my @st = stat('/containers/'.$uid.'/'.$filename);
				# deleted file ?
				unless(@st) {
					umount($uid, $dir);
					$ret = 0;
                                	last;
				}
				# invalid file size ?
				my $size = $st[7];
				if ($size < (1024*1024)) {
					umount($uid, $dir);
					$ret = 0;
                                	last;
				}
				# file decreased in size ?
				$file_sectors = $size/512;
				if ($file_sectors < $sectors) {
					umount($uid, $dir);
					$ret = 0;
                                	last;
				}
				# at least 1 megabyte more
				if ($file_sectors > $sectors + (2048)) {
					umount($uid, $dir);
					# calling resize2fs on a loopback device under a namespace
					# make the kernel hang ... :( disable it for now
					#my $cmd = '/etc/uwsgi/loopbox resize /containers/'.$uid.'/run/ns.socket /dev/loop'.$id.' /containers/'.$uid.'/'.$filename;
        				#print date().' running '.$cmd."\n";
					#system($cmd);
				}
                                $ret = 0;
                                last;
                        }
                }
        }
        close(MOUNTS);
        return $ret;
}

sub umount {
	my ($uid, $dir) = @_;
	my $cmd = '/etc/uwsgi/loopbox umount /containers/'.$uid.'/run/ns.socket '.$dir;
        print date().' running '.$cmd."\n";
	system($cmd.' >> /containers/'.$uid.'/logs/emperor.log');
}
