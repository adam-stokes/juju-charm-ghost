from os import path, makedirs
from shutil import rmtree
from charmhelpers.core import hookenv
from charmhelpers.fetch import apt_install
from subprocess import check_call, CalledProcessError

# node-layer
from nodejs import node_dist_dir


def download_archive():

    apt_install(['unzip'])
    config = hookenv.config()
    try:
        check_call('rm *.zip', shell=True)
    except CalledProcessError:
        hookenv.log("No prexisting zips to clean", "debug")

    cmd = ('wget -O ghost.zip https://ghost.org/zip/ghost-{}.zip'.format(
        config['release']))

    hookenv.log("Downloading Ghost: {}".format(cmd))
    check_call(cmd, shell=True)

    if path.isdir(node_dist_dir()):
        rmtree(node_dist_dir())
    makedirs(node_dist_dir())

    cmd = ('unzip -uo ghost.zip -d {}'.format(
        node_dist_dir()
    ))
    hookenv.log("Extracting Ghost: {}".format(cmd))

    check_call(cmd, shell=True)
