import sys
import os
from os import path
from tempfile import mkstemp
from contextlib import contextmanager

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

@contextmanager
def conf_for_test(zope_conf_path):
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

    fd, conf_path = mkstemp()
    with os.fdopen(fd, 'wb') as config_file:
        config_file.write(new_cfg)

    yield conf_path

    os.unlink(conf_path)

def startup(orig_conf_path):
    import Zope2.Startup.run
    import ZODB.DB
    from ZODB.DemoStorage import DemoStorage

    with conf_for_test(orig_conf_path) as conf_path:
        starter = Zope2.Startup.get_starter()
        opts = Zope2.Startup.run._setconfig(conf_path)
        starter.setConfiguration(opts.configroot)
        starter.prepare()

    import Zope2
    orig_db = opts.configroot.dbtab.getDatabase('/')

    @contextmanager
    def db_layer():
        base_db = Zope2.bobo_application._stuff[0]
        wrapper_db = ZODB.DB(DemoStorage(base=base_db.storage))
        Zope2.bobo_application._stuff = (wrapper_db, 'Application')
        yield wrapper_db
        Zope2.bobo_application._stuff = (base_db, 'Application')

    return orig_db, db_layer
