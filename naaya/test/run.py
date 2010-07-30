import sys
import os
from os import path
from contextlib import contextmanager
from tempfile import mkstemp

def make_wsgi_app(config_file_path, install_fixtures):
    import Zope2.Startup.run
    starter = Zope2.Startup.get_starter()
    opts = Zope2.Startup.run._setconfig(config_file_path)
    starter.setConfiguration(opts.configroot)
    starter.prepare()

    base_db = opts.configroot.dbtab.getDatabase('/')
    install_fixtures(base_db)

    from ZODB.DemoStorage import DemoStorage
    demo_storage = DemoStorage(base=base_db)

    import Zope2
    Zope2._stuff = (demo_storage, 'Application')

    return publish_app

def publish_app(environ, start_response):
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
    try:
        try:
            response = ZServerHTTPResponse(stdout=outstream, stderr=sys.stderr)
            stdout=response.stdout
            request=Request(environ['wsgi.input'], environ, response)
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


def install_fixtures(db):
    application = db.open().root()['Application']

    import pdb; pdb.set_trace()
    from Products.Naaya.NySite import manage_addNySite
    print "naaya!"

@contextmanager
def zope_config(part_name):
    buildout_root = path.dirname(path.dirname(sys.argv[0]))

    zope_conf_path = path.join(buildout_root, 'parts', part_name,
                               'etc', 'zope.conf')
    #yield zope_conf_path

    start_marker = '<zodb_db main>\n'
    end_marker = '</zodb_db>\n'
    new_text = ('    <mappingstorage>\n'
                '    </mappingstorage>\n'
                '    mount-point /\n')
    with open(zope_conf_path, 'rb') as f:
        orig_cfg = f.read()

    start_idx = orig_cfg.index(start_marker) + len(start_marker)
    end_idx = orig_cfg.index(end_marker)
    new_cfg = orig_cfg[:start_idx] + new_text + orig_cfg[end_idx:]

    fd, config_file_path = mkstemp()
    with os.fdopen(fd, 'wb') as config_file:
        config_file.write(new_cfg)

    yield config_file_path

    os.unlink(config_file_path)