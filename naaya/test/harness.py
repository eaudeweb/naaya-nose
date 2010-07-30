import zope_wrapper

class TestHarness(object):
    def __init__(self, changes_db):
        self.changes_db = changes_db

    def flush_temp_db(self):
        raise NotImplementedError

    wsgi_app = staticmethod(zope_wrapper.wsgi_publish)


def zope_test_harness(orig_conf_path, fixtures_callback):
    changes_db = zope_wrapper.startup(orig_conf_path, fixtures_callback)
    return TestHarness(changes_db)

def demo(part_name):
    import sys
    from os import path
    from contextlib import contextmanager

    def wsgireffix(app):
        from webob.dec import wsgify
        @wsgify
        def wrapper(request):
            response = request.get_response(app)
            del response.headers['Connection']
            return response
        return wrapper

    @contextmanager
    def temp_request(app, user_id):
        from ZPublisher.BaseRequest import BaseRequest
        user = app.acl_users.getUserById('admin')
        app.REQUEST = BaseRequest(AUTHENTICATED_USER=user)
        yield
        del app.REQUEST

    def install_fixtures(db):
        import transaction
        from Products.Naaya.NySite import manage_addNySite

        app = db.open().root()['Application']
        app.acl_users._doAddUser('admin', 'admin', ['Manager'], [])
        with temp_request(app, 'admin'):
            manage_addNySite(app, 'portal')

        transaction.commit()

    buildout_root = path.dirname(path.dirname(sys.argv[0]))
    orig_conf_path = path.join(buildout_root, 'parts', part_name,
                                 'etc', 'zope.conf')

    app = zope_test_harness(orig_conf_path, install_fixtures).wsgi_app

    from wsgiref.simple_server import make_server
    print "waiting for requests"
    make_server('127.0.0.1', 8080, wsgireffix(app)).serve_forever()
