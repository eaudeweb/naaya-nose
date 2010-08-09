from setuptools import setup, find_packages

setup(
    name='naaya-nose',
    version='0.3',
    author='Eau de Web',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['WebOb', 'nose'],
    entry_points={'console_scripts': ['nynose = naaya_nose:main']},
)
