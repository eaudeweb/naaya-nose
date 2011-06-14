import sys
from os import path
from time import time
import logging

log = logging.getLogger('naaya nose')
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler(sys.stderr))

def patch_sys_path(buildout_part_name):
    # must be done before importing any namespace package
    buildout_root = path.dirname(path.dirname(sys.argv[0]))
    part_script = path.join(buildout_root, 'bin', buildout_part_name)

    if not path.isfile(part_script):
        # on windows, buildout does funny things
        part_script += '-script.py'
        assert path.isfile(part_script)

    f = open(part_script, 'rb')
    try:
        all_script = f.read().replace('\r\n', '\n')
        end = 'import plone.recipe.zope2instance.ctl'
        script = all_script[:all_script.index(end)]
    finally:
        f.close()
    exec script

def call_nose_main(tzope):
    from nose import main

    plugins = []
    from Products.Naaya.tests.NaayaTestCase import NaayaPortalTestPlugin
    from Products.Naaya.tests.SeleniumTestCase import NaayaSeleniumTestPlugin

    plugins.append(NaayaPortalTestPlugin(tzope))
    plugins.append(NaayaSeleniumTestPlugin(tzope))

    try:
        from naaya.groupware.tests import GWPortalTestPlugin
        plugins.append(GWPortalTestPlugin(tzope))
    except ImportError:
        pass

    from timer_plugin import Timer
    plugins.append(Timer())

    main(addplugins=plugins)

def main(buildout_part_name=None):
    """
    Main entry point. Set up Zope2 and then call `nose`.

    We take a single argument, `buildout_part_name`. It can be provided as
    function argument (zc.recipe.egg can pass it) or command-line argument.
    """
    if buildout_part_name is None:
        buildout_part_name = sys.argv[1]
        del sys.argv[1]

    log.info("Preparing Zope environment ...")
    t0 = time()
    patch_sys_path(buildout_part_name)
    from zope_wrapper import zope_test_environment
    tzope = zope_test_environment(buildout_part_name)
    log.info("Zope environment loaded in %.3f seconds" % (time()-t0))
    log.info("Calling nose.main ... ")
    call_nose_main(tzope)

