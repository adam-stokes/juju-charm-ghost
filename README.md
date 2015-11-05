# Overview

Ghost is an Open Source application which allows you to write and publish your
own blog, giving you the tools to make it easy and even fun to do. It's simple,
elegant, and designed so that you can spend less time making your blog work and
more time blogging.

This is an updated charm originally written by Jeff Pihach and ported over to
the charms.reactive framework and updated for Trusty and the latest Ghost release.

# Quick Start

After you have a Juju cloud environment running:

    $ juju deploy ghost
    $ juju expose ghost

To access your newly installed blog you'll need to get the IP of the instance.

    $ juju status ghost

Visit `<your URL>:2368/ghost/` to create your username and password.
Continue setting up Ghost by following the
[usage documentation](http://docs.ghost.org/usage/).

You will want to change the URL that Ghost uses to generate links internally to
the URL you will be using for your blog.

    $ juju set ghost url=<your url>

# Configuration

To view the configuration options for this charm open the `config.yaml` file or:

    $ juju get ghost

To set a configuration option for this charm:

    $ juju set ghost <key>=<value>

See the `config.yaml` file in the charm for a detailed list of all of the charms
configuration options.


# Setting Up Email Service

Ghost needs the ability to send emails to users for things like new user
validation and password resets. To accomplish this Ghost supports using a
third party email service which it can communicate with to send these emails.
Ghost, and this charm, supports sending emails using Mailgun, Amazon SES, and
Gmail. Additional information about why Ghost needs this service and it's
supported platforms see [Mail configuration](http://support.ghost.org/mail/).

To specify a supported email service to use you simply need to set the
configuration values in the charm and they will be generated for your Ghost
instance.

#### Mailgun & Gmail

    $ juju set ghost mailserver_username=<your username>
    $ juju set ghost mailserver_password=<your password>
    Then
    $ juju set ghost mail_service=Mailgun
    -or-
    $ juju set ghost mail_service=Gmail

#### Amazon SES

    $ juju set ghost mailserver_username=<your username>
    $ juju set ghost mailserver_password=<your password>
    $ juju set ghost amazon_ses_host=<your ses host>
    Then
    $ juju set ghost mail_service=SES

After this has been completed your Ghost server will restart and Ghost will
now be able to send emails using that provider. It's recommended to test this
before you need it by creating a new user and pointing it to an email you
control and ensure that you get the validation email.


# Connecting To MySQL

By default this charm uses Ghost's built in SQLite storage. If you would like to
horizontally scale your ghost instance you will need to use an external database
like MySQL.

**If you already have blog posts in the SQLite database they will not be
deleted, but you will have to manually port them over to the MySQL database.**

First you will need to deploy MySQL into your Juju environment:

    $ juju deploy mysql

Additional details about the MySQL charm and configuration can be found in the
[MySQL charm details](https://jujucharms.com/mysql/precise/) page.

You'll then need to relate the Ghost blog service to the MySQL service.

    $ juju add-relation ghost mysql

The charm will then handle setting up all configuration options necessary to use
the MySQL database instead of the internal SQLite database.

# Load Balancing

    $ juju deploy haproxy
    $ juju expose haproxy
    $ juju unexpose ghost
    $ juju add-relation ghost haproxy

# Contributing

## Original charm

This charm is ported over from the original excellent charm @
[ghost-charm repository](https://github.com/hatched/ghost-charm)

## Current charm updated for Trusty and using charms.reactive

[juju-layer-ghost](https://github.com/battlemidget/juju-layer-ghost)


# Bug Reports

Please file bugs for the Ghost blogging engine in the
[TryGhost Ghost repository](https://github.com/TryGhost/Ghost) and not in the
ghost-charm repository.

If you have found a bug with the ghost-charm itself they can be filed in the
[juju-layer-ghost repository](https://github.com/battlemidget/juju-layer-ghost).
Please include exact steps to reproduce the issue and be as detailed as
possible, including what version of Ubuntu you're running on, the version of
this charm you have deployed, the cloud your environment is running on, any
other charms deployed to the environment.
