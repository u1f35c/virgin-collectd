These are a couple of Python scripts to collect statistics information from
[Virgin Media](https://www.virginmedia.com/) cable modems (originally SuperHub
v1 and the SuperHub v3; I've never had a SuperHub v2) and pass the information
into [collectd](https://collectd.org/). I no longer have a Virgin line, but I'm
releasing these scripts, rough and ready as they are, in the hope they may be
of use to others.

At present the configured upstream/downstream line rate and the per channel
upstream/downstream power levels are logged, but the scripts could easily be
extended to log more details if required. I found this useful to discover when
Virgin had regraded my line to a higher speed, and track potential issues due
to line quality problems.

To use with collectd you will need to put the scripts somewhere appropriate (I
went for `/usr/local/lib/collectd/`) - copy the appropriate version for your
cable modem as `collectd_virgin_cm`, possibly change URLBASE to point to the IP
address yours lives on (I was running it in modem mode) and edit
`/etc/collectd/collectd.conf` (assuming that's where your collectd config
lives) to ensure the

    LoadPlugin python

line is uncommented. You will also need to add a configuration stanza:

    <Plugin python>
        ModulePath "/usr/local/lib/collectd"
        Import "collectd_virgin_cm"
        <Module collectd_virgin_cm>
        </Module>
    </Plugin>

Note on implementation: For the SuperHub v1 the script screen scrapes the web
interface to obtain the appropriate information. There's a strong potential for
this to break if Virgin change the firmware but I suspect there's not a lot of
development going on for these devices (when they sent me a replacement v3 hub
they did not want the v1 returned). The v3 interface offers a sort of SNMP over
HTTP JSON interface, so I suspect is likely to be more stable (and is certainly
easier to parse).
