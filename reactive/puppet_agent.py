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




class PuppetConfigs:
    def __init__(self):
        self.version = config['puppet-version']
        self.puppet_base_url = 'https://apt.puppetlabs.com'
        self.puppet_conf = 'puppet.conf'
        self.auto_start = ('yes','no')
        self.ensure_running = 'false'
        self.puppet_ssl_dir = '/var/lib/puppet/ssl/'

        if config['puppet-version'] == 4:
            if config['pin-puppet']:
                self.puppet_pkgs = [('puppet-agent=%s' % config['pin-puppet'])]
            else:
                self.puppet_pkgs = ['puppet-agent']
            self.puppet_deb = 'puppetlabs-release-pc1-trusty.deb'
            self.puppet_exe = '/opt/puppetlabs/bin/puppet'
            self.puppet_conf_dir = '/etc/puppetlabs/puppet'
            if config['auto-start']:
                self.ensure_running = 'true'
            self.enable_puppet_cmd = \
                ('%s resource service puppet ensure=running '
                 'enable=%s' % (self.puppet_exe, self.ensure_running))
        elif config['puppet-version'] == 3:
            if config['pin-puppet']:
                self.puppet_pkgs = [('puppet=%s' % config['pin-puppet']),
                                    ('puppet-common=%s' % config['pin-puppet'])]
            else:
                self.puppet_pkgs = ['puppet','puppet-common']
            self.puppet_deb = 'puppetlabs-release-trusty.deb'
            self.puppet_exe = '/usr/bin/puppet'
            self.puppet_conf_dir = '/etc/puppet'
            if config['auto-start']:
                self.auto_start = ('no','yes')
            self.enable_puppet_cmd = ('sed -i /etc/default/puppet ' 
                                      '-e s/START=%s/START=%s/' % self.auto_start)
        else:
            hookenv.log('Only puppet versions 3 and 4 suported')

        self.puppet_conf_ctxt = {
            'environment': config['environment'],
            'puppet_server': config['puppet-server']
        }
        if config['ca-server']:
            self.puppet_conf_ctxt['ca_server'] = config['ca-server']


    def render_puppet_conf(self):
        ''' Render puppet.conf
        '''
        if os.path.exists(self.puppet_conf_path()):
            os.remove(self.puppet_conf_path())
        render(source=self.puppet_conf,
               target=self.puppet_conf_path(),
               owner='root',
               perms=0o644,
               context=self.puppet_conf_ctxt)


    def puppet_conf_path(self):
        '''Return fully qualified path to puppet.conf
        '''
        puppet_conf_path = '%s/%s' % (self.puppet_conf_dir, self.puppet_conf)
        return puppet_conf_path


    def puppet_deb_url(self):
        '''Return fully qualified puppet deb url
        '''
        puppet_deb_url = '%s/%s' % (self.puppet_base_url, self.puppet_deb)
        return puppet_deb_url


    def puppet_deb_temp(self):
        '''Return fully qualified path to downloaded deb
        '''
        puppet_deb_temp = os.path.join('/tmp', self.puppet_deb)
        return puppet_deb_temp


    def puppet_running(self):
    
        '''Enable or disable puppet auto-start
        '''
        call(self.enable_puppet_cmd.split(), shell=False)


def _puppet_active():
    if config['auto-start']:
        hookenv.status_set('active', 
                           'Puppet-agent running')
    else:
        hookenv.status_set('active', 
                           'Puppet-agent installed, but not running')


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
    aufh = ArchiveUrlFetchHandler()
    aufh.download(p.puppet_deb_url(), p.puppet_deb_temp())
    dpkg_puppet_deb = 'dpkg -i %s' % p.puppet_deb_temp()
    call(dpkg_puppet_deb.split(), shell=False)
    apt_update()

    # Clean up
    rm_trusty_puppet_deb = 'rm %s' % p.puppet_deb_temp()
    call(rm_trusty_puppet_deb.split(), shell=False)

    # Install puppet agent from apt
    hookenv.status_set('maintenance', 
                       'Installing puppet-agent: v%s from apt' % \
                       config['puppet-version'])
    apt_install(p.puppet_pkgs)
   
    # Render puppet.conf
    p.render_puppet_conf()

    # Render puppet running
    p.render_pupppet_auto_start()

    # Set status and state
    _puppet_active()
    set_state('puppet-agent.installed')


@when('config.changed.puppet-server')
def puppet_server_config_changed():

    '''React to puppet-server changed
    '''
    p = PuppetConfigs()
    if not config['ca-server']:
        if os.path.isdir(p.puppet_ssl_dir):
            shutil.rmtree(p.puppet_ssl_dir)
    p.render_puppet_conf()
    _puppet_active()


@when('config.changed.puppet-version')
def puppet_version_config_changed():

    '''React to puppet version changed
    '''
    p = PuppetConfigs()
    # Reinstall puppet to specified version
    hookenv.status_set('maintenance',
                       'Re-installing puppet.')
    apt_install(p.puppet_pkgs)
    p.render_puppet_conf()
    _puppet_active()


@when('config.changed.auto-start')
def puppet_auto_start_config_changed():

    '''React to auto-start changed
    '''
    p = PuppetConfigs()
    hookenv.status_set('maintenance',
                       'Configuring auto-start')
    p.puppet_running()
    _puppet_active()


@when('config.changed.environment')
def puppet_environment_config_changed():

    '''React to config-changed
    '''
    p = PuppetConfigs()
    hookenv.status_set('maintenance',
                       'Configuring new puppet env %s' % \
                       config['environment'])
    p.render_puppet_conf()
    _puppet_active()


@when('config.changed.ca-server')
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
    _puppet_active()
