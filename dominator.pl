use LWP::UserAgent;
use JSON;
use Config::IniFiles;
use POSIX qw(strftime);

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

	my $response =  $ua->get($base_url.'/domains/rsa/');

	if ($response->is_error or $response->code != 200 ) {
		print date().' oops: '.$response->code.' '.$response->message."\n";
		exit;
	}

	my $customers = decode_json($response->decoded_content);

	my %available_domains = {};
	
	foreach(@{$customers}) {
		my $domains = $_->{domains};
		foreach my $domain(@{$domains}) {
			next unless valid_domain($domain->{name})."\n";
			my $domain_pem = '/etc/uwsgi/domains/'.$domain->{name}.'.pem';
			if (-f $domain_pem) {
				my @st = stat($domain_pem);
				if ($domain->{mtime} > $st[9]) {
					write_rsa($domain_pem, $_->{rsa});
				}
			}
			else {
				write_rsa($domain_pem, $_->{rsa});
			}
			$available_domains{$domain->{name}.'.pem'} = 1;
		}
	}

	opendir DIR,'/etc/uwsgi/domains';
	@files = readdir(DIR);
	closedir(DIR);

	foreach(@files) {
		next if /^\./;
		next if $_ eq $cfg->val('uwsgi', 'api_domain').'.pem'; 
		unless(exists($available_domains{$_})) {
			unlink '/etc/uwsgi/domains/'.$_;
			print date().' '.$_." removed\n";
		}
	}

	sleep(30);
}

sub write_rsa {
	my ($domain_file, $rsa) = @_;

	open PEM,'>'.$domain_file;
	print PEM $rsa;
	close(PEM);

	print date().' '.$domain_file." updated\n";
};

sub date {
	return strftime "%Y-%m-%d %H:%M:%S", localtime;
}

sub valid_domain {
	my ($name) = @_;
	return 1 if $name =~ /[a-zA-Z0-9\.\-]/;
	return 0;
}
