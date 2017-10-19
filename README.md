PrivacyScore
============

PrivacyScore is a platform for investigating security and privacy issues on websites. It is inspired by tools like the [Qualys SSL test](https://www.ssllabs.com/ssltest/) and [Webbkoll](https://github.com/andersju/webbkoll), but aims to be more comprehensive and offer additional features like

- Comparing and ranking whole lists of sites
- Checking for embedded third parties that are known trackers
- Periodically rescanning each website and checking how the results change over time
- Be completely open source (GPLv3) and easily extendable

At the moment, the code should be considered beta quality. To try the system out, visit **[privacyscore.org](https://privacyscore.org/).**

## Used dependencies
PrivacyScore relies on the following libraries and frameworks:

- [Django](https://www.djangoproject.com/) (BSD)
- [OpenWPM](https://github.com/citp/OpenWPM) (GPLv3)
- [testssl.sh](https://github.com/drwetter/testssl.sh) (GPLv2)¹
- [Celery](http://www.celeryproject.org/) (BSD)
- [adblockparser](https://github.com/scrapinghub/adblockparser) (MIT)
- [dnspython](https://github.com/rthalley/dnspython) (ISC)
- [geoip2](https://github.com/maxmind/GeoIP2-python) (Apache v2)
- [Pillow](https://github.com/python-pillow/Pillow) (PIL)
- [Redis](https://redis.io/) (BSD)
- [Requests](http://docs.python-requests.org/en/master/) (Apache v2)
- [tldextract](https://github.com/john-kurkowski/tldextract) (BSD)
- [toposort](https://bitbucket.org/ericvsmith/toposort) (Apache)
- [url_normalize](https://github.com/niksite/url-normalize) (PSF)
- [pygments](http://pygments.org/) (BSD)

We are grateful to the maintainers and contributors of the respective projects.

¹ We have obtained permission from the maintainer of testssl.sh to combine his GPLv2 code with GPLv3 code in the context of this project

## Deployment

This describes the steps that are necessary to deploy the code to a new machine.

* Make sure you have the following values stored in your [pass](https://www.passwordstore.org/):
  * privacyscore.org/settings/SECRET_KEY
  * svs/svs-ps01/rabbitmq/privacyscore
  * privacyscore.org/sentry

Then deploy the slave using

    ansible-playbook -i ansible/inventory -K ansible/deploy_slave.yml

and update it (to add the relevant section to the settings) using

    ansible-playbook -i ansible/inventory -K ansible/update_hosts.yml

You may want to create a separate inventory file for the initial deployment to just run against new hosts.


## Development

The above mentioned playbooks can be used to set up a development environment.
You will need a machine to run the playbook against. In order to run ansible
you will need to have SSH access. The machine needs access to the Internet in order to download
the software. You will then need to run a Web server in order to access the Web UI.

A setup with an [Ubuntu cloud-image](https://cloud-images.ubuntu.com/)
running under QEMU with libvirt's user sessions could look like this:

    1) Run virt-manager and connect to the user session in order to make
       libvirt set the directories up. This can probably also be done
       through virsh:

            virt-manager qemu:///session
           

    2) Download the image in your user's libvirt image directory, i.e.

        cd ~/.local/share/libvirt/images
        wget https://cloud-images.ubuntu.com/daily/server/artful/current/artful-server-cloudimg-amd64.img


    3) Optionally make it read-only and create working copy:

        chmod a-w artful-server-cloudimg-amd64.img
        cp --reflink=auto artful-server-cloudimg-amd64.img privacyscore.img

    
    4) Resize the image. We need about 3GB. And then you don't have scan results yet.

        qemu-img resize privacyscore.img +10G


    5) Create a suitable [cloud-init](cloudinit.readthedocs.io/) medium.
       Because you want to SSH into the cloud-image, we need to provision it
       with our credentials.  When the image is booted, cloud-init looks for
       a [cloud config](http://cloudinit.readthedocs.io/en/latest/topics/examples.html)
       on various media, including CD-ROMs.  In order to create such a CD-ROM, you can
       use [Cloud-Init-ISO](https://github.com/frederickding/Cloud-Init-ISO) with your
       user-data.

           git clone https://github.com/frederickding/Cloud-Init-ISO.git
           cd Cloud-Init-ISO
           cat > user-data <<EOF
           # replace with your own public key (e.g. ~/.ssh/id_rsa.pub)
           ssh_authorized_keys:
             - ssh-rsa ...

           apt_upgrade: true
           packages:
              - python

           EOF

           ./build.sh

    6) Add the resized cloud-image to libvirt, possibly through virt-manager.
       File → New Virtual Machine. Select your user-session, Importing disk image, Forward.
       Then Browse... and optionally refresh your storage.
       Select the privacyscore.img and optionally select a GNU/Linux flavour.
       After you have created the VM, make sure to add the ISO as CD-ROM.
       Finally, you need to get access to SSH.
       You can make QEMU forward ports.  Ony way to do it to edit libvirt's
       XML. First, get the ID of the machine you've just created:

           virsh --connect qemu:///session list

       Then you can edit the XML:

           virsh --connect qemu:///session edit <ID>

       In the first line, make it look like:
    
           <domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>

       The end needs to look something like:

              <qemu:commandline>
                <qemu:arg value='-redir'/>
                <qemu:arg value='tcp:22222::22'/>
                <qemu:arg value='-redir'/>
                <qemu:arg value='tcp:8000::8000'/>
              </qemu:commandline>
            </domain>
                               
    7) Make sure you re-start the machine with the new configuration.

    8) Check that you can SSH into the machine.
       Note that we check whether Python works. Ansible need a Python interpreter.

        ssh -p 22222  -l ubuntu  localhost  "python -c 'print 23'"

    9) Edit your inventory so that Ansible knows about your machine,
       e.g. add your host to master, slave, and testing.
       You probably also want to configure ansible_user, ansible_port, and
       ansible_host.

        
    10) Now, you can run Ansible against your VM. In this example, the VM was
        named "testhost". You need to change it to the name you've just configures
        in the Ansible inventory.

        ansible-playbook --inventory ansible/inventory --limit testhost  ansible/deploy_slave.yml  ansible/update_hosts.yml 

    11) If all went well you should have a running instance of PrivacyScore. If you haven't forwarded another port yet,
        you can use SSH to both forward a port and start Django in runserver mode:

            ssh -p 22222  -l ubuntu  -L8888:localhost:8000  localhost  sudo -u privacyscore -i env PATH="/opt/privacyscore/.pyenv/bin:/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games"  VIRTUAL_ENV="/opt/privacyscore/.pyenv"  /opt/privacyscore/manage.py runserver 0:8000

    12) You should be able to visit http://localhost:8000 or http://localhost:8888 and see the Web UI.


## Distribution of Changes

* Check in to repository
* If the change only requires an update of the master:
  * sudo -s
  * cd /opt/privacyscore
  * sudo -u privacyscore git pull && systemctl restart privacyscore
* else
  * Execute the following command on a development machine (with all hosts prepared in the ssh_config file): ansible-playbook -i ansible/inventory -K ansible/update_hosts.yml

## Operations

The Redis key-value store runs on the master. Large lists of websites will generate large amounts of intermediate data, which is committed to disk in regular intervals in the background. Redis (which uses about 50% of available RAM in our VM) forks to generate a child process for this purpose. This should not be a problem due to copy-on-write memory management. However, in this case it fails and at some point the child cannot allocate memory any more (see /var/log/redis/redis-server.log). The solution is to tell Linux to be more optimistic about its memory management by adding the following lines to */etc/sysctl.conf*:


    # 
    # https://stackoverflow.com/questions/11752544/redis-bgsave-failed-because-fork-cannot-allocate-memory
    # 
    # default = 0 (heuristically determine what to allocate), 
    # but this fails for redis
    # we set it to 1, which means always overcommit, never check
    # 
    # activation: sudo sysctl -p /etc/sysctl.conf
    # check: cat /proc/sys/vm/overcommit_memory
    
    vm.overcommit_memory=1
    
    ###


## Acknowledgements
The creation of PrivacyScore was funded in part by the DFG as part of project C.1 and C.2 within the RTG 2050 "[Privacy and Trust for Mobile Users](https://www.privacy-trust.tu-darmstadt.de/)".

## License
PrivacyScore is licensed GPLv3 or, at your option, any later version. See LICENSE for more information.
