NyNose - Testing tool for Naaya
===============================

Requirements
-------------------------------
 - nose
 - selenium
 - wsgiref
 - coverage

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
 - --nycoverage substitutes --with-coverage from nose, for better coverage
 on Naaya
