"""
Example test case using the naaya.test infrastructure
"""

from contextlib import contextmanager
import sys
from os import path

@contextmanager
def temp_request(app, user_id):
    from ZPublisher.BaseRequest import BaseRequest
    user = app.acl_users.getUserById('admin')
    app.REQUEST = BaseRequest(AUTHENTICATED_USER=user)
    yield
    del app.REQUEST

def portal_fixture(db):
    import transaction
    from Products.Naaya.NySite import manage_addNySite

    app = db.open().root()['Application']
    app.acl_users._doAddUser('admin', 'admin', ['Manager'], [])
    with temp_request(app, 'admin'):
        manage_addNySite(app, 'portal')

    transaction.commit()

def run_one_test(test_function, test_db):
    app = test_db.open().root()['Application']
    test_function(app)

def demo_test_runner(tzope):
    with tzope.db_layer() as portal_db:
        portal_fixture(portal_db)
        for test_function in all_tests():
            with tzope.db_layer() as test_db:
                run_one_test(test_function, test_db)

def all_tests():
    yield test_one
#    yield test_two
#    yield test_three

def test_one(app):
    from Products.Naaya.NyFolder import addNyFolder
    portal = app.portal
    with temp_request(app, 'admin'):
        new_folder = addNyFolder(portal, id='myfolder')
    print portal.myfolder

def demo_http_server(tzope):
    def wsgireffix(app):
        from webob.dec import wsgify
        @wsgify
        def wrapper(request):
            response = request.get_response(app)
            del response.headers['Connection']
            return response
        return wrapper

    portal_fixture(tzope.orig_db)

    from wsgiref.simple_server import make_server
    app = wsgireffix(tzope.wsgi_app)
    httpd = make_server('127.0.0.1', 8080, app)

    while True:
        with tzope.db_layer() as db_layer:
            print "waiting for requests. press ctrl_c to refresh db."
            try:
                httpd.serve_forever()
            except SystemExit:
                continue

def main(part_name):
    from zope_wrapper import zope_test_environment
    tzope = zope_test_environment(part_name)
    demo_http_server(tzope)
    #demo_test_runner(tzope)
