"""
main
"""

import re
from pyramid.config import Configurator
from pyramid_chameleon import zpt

__version__ = "0.2.1"

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings) as config:
        config.include('pyramid_chameleon')
        config.include('.routes')

         # xhtml
        config.add_renderer('.xhtml', zpt.renderer_factory)

        # prevent flycheck files to be scanned
        config.scan(ignore=[re.compile(r"\.flycheck_.*").search,])

    return config.make_wsgi_app()
