#! /bin/bash
#
# nginx should be installed on the host machine
#
#

DOMAIN=${2}
INSTALL_ROOT=$HOME

# Stop nginx
sudo service nginx stop

cd $INSTALL_ROOT/spack-monitor

# 2. Renewing Certificates
# To renew
# sudo certbox renew
# and then the same procedure above

# stop nginx container since we need to start nginx on server
docker-compose stop nginx

# Create recursive backup
backup=$(echo /etc/letsencrypt{,.bak."$(date +%s)"} | cut -d ' ' -f 2)
sudo cp -R /etc/letsencrypt "$backup"

# Start on server and renew!
sudo service nginx start
sudo certbot renew

# Since the containers expect these files to be in /etc/ssl, copy there
# This CANNOT be a link.
sudo cp /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem /etc/ssl/certs/chained.pem
sudo cp /etc/letsencrypt/live/"$DOMAIN"/privkey.pem /etc/ssl/private/domain.key

# stop nginx and restart nginx container, verify certs at SSL checker online!
sudo service nginx stop
docker-compose up -d nginx
