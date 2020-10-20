__version__ = '0.2.2'

from pypads import logger

from pypads_onto.app.plugin import configure_plugin


# Entrypoint for the plugin TODO allow to disable this we could also call a defined entrypoint from pypads and decide
def activate(pypads, *args, **kwargs):
    logger.info("Trying to configure onto plugin for pypads...")
    configure_plugin(pypads, *args, **kwargs)
    logger.info("Finished configuring onto plugin for pypads!")
