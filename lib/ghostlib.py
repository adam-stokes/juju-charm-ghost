import sys
from os import path, makedirs
from shutil import rmtree
from charmhelpers.core import hookenv
from hashlib import sha256
from shell import shell

# node-layer
from nodejs import node_dist_dir


def download_archive():

    shell('apt-get install -qy unzip')
    config = hookenv.config()
    shell('rm *.zip || true')
    cmd = ('wget -O ghost.zip https://ghost.org/zip/ghost-{}.zip'.format(
        config['release']))
    hookenv.log("Downloading Ghost: {}".format(cmd))
    shell(cmd)

    with open('ghost.zip', 'rb') as fp:
        dl_byte = sha256(fp.read())
        if dl_byte.hexdigest() != config['checksum']:
            hookenv.status_set(
                'blocked',
                'Downloaded Ghost checksums do not match, '
                'possible corrupt file!')
            sys.exit(0)

    if path.isdir(node_dist_dir()):
        rmtree(node_dist_dir())
    makedirs(node_dist_dir())

    cmd = ('unzip -uo ghost.zip -d {}'.format(
        node_dist_dir()
    ))
    hookenv.log("Extracting Ghost: {}".format(cmd))
    shell(cmd)
