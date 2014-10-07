from django.conf import settings
from django.template.loader import render_to_string
import ConfigParser
from collections import OrderedDict
import sys
from Crypto.PublicKey import RSA

class AllowsSameKeys(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super(OrderedDict, self).__setitem__(key, value)

c = ConfigParser.ConfigParser(dict_type=AllowsSameKeys)
c.readfp(open(sys.argv[1]))

# django snippet 646, raise an Exception missing var
class InvalidVarException(object):
    def __mod__(self, missing):
        try:
            missing_str=unicode(missing)
        except:
            missing_str='Failed to create string representation'
        raise Exception('Unknown template variable %r %s' % (missing, missing_str))
    def __contains__(self, search):
        if search=='%s':
            return True
        return False

settings.configure(TEMPLATE_DIRS=('uwsgi_it_api/templates',), TEMPLATE_STRING_IF_INVALID=InvalidVarException())

rsa_key = RSA.generate(2048).exportKey()

container = {
    'name': '30000',
    'hostname': c.get('uwsgi','api_domain')[0].replace('.','-'),
    'uid': 30000,
    'ip': '10.0.0.2',
    'server': {
        'hd':c.get('uwsgi','api_hd')[0],
        'etc_resolv_conf_lines': c.get('uwsgi','api_resolvconf'),
        'etc_hosts_lines': c.get('uwsgi','api_hosts'),
     },
    'quota': 20 * 1024 * 1024 * 1024, 
    'memory_limit_in_bytes': 2048 * 1024 * 1024,
    'distro': {'path': 'precise'},
    'quota_threshold': 90,
    'ssh_keys': c.get('uwsgi','api_ssh_key'),
    'customer': {
        'rsa_key_lines': rsa_key.split('\n'),
        'rsa_pubkey_lines': RSA.importKey(rsa_key).publickey().exportKey().split('\n'),
    },
}

print render_to_string('vassal.ini', {'container': container})
