# Dockerfile
FROM odoo:18.0

# Copy custom addons
COPY ./addons /mnt/extra-addons
# RUN chown -R odoo:odoo /mnt/extra-addons

# Copy configuration file
COPY ./odoo.conf /etc/odoo/odoo.conf
