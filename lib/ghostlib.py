import os
from shutil import rmtree, move
from charmhelpers.core import hookenv
from charmhelpers.fetch import install_remote

# node-layer
from nodejs import node_dist_dir


def download_archive():
    config = hookenv.config()
    dest = install_remote('https://ghost.org/zip/ghost-{}.zip'.format(
        config['node-version']))
    if os.path.isdir(node_dist_dir()):
        rmtree(node_dist_dir())
    move(dest, node_dist_dir())
