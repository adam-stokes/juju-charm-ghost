import sys
from charms.reactive import (
    hook,
    when,
    is_state,
    set_state,
    remove_state
)

from charmhelpers.core import hookenv, host
from charmhelpers.core.templating import render

# ./lib/nodejs.py
from nodejs import node_dist_dir, npm, node_switch

# ./lib/ghostlib.py
from ghostlib import download_archive

config = hookenv.config()


@hook('install')
def install():
    hookenv.log("Python version: {}".format(sys.version_info), 'debug')

    if not is_state('nodejs.installed'):
        hookenv.log('Installing Node.js {} for Ghost'.format(
            config['node-version']))
        node_switch(config['node-version'])
    set_state('nginx.install')


@hook('config-changed')
def config_changed():
    hookenv.log('Previous Ghost Release: {} Changed: {}'.format(
        config.previous('ghost-release'),
        config.changed('ghost-release')))


@hook('start')
def start():
    hookenv.status_set('maintenance', 'Starting Ghost')
    host.service_restart('ghost')
    host.service_restart('nginx')
    hookenv.status_set('active', 'ready')


@when('nginx.available', 'nodejs.installed')
def app_install():
    """ Performs application installation
    """
    remove_state('nodejs.installed')

    # Update application
    download_archive()
    npm('install --production')

    # Render upstart job
    ctx = {
        'dist_dir': node_dist_dir()
    }
    render(source='ghost-upstart.conf',
           target='/etc/init/ghost.conf',
           context=ctx)
