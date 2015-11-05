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
    # Install Node.js
    if not is_state('nodejs.installed'):
        hookenv.log('Installing Node.js {} for Ghost'.format(
            config['node-version']))
        node_switch(config['node-version'])

    # Node.js installed, Install NGINX
    set_state('nginx.install')


@hook('config-changed')
def config_changed():

    # Update config on any config items altered
    if any(config.changed(k) for k in config.keys()):
        host.service_stop('ghost')
        target = os.path.join(node_dist_dir(), 'config.js')
        render(source='config.js.template',
               target=target,
               context=config)

    if config.changed('port'):
        host.service_stop('ghost')
        hookenv.log('Changing ports: {} -> {}'.format(
            config.previous('port'),
            config['port']
        ))
        hookenv.close_port(config.previous('port'))
        hookenv.open_port(config['port'])

    host.service_start('ghost')
    host.service_restart('nginx')


@hook('start')
def start():
    hookenv.status_set('maintenance', 'Starting Ghost')
    host.service_start('ghost')
    host.service_restart('nginx')
    hookenv.status_set('active', 'ready')


# REACTORS --------------------------------------------------------------------
@when('nginx.available', 'database.available')
def setup_mysql(mysql):
    """ Mysql is available, update Ghost db configuration
    """
    host.service_stop('ghost')

    hookenv.status_set('maintenance', 'Connecting Ghost to MySQL!')
    target = os.path.join(node_dist_dir(), 'dbconfig.js')
    render(source='mysql.js.template',
           target=target,
           context=dict(db=mysql))

    host.service_start('ghost')
    host.service_restart('nginx')
    hookenv.status_set('active', 'ready')


@when('nginx.available', 'nodejs.installed')
def app_install():
    """ Performs application installation

    This method becomes available once Node.js and NGINX have been
    installed via the install hook and their states are then made
    available (nginx.available, nodejs.installed) which we react on.
    """

    # Make sure this state doesn't re-trigger an install loop
    # TODO: Maybe I'm doing it wrong?
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
