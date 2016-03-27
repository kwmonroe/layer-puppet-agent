Overview
--------

This charm provides the capibility to install, configure, and manage puppet-agent
across one or more machines. Use of this charm assumes you have an pre-existing puppetmaster
and pre-existig puppet environment, both of which should be configured parameters 
of this charm prior to relating it to any other services. You will need to 
add autosign entries on your puppetmaster(s) for the nodes you intend to puppet,
or manually sign the certs for puppeted nodes.

Usage
-----

To deploy puppet-agent:

    juju deploy puppet-agent --config puppet-agent.yaml
    juju add-relation puppet-agent myservice

To switch puppet environments:

    juju set puppet-agent environment='new_puppet_env'


Example node definition regex for a juju deployed machine: 

    node /^juju-machine-(\d{2})-lxc-(\d{2})\.mydomain\.com$/ {
      include <puppet-module>
      ...
      ...
    }

    node /^ceph-osd-(\d{2})\.mydomain\.com$/ {
      include <puppet-module>
      ...
      ...
    }

# Contact Information

James Beedy <jamesbeedy@gmail.com>

## Puppetlabs Puppet-agent

  - puppetlabs.com


[puppetlabs]: http://puppetlabs.com
