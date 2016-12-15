import sys
from os import path, listdir, unlink
from shutil import rmtree
from charmhelpers.core import hookenv
from charmhelpers.core import host
from charmhelpers.core import unitdata
from charmhelpers.core.templating import render
from subprocess import call, check_call, check_output
from charms.reactive.relations import RelationBase
from charms.reactive.helpers import data_changed

# node-layer
from charms.layer.nodejs import node_dist_dir, npm
kv = unitdata.kv()


def download_archive():
    check_call(['apt-get', 'install', '-qy', 'unzip'])
    config = hookenv.config()
    ghost_source = hookenv.resource_get('ghost-stable')
    kv.set('checksum', host.file_hash(ghost_source, 'sha256'))

    # delete the app dir contents (but not the dir itself)
    dist_dir = node_dist_dir()
    for entry in listdir(dist_dir):
        if path.isfile(entry):
            unlink(entry)
        elif path.isdir(entry):
            rmtree(entry)

    cmd = ('unzip', '-uo', ghost_source, '-d', dist_dir)
    hookenv.log("Extracting Ghost: {}".format(' '.join(cmd)))
    check_call(cmd)


def check_db_changed():
    mysql = RelationBase.from_state('database.available')
    db_data = []
    if mysql:
        db_data.extend((
            mysql.host(),
            mysql.port(),
            mysql.database(),
            mysql.user(),
            mysql.password()
        ))
    return data_changed('ghost.db', db_data)


def update_ghost():
    stop_ghost()
    download_archive()
    npm('install', '--production')


def update_general_config():
    config = hookenv.config()
    target = path.join(node_dist_dir(), 'config.js')
    render(source='config.js.template',
           target=target,
           context=config)

    if config.changed('port'):
        hookenv.log('Changing ports: {} -> {}'.format(
            config.previous('port'),
            config['port']
        ))
        if config.previous('port'):
            hookenv.close_port(config.previous('port'))
        hookenv.open_port(config['port'])


def update_db_config():
    mysql = RelationBase.from_state('database.available')
    db_type = 'mysql' if mysql else 'sqlite'
    hookenv.log('Updating database config, using: %s' % db_type)
    render(source='%s.js.template' % db_type,
           target=path.join(node_dist_dir(), 'dbconfig.js'),
           context={
               'db': mysql,
               'dist_dir': node_dist_dir(),
           })


def ghost_running():
    with host.chdir(node_dist_dir()):
        output = check_output(['env', 'NODE_ENV=production', 'forever',
                               'list'])
        return 'index.js' in output.decode('utf8')


def start_ghost():
    if not ghost_running():
        with host.chdir(node_dist_dir()):
            check_call(['env', 'NODE_ENV=production', 'forever',
                        '-l', '/var/log/ghost.log', '-a', 'start', 'index.js'])


def stop_ghost():
    if ghost_running():
        with host.chdir(node_dist_dir()):
            check_call(['env', 'NODE_ENV=production', 'forever',
                        'stop', 'index.js'])


def restart_ghost():
    cmd = 'restart' if ghost_running() else 'start'
    with host.chdir(node_dist_dir()):
        check_call(['env', 'NODE_ENV=production', 'forever',
                    '-l', '/var/log/ghost.log', '-a', cmd, 'index.js'])
