from setuptools import setup, find_packages

setup(
    name='naaya.test',
    version='0.1',
    author='Eau de Web',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points={'console_scripts': ['nytest = naaya_test_entry_point:main']},
)
