#!/usr/bin/python3
# Copyright (c) 2016, James Beedy <jamesbeedy@gmail.com>

import os
import shutil

from charms.reactive import when, when_not, set_state

from charmhelpers.core import hookenv
from charmhelpers.fetch import (
    apt_purge,
    apt_unhold,
)
from charms.layer.puppet import PuppetConfigs
config = hookenv.config()


@when_not('puppet-agent.installed')
def install_puppet_agent():

    '''Install puppet agent
    '''
    p = PuppetConfigs()
    # Download and install trusty puppet deb
    hookenv.status_set('maintenance',
                       'Installing puppet agent')
    hookenv.status_set('maintenance',
                       'Configuring Puppetlabs apt sources')
    PuppetConfigs.install_puppet(p)

    set_state('puppet-agent.installed')


@when('config.set.puppet-server')
@when_not('puppet-agent.configured')
def configure_puppet_agent():
    '''Since the server is set we render
    the puppet config files and ensure puppet service running
    '''
    p = PuppetConfigs()
    PuppetConfigs.configure_puppet(p)

    set_state('puppet-agent.configured')


@when('puppet-agent.installed')
@when_not('puppet.available')
def puppet_masterless_ready():
    '''
    Set the `puppet.available` state so that other layers can
    gate puppet operations for masterless puppet state (unconfigured)
    '''
    set_state('puppet.available')


@when('puppet-agent.installed', 'puppet-agent.configured')
@when_not('puppet-agent.available')
def puppet_agent_ready():

    '''
    Set the `puppet.masterfull.available` state to indicate puppet agent
    is installed, configured and started in master-client state.
    '''
    set_state('puppet-agent.available')


@when('config.changed.puppet-server', 'config.set.puppet-server')
def puppet_server_config_changed():

    '''React to puppet-server changed
    '''
    p = PuppetConfigs()
    if not config['ca-server']:
        if os.path.isdir(p.puppet_ssl_dir):
            shutil.rmtree(p.puppet_ssl_dir)
    p.render_puppet_conf()
    PuppetConfigs.puppet_active(p)


@when('config.changed.pin-puppet')
def puppet_version_config_changed():

    '''React to pin-puppet version changed
    '''
    p = PuppetConfigs()
    # Reinstall puppet to specified version
    hookenv.status_set('maintenance',
                       'Re-installing puppet.')
    if config.previous('pin-puppet') != config['pin-puppet']:
        apt_unhold(p.puppet_purge)
        apt_purge(p.puppet_purge)
        PuppetConfigs.install_puppet(p)


@when('config.changed.auto-start', 'config.set.puppet-server')
def puppet_auto_start_config_changed():

    '''React to auto-start changed
    '''
    p = PuppetConfigs()
    hookenv.status_set('maintenance',
                       'Configuring auto-start')
    p.puppet_running()
    PuppetConfigs.puppet_active(p)


@when('config.changed.environment', 'config.set.puppet-server')
def puppet_environment_config_changed():

    '''React to config-changed
    '''
    p = PuppetConfigs()
    hookenv.status_set('maintenance',
                       'Configuring new puppet env %s' % config['environment'])
    p.render_puppet_conf()
    PuppetConfigs.puppet_active(p)


@when('config.changed.ca-server', 'config.set.puppet-server')
def puppet_ca_server_config_changed():

    '''React to config-changed
    '''
    p = PuppetConfigs()
    # Remove ssl dir if ca-server has changed to avoid
    # cert conflicts with pre-existing, now stale client
    # cert and new puppetmaster cert
    hookenv.status_set('maintenance',
                       'Reconfiguring puppet-agent for new ca-server.')
    if os.path.isdir(p.puppet_ssl_dir):
        shutil.rmtree(p.puppet_ssl_dir)
    p.render_puppet_conf()
    PuppetConfigs.puppet_active(p)
