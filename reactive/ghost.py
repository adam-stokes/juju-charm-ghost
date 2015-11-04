from charms.reactive import (
    when,
    set_state
)

from charms.reactive.decorators import when_file_changed
from charmhelpers.core import hookenv, host
from charmhelpers.core.templating import render

# ./lib/nodejs.py
from nodejs import node_dist_dir, npm

# ./lib/ghostlib.py
from ghostlib import download_archive


# REACTORS --------------------------------------------------------------------
@when('nginx.available')
def install_nodejs():
    config = hookenv.config()

    hookenv.log('Installing Node.js {} for Ghost'.format(
        config['node-version']))

    set_state('nodejs.install_runtime')


@when('nodejs.installed')
def app_install():
    """ Performs application installation
    """
    # Update application
    download_archive()
    npm('install --production')

    hookenv.status_set('maintenance', 'Starting Ghost')

    # Render upstart job
    ctx = {
        'dist_dir': node_dist_dir()
    }
    render(source='ghost-upstart.conf',
           target='/etc/init/ghost.conf',
           context=ctx)

    hookenv.status_set('active', 'ready')
    set_state('nginx.start')


@when_file_changed('/etc/init/ghost.conf')
def restart():
    hookenv.status_set('maintenance', 'Restarting Ghost')
    host.service_restart('ghost')
