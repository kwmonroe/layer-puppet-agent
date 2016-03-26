#!/usr/bin/python3
# Copyright (c) 2016, James Beedy <jamesbeedy@gmail.com>

import os
import sys
import shutil
from subprocess import call

from charms.reactive import when, when_not, set_state

from charmhelpers.core.templating import render
from charmhelpers.core import hookenv
from charmhelpers.fetch import (
    apt_install,
    apt_update
)
from charmhelpers.fetch.archiveurl import (
    ArchiveUrlFetchHandler
)

config = hookenv.config()

PUPPET_VERSION = config['puppet-version']
PUPPET_BASE_URL = 'https://apt.puppetlabs.com'
PUPPET_CONF = 'puppet.conf'
ENABLE_PUPPET_CMD = None

if config['auto-start']:
    AUTO_START = ('no','yes')
else:
    AUTO_START = ('yes','no')


if PUPPET_VERSION.startswith('2'):
    PUPPET_DEB = 'puppetlabs-release-pc1-trusty.deb'
    PUPPET_PKGS = [('puppet-agent=%s' % PUPPET_VERSION)]
    PUPPET_EXE = '/opt/puppetlabs/bin/puppet'
    PUPPET_CONF_DIR = '/etc/puppetlabs/puppet'
    if config['auto-start']:
        ENABLE_PUPPET_CMD = ('%s resource service puppet ensure=running '
                             'enable=true' % PUPPET_EXE)
else:
    PUPPET_DEB = 'puppetlabs-release-trusty.deb'
    PUPPET_PKGS = [('puppet=%s' % PUPPET_VERSION),
                         ('puppet-common=%s' % PUPPET_VERSION)]
    PUPPET_EXE = '/usr/bin/puppet'

    PUPPET_CONF_DIR = '/etc/puppet'
    if config['auto-start']:
        ENABLE_PUPPET_CMD = ('sed -i /etc/default/puppet ' 
                             '-e s/START=%s/START=%s/' % AUTO_START)

PUPPET_CONF_PATH = '%s/%s' % (PUPPET_CONF_DIR, PUPPET_CONF)
PUPPET_DEB_URL = '%s/%s' % (PUPPET_BASE_URL, PUPPET_DEB)
PUPPET_DEB_TEMP = os.path.join('/tmp', PUPPET_DEB)

PUPPET_CONF_CTXT = {
    'environment': config['environment'],
    'puppet_server': config['puppet-server']
}

if config['ca-server']:
    PUPPET_CONF_CTXT['ca_server'] = config['ca-server']


def render_puppet_conf(ctxt):

    """ Render puppet.conf
    """
    if os.path.exists(PUPPET_CONF_PATH):
        os.remove(PUPPET_CONF_PATH)
    render(source=PUPPET_CONF,
           target=PUPPET_CONF_PATH,
           owner='root',
           perms=0o644,
           context=ctxt)


@when_not('puppet-agent.installed')
def install_puppet_agent():

    """ Install puppet agent
    """
    # Download and install trusty puppet deb
    hookenv.status_set('maintenance', 
                       'Installing puppet agent')
    hookenv.status_set('maintenance', 
                       'Configuring Puppetlabs apt sources')
    aufh = ArchiveUrlFetchHandler()
    aufh.download(PUPPET_DEB_URL, PUPPET_DEB_TEMP)
    dpkg_puppet_deb = 'dpkg -i %s' % PUPPET_DEB_TEMP
    call(dpkg_puppet_deb.split(), shell=False)
    apt_update()

    # Clean up
    rm_trusty_puppet_deb = 'rm %s' % PUPPET_DEB_TEMP
    call(rm_trusty_puppet_deb.split(), shell=False)

    # Install puppet agent from apt
    hookenv.status_set('maintenance', 
                       'Installing puppet agent version: %s' % PUPPET_VERSION)
    apt_install(PUPPET_PKGS)
   
    # Render puppet.conf
    render_puppet_conf(PUPPET_CONF_CTXT)
    # Enable auto-start
    if config['auto-start']:
        call(ENABLE_PUPPET_CMD.split(), shell=False)
    set_state('puppet-agent.installed')
