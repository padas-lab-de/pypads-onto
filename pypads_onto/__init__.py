__version__ = '0.1.4'

from pypads_onto.app.plugin import configure_plugin


# Entrypoint for the plugin TODO allow to disable this we could also call a defined entrypoint from pypads and decide
def activate():
    configure_plugin()
