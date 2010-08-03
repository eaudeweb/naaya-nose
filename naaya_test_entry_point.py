import sys
import os
from os import path

def patch_sys_path(buildout_part_name):
    # must be done before importing any namespace package
    buildout_root = path.dirname(path.dirname(sys.argv[0]))
    part_script = path.join(buildout_root, 'bin', buildout_part_name)
    with open(part_script, 'rb') as f:
        all_script = f.read()
        end = 'import plone.recipe.zope2instance.ctl'
        script = all_script[:all_script.index(end)]
    exec script

def main(buildout_part_name=None):
    assert buildout_part_name is not None, \
            "Please specify the name of a buildout part"
    patch_sys_path(buildout_part_name)

    from naaya.test.example import main
    main(buildout_part_name)
