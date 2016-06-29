from charms.reactive import (
    when,
    when_not,
    is_state,
    set_state,
)

from charmhelpers.core import hookenv, host

# from nodejs layer
from charms.layer.nodejs import npm

# from nginx layer
import nginxlib

# ./lib/charms/ghost.py
from charms import ghost

config = hookenv.config()


@when('nginx.available')
@when_not('ghost.nginx.configured')
def configure_nginx():
    """
    Once nginx is ready, setup our vhost entry.
    """
    nginxlib.configure_site('default', 'vhost.conf')
    set_state('ghost.nginx.configured')


@when('nodejs.available')
@when_not('ghost.forever.installed')
def install_forever():
    """
    Once NodeJS is ready, install the NPM forever package.
    """
    npm('install', 'forever', '-g')
    set_state('ghost.forever.installed')


@when('ghost.nginx.configured', 'ghost.forever.installed')
def check_app_config():
    """
    Check the Ghost application config and possibly update and restart it.
    """
    db_changed = ghost.check_db_changed()

    if not (is_state('config.changed') or db_changed):
        return

    hookenv.status_set('maintenance', 'updating configuration')

    # Update application
    if config.changed('release') or config.changed('checksum'):
        ghost.update_ghost()

    # Update general config
    if is_state('config.changed'):
        ghost.update_general_config()

    # Update database config
    if db_changed:
        ghost.update_db_config()

    ghost.restart_ghost()
    set_state('ghost.running')
    host.service_restart('nginx')
    hookenv.status_set('active', 'ready')


@when('ghost.running', 'website.available')
def configure_website(website):
    website.configure(port=config['port'])
