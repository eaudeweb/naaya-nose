import transaction

def wsgireffix(app):
    from webob.dec import wsgify

    @wsgify
    def wrapper(request):
        response = request.get_response(app)
        del response.headers['Connection']
        return response

    return wrapper

def main():
    app = make_wsgi_app(install_fixtures)
    from wsgiref.simple_server import make_server
    make_server('127.0.0.1', 8080, wsgireffix(app)).serve_forever()

def make_wsgi_app(install_fixtures):
    config_file_path = make_instance()
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
    install_fixtures(base_db)

    from ZODB.DemoStorage import DemoStorage
    demo_storage = ZODB.DemoStorage.DemoStorage(base=base_db)

    import Zope2
    Zope2._stuff = (demo_storage, 'Application')

    return publish_module

def install_fixtures(db):
    application = db.open().root()['Application']

    import pdb; pdb.set_trace()
    from Products.Naaya.NySite import manage_addNySite
    print "naaya!"

def make_instance():
    p = "/Work/repos/edw.test/sandbox26/var/zope_instance_temp"
    p_conf = p + '/etc/zope.conf'
    import os
    if os.path.isdir(p):
        import shutil
        shutil.rmtree(p)
    os.mkdir(p)
    os.mkdir(p + '/etc')
    with open(p_conf, 'wb') as f:
        f.write(zope_conf_tmpl % {'ih_path': p})
    return p_conf

zope_conf_tmpl = """
%%define INSTANCE %(ih_path)s
instancehome $INSTANCE

<zodb_db main>
    <mappingstorage>
    </mappingstorage>
    mount-point /
</zodb_db>

<zodb_db temporary>
    <temporarystorage>
      name temporary storage for sessioning
    </temporarystorage>
    mount-point /temp_folder
    container-class Products.TemporaryFolder.TemporaryContainer
</zodb_db>
"""
