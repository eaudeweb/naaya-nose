import sys
import os
from os import path
from time import time

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

    nycoverage = "--nycoverage" in sys.argv
    if nycoverage:
        from coverage import coverage
        cov = coverage()
        cov.start()
        sys.argv.pop(sys.argv.index("--nycoverage"))
    try:
        print>>sys.stderr, "Preparing Zope environment ..."
        t0 = time()
        patch_sys_path(buildout_part_name)
        from zope_wrapper import zope_test_environment
        tzope = zope_test_environment(buildout_part_name)
        print>>sys.stderr, "Zope environment loaded in %.3f seconds" % (time()-t0)

        #from demo_http import demo_http_server; demo_http_server(tzope)

        print>>sys.stderr, "Calling nose.main ... "
        call_nose_main(tzope)
    finally:
        if nycoverage:
            t0 = time()
            cov.stop()
            cov.save()
            print>>sys.stderr, ("[NyCoverage] Coverage binary information saved in"
                                " .coverage")
            f = open(".coverage-report", "wb")
            cov.report(file=f, ignore_errors=True)
            f.close()
            print>>sys.stderr, ("[NyCoverage] Text report saved in "
                                ".coverage-report")
            cov.html_report(directory="coverage_html", ignore_errors=True)
            print>>sys.stderr, ("[NyCoverage] Html report saved in "
                                "coverage_html directory")
            print>>sys.stderr, ("Coverage reports generated in %.3f seconds"
                               % (time()-t0))
