from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

from distutils.extension import Extension

__version__ = "0.9"
__date__ = "not/yet/released"


setup(
    name = 'rdflib_plugins',
    version = __version__,
    description = "Standard plugins for rdflib.",
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
    http://rdflib.googlecode.com/svn/rdflib_plugins/#egg=rdflib-dev

    """,
    download_url = "http://rdflib.net/rdflib_plugins-%s.tar.gz" % __version__,

    packages = find_packages(),

    install_requires = ['rdflib'],

    tests_require = ["nose>=0.9.2", "Persistence", "pysqlite"],

    test_suite = 'nose.collector',

    entry_points = {        
        'rdflib.plugins.store': [
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
            'pretty-xml =     rdflib_plugins.serializers.PrettyXMLSerializer:PrettyXMLSerializer',
            'nt =     rdflib_plugins.serializers.NTSerializer:NTSerializer',
            'turtle =     rdflib_plugins.serializers.TurtleSerializer:TurtleSerializer',
            'n3 =     rdflib_plugins.serializers.N3Serializer:N3Serializer',
            ],
        'rdflib.plugins.parser': [
            'text/rdf+n3 =     rdflib_plugins.parsers.N3Parser:N3Parser',
            'n3 =     rdflib_plugins.parsers.N3Parser:N3Parser',
            'nt =     rdflib_plugins.parsers.NTParser:NTParser', # text/plain
            'rdfa =     rdflib_plugins.parsers.RDFaParser:RDFaParser',
            'trix =     rdflib_plugins.parsers.TriXParser:TriXParser',
            ],
        },

    )

