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

def zope_startup(orig_conf_path):
    import Zope2.Startup.run
    import ZODB.DB
    from ZODB.DemoStorage import DemoStorage

    _cleanup_conf, conf_path = conf_for_test(orig_conf_path)
    try:
        starter = Zope2.Startup.get_starter()
        opts = Zope2.Startup.run._setconfig(conf_path)
        starter.setConfiguration(opts.configroot)
        starter.prepare()

    finally:
        _cleanup_conf()

    import Zope2
    orig_db = opts.configroot.dbtab.getDatabase('/')

    def db_layer():
        # create a DemoStorage that wraps the old storage
        base_db = Zope2.bobo_application._stuff[0]
        demo_storage = DemoStorage(base=base_db._storage)

        # reconstruct the mount table
        database_name = base_db.database_name
        new_databases = dict(base_db.databases)
        del new_databases[database_name]

        # new database with the new storage
        wrapper_db = ZODB.DB(storage=demo_storage,
                             database_name=database_name,
                             databases=new_databases)

        # monkey-patch the current bobo_application to use our new database
        Zope2.bobo_application._stuff = (wrapper_db, 'Application', 'Zope-Version')

        def cleanup():
            Zope2.bobo_application._stuff = (base_db, 'Application', 'Zope-Version')

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
