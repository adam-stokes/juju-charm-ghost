import sys
import os
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


# HOOKS -----------------------------------------------------------------------
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
    host.service_stop('ghost')

    if config.changed('port'):
        hookenv.log('Changing ports: {} -> {}'.format(
            config.previous('port'),
            config['port']
        ))
        hookenv.close_port(config.previous('port'))
        hookenv.open_port(config['port'])

    target = os.path.join(node_dist_dir(), 'config.js')
    render(source='config.js.template',
           target=target,
           context=config)

    host.service_start('ghost')
    host.service_restart('nginx')


@hook('start')
def start():
    hookenv.status_set('maintenance', 'Starting Ghost')
    host.service_restart('ghost')
    host.service_restart('nginx')
    hookenv.status_set('active', 'ready')


# REACTORS --------------------------------------------------------------------
@when('nginx.available', 'database.available')
def setup_mysql(mysql):
    """ Mysql is available, update Ghost db configuration
    """
    hookenv.status_set('maintenance', 'Connecting Ghost to MySQL!')
    target = os.path.join(node_dist_dir(), 'dbconfig.js')
    render(source='mysql.js.template',
           target=target,
           context=dict(db=mysql))
    host.service_restart('ghost')
    host.service_restart('nginx')
    hookenv.status_state('active', 'ready')


@when('nginx.available', 'nodejs.installed')
def app_install():
    """ Performs application installation
    """
    remove_state('nodejs.installed')

    # Update application
    download_archive()
    npm('install --production')

    ctx = {
        'dist_dir': node_dist_dir()
    }

    # Render default database
    target = os.path.join(node_dist_dir(), 'dbconfig.js')
    render(source='sqlite.js.template',
           target=target,
           context=ctx)

    # Render upstart job
    render(source='ghost-upstart.conf',
           target='/etc/init/ghost.conf',
           context=ctx,
           perms=0o644)
