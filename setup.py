import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-rest-passwordreset',
    version=os.getenv('PACKAGE_VERSION', '0.0.0').replace('refs/tags/', ''),
    packages_dir={"django_rest_passwordreset":"django_rest_passwordreset"},
    packages=find_packages(),
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    include_package_data=True,
    license='BSD License',
    description='An extension of django rest framework, providing a configurable password reset strategy',
    long_description=README,
    long_description_content_type='text/markdown',  # This is important for README.md in markdown format
    url='https://github.com/anexia-it/django-rest-passwordreset',
    author='Harald Nezbeda',
    author_email='HNezbeda@anexia-it.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
