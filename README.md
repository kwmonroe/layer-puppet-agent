Overview
--------

Puppet-agent provides the capibility to install, configure, and control puppet agent
across one or more machines. Use of this charm assumes you have an existing puppetmaster
and puppet environment defined, both of which should be configured parameters of this charm prior
to relating it to any other services.

Usage
-----

To deploy puppet-agent:

    juju deploy puppet-agent --config puppet-agent.yaml
    juju add-relation puppet-agent myservice

To switch puppet environments:

    juju set puppet-agent environment='new_puppet_env'


I like to add a generic node definition in my puppet environment to handle
the juju named containers:

    node /^juju-machine-(\d{2})-lxc-(\d{2})\.mydomain\.com$/ {
      include <puppet-module>
      ...
      ...
    }
