#!/bin/sh

# Change this to where you want to install. $HOME
# is probably a bad choice if it needs to be maintained
# by a group of people

# This was developed on Ubuntu 20.04 LTS on AWS

INSTALL_ROOT=/opt

# Prepare instance (or machine) with Docker, docker-compose, python

sudo apt-get update > /dev/null
sudo apt-get install -y git \
                        build-essential \
                        nginx \
                        python-dev

# Needed module for system python
wget https://bootstrap.pypa.io/get-pip.py
sudo /usr/bin/python get-pip.py
sudo pip install ipaddress
sudo pip install oauth2client


# Install Docker dependencies
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

# Add docker key server
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null


# Install Docker!
sudo apt-get update &&
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# test, you will still need sudo
sudo docker run hello-world

# Docker group should already exist
# sudo groupadd docker

# this command won't work via session - the user is empty (you should be ubuntu)
#make sure to add all users that will maintain / use the registry
sudo usermod -aG docker "$USER"

# Docker-compose
sudo apt -y install docker-compose


# Note that you will need to log in and out for changes to take effect

if [ ! -d "$INSTALL_ROOT"/spack-monitor ]; then
    cd "$INSTALL_ROOT"

    # otherwise production
    sudo git clone https://github.com/spack/spack-monitor.git
    sudo chmod o+x -R spack-monitor

    cd spack-monitor

    # If you are connected via ssh you should not need sudo
    sudo docker-compose up -d
fi
