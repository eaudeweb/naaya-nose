import sys
import os
from os import path
from contextlib import contextmanager
from tempfile import mkstemp

import transaction

def wsgireffix(app):
    from webob.dec import wsgify

    @wsgify
    def wrapper(request):
        response = request.get_response(app)
        del response.headers['Connection']
        return response

    return wrapper

def quickserver(app):
    from wsgiref.simple_server import make_server
    print "waiting for requests"
    make_server('127.0.0.1', 8080, wsgireffix(app)).serve_forever()

def main(part_name=None):
    assert part_name is not None, "Please specify the name of a buildout part"

    with zope_config(part_name) as config_file_path:
        app = make_wsgi_app(config_file_path, install_fixtures)

    quickserver(app)

def make_wsgi_app(config_file_path, install_fixtures):
    from App.config import setConfiguration
    from Zope2.Startup import get_starter
    from Zope2.Startup.handlers import handleConfig
    from Zope2.Startup.options import ZopeOptions
    from ZPublisher.WSGIPublisher import publish_module
    starter = get_starter()
    opts = ZopeOptions()
    opts.configfile = config_file_path
    opts.realize(args=(), progname='Zope2WSGI', raise_getopt_errs=False)

    handleConfig(opts.configroot, opts.confighandlers)
    setConfiguration(opts.configroot)
    starter.setConfiguration(opts.configroot)
    starter.prepare()

    base_db = opts.configroot.dbtab.getDatabase('/')
    #install_fixtures(base_db)

    from ZODB.DemoStorage import DemoStorage
    demo_storage = DemoStorage(base=base_db)

    import Zope2
    Zope2._stuff = (demo_storage, 'Application')

    return publish_module

def install_fixtures(db):
    application = db.open().root()['Application']

    import pdb; pdb.set_trace()
    from Products.Naaya.NySite import manage_addNySite
    print "naaya!"

@contextmanager
def zope_config(part_name):
    buildout_root = path.dirname(path.dirname(sys.argv[0]))
    part_script = path.join(buildout_root, 'bin', part_name)

    with open(part_script, 'rb') as f:
        all_script = f.read()
        end = 'import plone.recipe.zope2instance.ctl'
        script = all_script[:all_script.index(end)]
    exec script

    zope_conf_path = path.join(buildout_root, 'parts', part_name,
                               'etc', 'zope.conf')
    yield zope_conf_path

    #test_db = """
    #<zodb_db main>
    #    <mappingstorage>
    #    </mappingstorage>
    #    mount-point /
    #</zodb_db>
    #"""

    #fd, config_file_path = mkstemp()
    #with os.fdopen(fd, 'wb') as config_file:
    #    config_file.write(something)

    #yield config_file_path

    #os.unlink(config_file_path)
