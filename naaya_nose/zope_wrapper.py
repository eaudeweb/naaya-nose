import sys
import os
from os import path
from tempfile import mkstemp

def wsgi_publish(environ, start_response):
    """
    copied from publish_module in ZPublisher/Test.py, simplified, and
    modified to accept streaming responses
    """
    from ZPublisher.Request import Request
    from ZPublisher.Publish import publish
    from ZServer.HTTPResponse import ZServerHTTPResponse
    from zope.publisher.browser import setDefaultSkin
    from StringIO import StringIO

    outstream = StringIO()

    must_die=0
    after_list=[None]
    response = ZServerHTTPResponse(stdout=outstream, stderr=sys.stderr)
    stdout = response.stdout
    request = Request(environ['wsgi.input'], environ, response)
    try:
        try:
            setDefaultSkin(request)
            response = publish(request, 'Zope2', after_list, debug=0)
        except SystemExit, v:
            must_die=sys.exc_info()
            response.exception(must_die)
        except ImportError, v:
            if isinstance(v, TupleType) and len(v)==3: must_die=v
            else: must_die=sys.exc_info()
            response.exception(1, v)
        except:
            response.exception()

        if response:
            stdout.write(str(response))
            producer = response._bodyproducer
            if producer is not None:
                while True:
                    data = producer.more()
                    if not data:
                        break
                    stdout.write(data)

        if after_list[0] is not None: after_list[0]()

    finally:
        request.close()

    if must_die:
        try: raise must_die[0], must_die[1], must_die[2]
        finally: must_die=None

    output = outstream.getvalue()
    newline = '\r\n'
    headers, body = output.split(newline*2, 1)
    header_lines = headers.split(newline)
    assert header_lines[0].startswith('HTTP/1.0 ')
    status = header_lines[0][len('HTTP/1.0 '):]
    headers = [header.split(': ', 1) for header in header_lines[1:]]

    headers = [ (header[0], ', '.join(header[1:])) for header in headers ]
    if 'content-type' not in (header[0].lower() for header in headers):
        headers.append( ('Content-Type', 'text/html; charset=utf-8') )
    #headers = filter(lambda h: h[0] != 'Connection', headers)
    start_response(status, headers)
    return [body]

def conf_for_test(zope_conf_path):
    #yield zope_conf_path

    start_marker = '<zodb_db main>\n'
    end_marker = '</zodb_db>\n'
    new_text = ('    <mappingstorage>\n'
                '    </mappingstorage>\n'
                '    mount-point /\n')
    f = open(zope_conf_path, 'rb')
    orig_cfg = f.read()
    f.close()

    start_idx = orig_cfg.index(start_marker) + len(start_marker)
    end_idx = orig_cfg.index(end_marker)
    new_cfg = orig_cfg[:start_idx] + new_text + orig_cfg[end_idx:]

    fd, conf_path = mkstemp()
    config_file = os.fdopen(fd, 'wb')
    config_file.write(new_cfg)
    config_file.close()

    def cleanup():
        os.unlink(conf_path)

    return cleanup, conf_path

def get_dummy_starter():
    # copy of Zope2.Startup.get_starter(). Change is in the included classes
    # because our Zope instance MUST NOT listen on any port
    import Zope2
    Zope2.Startup.check_python_version()
    if sys.platform[:3].lower() == "win":
        class DummyWindowsZopeStarter(Zope2.Startup.WindowsZopeStarter):
            def setupServers(self):
                pass
        return DummyWindowsZopeStarter()
    else:
        class DummyUnixZopeStarter(Zope2.Startup.UnixZopeStarter):
            def setupServers(self):
                pass
        return DummyUnixZopeStarter()

def zope_startup(orig_conf_path):
    import Zope2.Startup.run
    import ZODB.DB
    from ZODB.DemoStorage import DemoStorage
    from ZODB.interfaces import IBlobStorage

    _cleanup_conf, conf_path = conf_for_test(orig_conf_path)
    try:
        starter = get_dummy_starter()
        opts = Zope2.Startup.run._setconfig(conf_path)
        starter.setConfiguration(opts.configroot)
        starter.prepare()

    finally:
        _cleanup_conf()

    import Zope2
    orig_db = opts.configroot.dbtab.getDatabase('/')

    def patch_bobo_application(new_db):
        import App
        if App.version_txt.getZopeVersion() >= (2, 12):
            p = (new_db, 'Application')
        else:
            p = (new_db, 'Application', 'Zope-Version')
        Zope2.bobo_application._stuff = p

    def db_layer():
        # create a DemoStorage that wraps the old storage
        base_db = Zope2.bobo_application._stuff[0]
        demo_storage = DemoStorage(base=base_db._storage)
        if not IBlobStorage.providedBy(demo_storage):
            from ZODB.blob import BlobStorage
            from tempfile import mkdtemp
            blob_temp = mkdtemp()
            demo_storage = BlobStorage(blob_temp, demo_storage)
        else:
            blob_temp = None

        # reconstruct the mount table
        wrapper_databases = {}
        for mount_name, mount_db in base_db.databases.iteritems():
            if mount_name == base_db.database_name:
                continue # don't mount the main db over itself
            # wrap each piece of the mount table in a DemoStorage
            new_storage = mount_db._storage
            wrapper_mount_db = ZODB.DB(storage=DemoStorage(base=new_storage),
                                       database_name=mount_db.database_name)
            wrapper_databases[mount_name] = wrapper_mount_db

        # new database with the new storage
        wrapper_db = ZODB.DB(storage=demo_storage,
                             database_name=base_db.database_name,
                             databases=wrapper_databases)

        # monkey-patch the current bobo_application to use our new database
        patch_bobo_application(wrapper_db)

        def cleanup():
            patch_bobo_application(base_db)
            if blob_temp is not None:
                import shutil
                shutil.rmtree(blob_temp)

        return cleanup, wrapper_db

    return orig_db, db_layer

class ZopeTestEnvironment(object):
    def __init__(self, orig_db, db_layer):
        self.orig_db = orig_db
        self.db_layer = db_layer

    wsgi_app = staticmethod(wsgi_publish)

def zope_test_environment(buildout_part_name):
    import sys
    from os import path

    argv_orig = list(sys.argv)
    sys.argv[1:] = []

    buildout_root = path.dirname(path.dirname(sys.argv[0]))
    orig_conf_path = path.join(buildout_root, 'parts', buildout_part_name,
                                 'etc', 'zope.conf')
    orig_db, db_layer = zope_startup(orig_conf_path)

    sys.argv[:] = argv_orig

    return ZopeTestEnvironment(orig_db, db_layer)
