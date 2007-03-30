from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

from distutils.extension import Extension

# Install rdflib
from rdflib import __version__, __date__


setup(
    name = 'rdflib',
    version = __version__,
    description = "RDF library containing an RDF triple store and RDF/XML parser/serializer",
    author = "Daniel 'eikeon' Krech",
    author_email = "eikeon@eikeon.com",
    maintainer = "Daniel 'eikeon' Krech",
    maintainer_email = "eikeon@eikeon.com",
    url = "http://rdflib.net/",
    license = "http://rdflib.net/latest/LICENSE",
    platforms = ["any"],
    classifiers = ["Programming Language :: Python",
                   "License :: OSI Approved :: BSD License",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Operating System :: OS Independent",
                   "Natural Language :: English",
                   ],
    long_description = \
    """RDF library containing an RDF triple store and RDF/XML parser/serializer
    
    If you have recently reported a bug marked as fixed, or have a craving for
    the very latest, you may want the development version instead:
    http://svn.rdflib.net/trunk#egg=rdflib-dev
    """,
    download_url = "http://rdflib.net/rdflib-%s.tar.gz" % __version__,

    packages = find_packages(),

    ext_modules = [
        Extension(
            name='rdflib.sparql.bison.SPARQLParserc',
            sources=['src/bison/SPARQLParser.c'],
            ),
        ],

    tests_require = ["nose>=0.9.2"],

    test_suite = 'nose.collector',

    entry_points = {        
        'console_scripts': [
            'rdfpipe = rdflib_tools.RDFPipe:main',
        ],
        'nose.plugins': [
            'EARLPlugin = rdflib_tools.EARLPlugin:EARLPlugin',
            ],
        },

    )

