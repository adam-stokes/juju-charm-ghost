import os.path as path
import json

from charms.reactive import (
    when,
    when_not,
    is_state,
    set_state,
)

from charmhelpers.core import hookenv, host

from charms.layer import ghost, nginx
from charms.layer.nodejs import npm, node_dist_dir

config = hookenv.config()


@when('nginx.available')
@when_not('ghost.nginx.configured')
def configure_nginx():
    """
    Once nginx is ready, setup our vhost entry.
    """
    nginx.configure_site('default', 'vhost.conf')
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
    cfg_changed = is_state('config.changed')
    db_changed = ghost.check_db_changed()
    if cfg_changed or db_changed or not is_state('ghost.running'):
        hookenv.status_set('maintenance', 'updating configuration')

        try:
            # Update application
            ghost.update_ghost()
        except ghost.ResourceFailure:
            hookenv.status_set('blocked',
                               'unable to get ghost-stable resource')
            return

        # Update general config
        if cfg_changed:
            ghost.update_general_config()

        # Update database config
        if db_changed:
            ghost.update_db_config()

        ghost.restart_ghost()
        set_state('ghost.running')
        host.service_restart('nginx')

        with open(path.join(node_dist_dir(), 'package.json'), 'r') as fp:
            package_json = json.loads(fp.read())

            # Set Ghost application version
            hookenv.application_version_set(package_json['version'])

    hookenv.status_set('active', 'ready')


@when('ghost.running', 'website.available')
def configure_website(website):
    website.configure(port=config['port'])
