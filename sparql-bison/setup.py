from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

from distutils.extension import Extension

__version__ = "0.9"
__date__ = "not/yet/released"


setup(
    name = 'rdflib_sparql',
    version = __version__,
    description = "Standard sparql for rdflib.",
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
    """

    If you have recently reported a bug marked as fixed, or have a craving for
    the very latest, you may want the development version instead:
    http://rdflib.googlecode.com/svn/rdflib_sparql/#egg=rdflib-dev

    """,
    download_url = "http://rdflib.net/rdflib_sparql-%s.tar.gz" % __version__,

    packages = find_packages(),

    install_requires = ['rdflib'],

    ext_modules = [
        Extension(
            name='rdflib_sparql.sparql.bison.SPARQLParserc',
            sources=['src/bison/SPARQLParser.c'],
            ),
        ],

    tests_require = ["nose>=0.9.2"],

    test_suite = 'nose.collector',

    entry_points = {        
        'rdflib.plugins.query_processor': [
            'sparql = rdflib_sparql.sparql.bison.Processor:Processor',
            ],
        'rdflib.plugins.query_result': [
            'SPARQLQueryResult = rdflib_sparql.sparql.QueryResult:SPARQLQueryResult'
            ],
        },

    )

