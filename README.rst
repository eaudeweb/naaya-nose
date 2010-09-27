NyNose - Testing tool for Naaya
===============================

Requirements
-------------------------------
 - nose
 - selenium (for Selenium tests)
 - wsgiref (ditto)
 - coverage (for coverage reporting)

Instructions
-------------------------------
Call nynose by::
    bin/nynose test.module

Example::
    bin/nynose Products.NaayaCore.FormsTool

Nynose will autodiscover tests recursively in the given module.
All command line options available for nose are also available for nynose.

E.g.::
    bin/nynose -s naaya Products.NaayaCore

will test naaya and Products.NaayaCore without capturing stdout.

Always use -s when debugging.

Additional options
-------------------------------
 - --nycoverage substitutes --with-coverage from nose, for better coverage on Naaya
 - --ny-selenium enables running Naaya SeleniumTestCases, with the following options available:

  - --ny-instance-port will change wsgi listener's port
  - --selenium-grid-port will change selenium remote control port
  - --ny-selenium-browsers will change the browser used in testing

  More info on Naaya Selenium testing here: http://github.com/eaudeweb/naaya.selenium
