import sys
import os
from os import path
from time import time

def patch_sys_path(buildout_part_name):
    # must be done before importing any namespace package
    buildout_root = path.dirname(path.dirname(sys.argv[0]))
    part_script = path.join(buildout_root, 'bin', buildout_part_name)
    f = open(part_script, 'rb')
    try:
        all_script = f.read()
        end = 'import plone.recipe.zope2instance.ctl'
        script = all_script[:all_script.index(end)]
    finally:
        f.close()
    exec script

def call_nose_main(tzope):
    from nose import main
    from Products.Naaya.tests.NaayaTestCase import NaayaPortalTestPlugin
    main(addplugins=[NaayaPortalTestPlugin(tzope)])

def main(buildout_part_name):
    assert buildout_part_name is not None, \
            "Please specify the name of a buildout part"

    print "Preparing Zope environment ..."
    t0 = time()
    patch_sys_path(buildout_part_name)
    from zope_wrapper import zope_test_environment
    tzope = zope_test_environment(buildout_part_name)
    print "Zope environment loaded in %.3f seconds" % (time() - t0)

    #from demo_http import demo_http_server; demo_http_server(tzope)

    print "Calling nose.main ... "
    call_nose_main(tzope)
