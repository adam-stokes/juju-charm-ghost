import os
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
from ghostlib import download_archive

config = hookenv.config()


# HOOKS -----------------------------------------------------------------------
@hook('config-changed')
def config_changed():

    if not is_state('nginx.available') or not is_state('nodejs.available'):
        return

    # Update config on any config items altered
    if any(config.changed(k) for k in config.keys()):
        host.service_stop('ghost')
        target = os.path.join(node_dist_dir(), 'config.js')
        render(source='config.js.template',
               target=target,
               context=config)
        host.service_restart('ghost')

    if config.changed('port'):
        host.service_stop('ghost')
        hookenv.log('Changing ports: {} -> {}'.format(
            config.previous('port'),
            config['port']
        ))
        hookenv.close_port(config.previous('port'))
        hookenv.open_port(config['port'])
        host.service_restart('ghost')

    host.service_restart('nginx')


# REACTORS --------------------------------------------------------------------
@when('nginx.available', 'nodejs.available')
@only_once
def install():
    """ Performs application installation

    This method becomes available once Node.js and NGINX have been
    installed via the install hook and their states are then made
    available (nginx.available, nodejs.installed) which we react on.
    """

    hookenv.log('Installing Ghost', 'info')

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
    hookenv.status_set('active', 'Ghost is installed, start blogging!')
    host.service_start('ghost')
    host.service_restart('nginx')


@when('nginx.available', 'database.available')
def setup_mysql(mysql):
    """ Mysql is available, update Ghost db configuration
    """
    hookenv.status_set('maintenance', 'Ghost is connecting to MySQL!')
    host.service_stop('ghost')
    target = os.path.join(node_dist_dir(), 'dbconfig.js')
    render(source='mysql.js.template',
           target=target,
           context=dict(db=mysql))

    host.service_start('ghost')
    host.service_restart('nginx')
    hookenv.status_set('active', 'Ready')


@when('nginx.available', 'website.available')
def configure_website(website):
    website.configure(port=80)
