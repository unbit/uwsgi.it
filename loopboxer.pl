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

for(;;) {
        my $ua = LWP::UserAgent->new;
        $ua->ssl_opts(
                SSL_key_file => $ssl_key,
                SSL_cert_file => $ssl_cert,
        );
        $ua->timeout(3);

        my $response =  $ua->get($base_url.'/loopbacks/');

        if ($response->is_error or $response->code != 200 ) {
                print date().' oops: '.$response->code.' '.$response->message."\n";
                exit;
        }

        my $loopbacks = decode_json($response->decoded_content);

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

        foreach my $lb (@{$loopbacks}) {
                my $pid = get_container_pid($lb->{uid}, $containers_json->{vassals});
                next unless $pid;
                if (check_mountpoint($pid, $lb->{id}, $lb->{filename}, $lb->{mountpoint}, $loopbacks)) {
                        print "need to create /dev/loop".$lb->{id}." from ".$lb->{filename}." on ".$lb->{mountpoint}."\n";
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
                        return $_->{pid};
                }
        }

}

sub check_mountpoint {
        my ($pid, $id, $filename, $mountpoint) = @_;
        my $ret = 1;
        open MOUNTS,'/proc/'.$pid.'/mounts';
        while(<MOUNTS>) {
                my ($device, $dir) = split /\s+/;
                # first check if we need to umount the device
                if ($device =~ /\/dev\/loop(\d+)/) {
                        my $loop = $1;
                        my $found = 0;
                        foreach(@{$loopbacks}) {
                                if ($loop eq $_->{id}) {
                                        $found = 1;
                                        last;
                                }
                        }
                        unless($found) {
                                print "need to remove ".$device."\n";
                        }
                        if ($device eq '/dev/loop'.$id) {
                                $ret = 0;
                                last;
                        }
                }
        }
        close(MOUNTS);
        return $ret;
}
