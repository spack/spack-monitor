.. _development-setup:

=========================
Amazon Web Services (AWS)
=========================

This tutorial requires an AWS account. You'll need the following dependencies on the instance:

 - `Docker <https://docs.docker.com/get-docker/>`_
 - `docker-compose <https://docs.docker.com/compose/install/>`_

Setting up AWS
==============

Amazon allows you to run instances on a service called `EC2 <https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Home:>`_
or `lightsail <https://lightsail.aws.amazon.com/>`_.

Lightsail
---------

Lightsail is much easier to setup. You can select to create a new Linux instance, selecting to choose the OS and then choosing Ubuntu 20.04, and then download the default key. You'll need to change permissions for it:

.. code-block:: console

    $ chmod 400 ~/.ssh/Lightsail*.pem

And then follow the instruction to ssh to it (the username is ubuntu)

.. code-block:: console

    $ ssh -v -i "~/.ssh/Lightsail-<keyhname>.pem" ubuntu@<ipaddress>

You'll want to register a static IP, from the Networking tab, otherwise we cannot associate a domain.
You'll also want to add an HTTPS rule to networking, unless you don't plan on setting up https.
You can now jump down to the Install Dependencies section.


EC2
---

You'll want to navigate in your cloud console to Compute -> EC2 and then select "Launch Instance."

- Select a base OS that you are comfortable with. I selected "Ubuntu Server 20.04 LTS (HVM), SSD Volume Type - ami-042e8287309f5df03 (64-bit x86) / ami-0b75998a97c952252 (64-bit Arm)"
- For size I selected t2.xlarge. 
- Select Step 3. Configure Instance Details. In this screen everything is okay, and I selected to enable termination protection. Under tenancy I first had wanted "Dedicated - Run a Dedicated Instance" but ultimately chose the default (Shared) as Dedicated was not an allowed configuration at the time.
- Select Step 4. Add Storage. For this I just increased the root filesystem to 100 GB. This instruction is for a test instance so I didn't think we needed to add additional filesystems.
- IAM roles: I created a new one with the role that was for an llnl admin, with access to EC2.
- Under Step 5. Tags - you can add tags that you think are useful! I usually add service:spack-monitor and creator (my name).
- Step 6. Configure Security group: give the group a name that will be easy to associate (e.g., spack-monitor-security-group). Make sure to add rules for exposing ports 80 and 443 for the web interface.

When you click "Review and Launch" there will be a popup generated about a keypair. If you don't have one, you should
generate it and save to your local machine. You will need this key pair to access the instance with ssh.
I typically move the pem keys to my ~/.ssh folder.

Finally, you'll want to follow instructions `here <https://aws.amazon.com/premiumsupport/knowledge-center/ec2-associate-static-public-ip/>`_ 
to generate a static ip address and associate it with your instance. This will ensure that if you map a domain name to it,
the ip address won't change if you stop and restart.

To connect to your instance, the easiest thing to do is click "View Instances," and then search for your instance by metadata or tags (e.g., I searched for "spack-monitor"). You can also
rename your instance to call it something more meaningful (e.g., spack-monitor-dev). If you then click the instance ID, it will take you
to a details page, and you can click "Connect" and then the tab for SSH. First, you will be instructed to change the permissions
of your key:

.. code-block:: console

    $ chmod 400 ~/.ssh/myusername-spack-monitor.pem

**Important** if you are on VPN, you wil need to request a firewall exception to connect via ssh. Otherwise, you can
 follow the instructions on `this page <https://aws.amazon.com/premiumsupport/knowledge-center/ec2-linux-resolve-ssh-connection-errors/>`_ to:

1. stop the instance
2. edit user data to reset the ssh service
3. start the instance
4. connect via a session

Sessions are in the browser instead of a terminal, but can work if you are absolutely desparate! Otherwise, if you
are off VPN or have an exception, you can do:

.. code-block:: console

    $ ssh -v -i "~/.ssh/username-spack-monitor.pem" ubuntu@ec2-XX-XXX-XXX-X.compute-1.amazonaws.com


Install Dependencies
--------------------

Once connected to the instance, `here is a basic script <https://github.com/spack/spack-monitor/tree/main/script/prepare_instance.sh>`_ to 
t your dependencies installed. If you log in via ssh, you should be able to exit and connect again and not need sudo.


Build and Start Spack Monitor
-----------------------------

It looks like nginx is installed on the instance by default, so you will need to stop it.

.. code-block:: console

    $ sudo service nginx stop

And then build and bring up spack monitor:

.. code-block:: console

    $ docker-compose up -d

After creation, if you need an interactive shell:

.. code-block:: console

    $ docker exec -it spack-monitor_uwsgi_1 bash

or to see logs

.. code-block:: console

    $ docker-compose logs uwsgi

You can then check that the instance interface is live (without https). When that is done, use `this script <https://github.com/spack/spack-monitor/tree/main/script/generate_cert.sh>`_ to set up https. This means that you've registered a static IP, have a domain somewhere where you've associated it, and then
are able to generate certificates for it. After generating the certificates, you will want to use the docker-compose.yml and nginx.conf in the https folder.

You can reference :ref:`getting-started_install` for more details.

Update Settings
---------------

Finally, you'll want to ensure that you update the list of allowed hosts to
include localhost and your custom domain, turn the application on debug mode,
ensure https only is used, and (if you want) enable timezone support to the ``settings.py`` file.

.. code-block:: python

    ALLOWED_HOSTS = [“localhost”, “127.0.0.1", “monitor.spack.io”]
    USE_TZ = True
    SECURE_SSL_REDIRECT = True
    DEBUG = False
