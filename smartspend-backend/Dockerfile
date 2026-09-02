FROM odoo:19

# The official Odoo image doesn't ship the Anthropic SDK. Add it so the
# smartspend_core module's ai.gateway can call Claude.
USER root
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed "anthropic>=0.40"
USER odoo
