from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

# Install rdflib
from rdflib import __version__, __date__
__version__ = "3.0a1"

setup(
    name = 'rdflib',
    version = __version__,
    description = "RDFLib is a Python library for working with RDF, a simple yet powerful language for representing information.",
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
    """RDFLib is a Python library for working with RDF, a simple yet powerful language for representing information.

    The library contains parsers and serializers for RDF/XML, N3,
    NTriples, Turtle, TriX and RDFa . The library presents a Graph
    interface which can be backed by any one of a number of Store
    implementations, including, Memory, MySQL, Redland, SQLite,
    Sleepycat, ZODB and SQLObject.
    
    If you have recently reported a bug marked as fixed, or have a craving for
    the very latest, you may want the development version instead:
    http://rdflib.googlecode.com/svn/trunk/#egg=rdflib-core-dev

    """,

    packages = find_packages(),

    tests_require = ["nose==0.10.1"],

    test_suite = 'nose.collector',

    entry_points = {        
        'rdflib.plugins.store': [
            'IOMemory = rdflib.plugins.store.IOMemory:IOMemory',
            'Memory = rdflib.plugins.store.Memory:Memory',
            ],
        'rdflib.plugins.serializer': [
            'rdf/xml =     rdflib.plugins.serializers.XMLSerializer:XMLSerializer',
            ],
        'rdflib.plugins.parser': [
            'xml =     rdflib.plugins.parsers.RDFXMLParser:RDFXMLParser',
            'application/rdf+xml =     rdflib.plugins.parsers.RDFXMLParser:RDFXMLParser',
            ],
        },

    )

