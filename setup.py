from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

from distutils.extension import Extension

# Install rdflib
from rdflib import __version__, __date__


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
    http://rdflib.googlecode.com/svn/trunk/#egg=rdflib-dev

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
        'rdflib.plugins.store': [
            'IOMemory = rdflib_plugins.store.IOMemory:IOMemory',
            'Memory = rdflib_plugins.store.Memory:Memory',
            'Sleepycat = rdflib_plugins.store.Sleepycat:Sleepycat',
            'BerkeleyDB = rdflib_plugins.store.BerkeleyDB:BerkeleyDB', 
            'BDBOptimized = rdflib_plugins.store.BDBOptimized:BDBOptimized',
            'MySQL = rdflib_plugins.store.MySQL:MySQL',
            'SQLite = rdflib_plugins.store.SQLite:SQLite',
            'ZODB = rdflib_plugins.store.ZODB:ZODB',
            'sqlobject = rdflib_plugins.store._sqlobject:SQLObject',
            'Redland = rdflib_plugins.store.Redland:Redland',
            ],
        'rdflib.plugins.serializer': [
            'rdf =     rdflib.syntax.serializers.XMLSerializer:XMLSerializer',
            'xml =     rdflib.syntax.serializers.XMLSerializer:XMLSerializer',
            'rdf/xml =     rdflib.syntax.serializers.XMLSerializer:XMLSerializer',
            'pretty-xml =     rdflib.syntax.serializers.PrettyXMLSerializer:PrettyXMLSerializer',
            'nt =     rdflib.syntax.serializers.NTSerializer:NTSerializer',
            'turtle =     rdflib.syntax.serializers.TurtleSerializer:TurtleSerializer',
            'n3 =     rdflib.syntax.serializers.N3Serializer:N3Serializer',
            ],
        'rdflib.plugins.parser': [
            'xml =     rdflib_plugins.parsers.RDFXMLParser:RDFXMLParser',
            'trix =     rdflib_plugins.parsers.TriXParser:TriXParser',
            'n3 =     rdflib_plugins.parsers.N3Parser:N3Parser',
            'notation3 =     rdflib_plugins.parsers.N3Parser:N3Parser',
            'nt =     rdflib_plugins.parsers.NTParser:NTParser',
            'rdfa =     rdflib_plugins.parsers.RDFaParser:RDFaParser',
            ],
        'rdflib.plugins.query_processor': [
            'sparql = rdflib.sparql.bison.Processor:Processor',
            ],
        'rdflib.plugins.query_result': [
            'SPARQLQueryResult = rdflib.sparql.QueryResult:SPARQLQueryResult'
            ],
        'console_scripts': [
            'rdfpipe = rdflib_tools.RDFPipe:main',
        ],
        'nose.plugins': [
            'EARLPlugin = rdflib_tools.EARLPlugin:EARLPlugin',
            ],
        },

    )

