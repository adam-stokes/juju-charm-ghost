import os
import sys
from charms.reactive import (
    hook,
    when,
    only_once,
    is_state
)

from charmhelpers.core import hookenv, host
from charmhelpers.core.templating import render

# ./lib/nodejs.py
from nodejs import node_dist_dir, npm

# ./lib/ghostlib.py
import ghostlib

config = hookenv.config()


# HOOKS -----------------------------------------------------------------------
@hook('config-changed')
def config_changed():

    if not is_state('nginx.available') or not is_state('nodejs.available'):
        return

    if config.changed('node-version') and config['node-version'] != "0.10":
        hookenv.status_set('blocked',
                           'Ghost has only been tested on Node.js v0.10, '
                           'please update your node-version config '
                           'to "node-version=0.10".')
        sys.exit(0)
    else:
        hookenv.status_set('active', 'ready')

    # Update config on any config items altered
    # if any(config.changed(k) for k in config.keys()):
    target = os.path.join(node_dist_dir(), 'config.js')
    render(source='config.js.template',
           target=target,
           context=config)

    if config.changed('port'):
        hookenv.log('Changing ports: {} -> {}'.format(
            config.previous('port'),
            config['port']
        ))
        hookenv.close_port(config.previous('port'))
        hookenv.open_port(config['port'])

    hookenv.log('Ghost: config-changed, restarting services', 'info')
    ghostlib.restart_ghost()
    host.service_restart('nginx')


# REACTORS --------------------------------------------------------------------
@when('nginx.available', 'nodejs.available')
@only_once
def install_app():
    """ Performs application installation

    This method becomes available once Node.js and NGINX have been
    installed via the install hook and their states are then made
    available (nginx.available, nodejs.installed) which we react on.
    """

    hookenv.log('Installing Ghost', 'info')

    # Update application
    ghostlib.download_archive()
    npm('install --production')
    npm('install forever -g')

    ctx = {
        'dist_dir': node_dist_dir()
    }

    # Render default database
    target = os.path.join(node_dist_dir(), 'dbconfig.js')
    render(source='sqlite.js.template',
           target=target,
           context=ctx)

    # Render upstart job
    # render(source='ghost-upstart.conf',
    #        target='/etc/init/ghost.conf',
    #        context=ctx,
    #        perms=0o644)
    ghostlib.start_ghost()
    host.service_restart('nginx')

    hookenv.status_set('active', 'Ghost is installed, start blogging!')


@when('nginx.available', 'database.available')
def setup_mysql(mysql):
    """ Mysql is available, update Ghost db configuration
    """
    hookenv.status_set('maintenance', 'Ghost is connecting to MySQL!')
    target = os.path.join(node_dist_dir(), 'dbconfig.js')
    render(source='mysql.js.template',
           target=target,
           context=dict(db=mysql))

    ghostlib.restart_ghost()
    host.service_restart('nginx')
    hookenv.status_set('active', 'Ready')


@when('nginx.available', 'website.available')
def configure_website(website):
    hookenv.status_set('maintenance', 'Connecting to an HTTP interface')
    website.configure(port=80)
