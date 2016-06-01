Overview
--------

This is a merge of two other layers:

juju-solutions/layer-puppet (idea(s)shamelessly taken from battlemidget/juju-layer-node)

and

https://github.com/jamesbeedy/layer-puppet-agent

## states emitted

puppet.available - This state is emitted once Puppet packages are installed. Rely on this state to gate a puppet apply operation.

puppet-agent.available - This state is emitted once Puppet is also configured (puppet.conf)

In summary, puppet.available is for masterless functionality, 

puppet-agent.available for puppet daemon and master.

This layer currently only supports ubuntu releases trusty and precise.

# Contact Information

James Beedy <jamesbeedy@gmail.com> / bigdata-dev

## Puppetlabs Puppet-agent

  - [puppetlabs](https://puppetlabs.com)

