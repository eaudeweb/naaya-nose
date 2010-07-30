import sys
import os
from os import path

def patch_sys_path(part_name):
    # must be done before importing any namespace package

    buildout_root = path.dirname(path.dirname(sys.argv[0]))
    part_script = path.join(buildout_root, 'bin', part_name)
    with open(part_script, 'rb') as f:
        all_script = f.read()
        end = 'import plone.recipe.zope2instance.ctl'
        script = all_script[:all_script.index(end)]
    exec script

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

    patch_sys_path(part_name)

    from edw.test.run import zope_config, make_wsgi_app

    with zope_config(part_name) as config_file_path:
        app = make_wsgi_app(config_file_path, lambda db: None)

    quickserver(app)
