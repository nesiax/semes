""" routes """

def includeme(config):
    """ includeme """
    config.add_static_view('semes/static', 'static', cache_max_age=3600)
    config.add_static_view('semes/deform_static', 'deform:static/')
    config.add_route('home', 'semes/')
    config.add_route('send', 'semes/send')
