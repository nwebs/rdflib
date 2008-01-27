# RDF Library

__version__ = "2.4.1"
__date__ = "not/yet/released"

import sys
# generator expressions require 2.4
assert sys.version_info >= (2,4,0), "rdflib requires Python 2.4 or higher"
del sys

import logging
_logger = logging.getLogger("rdflib")
_logger.info("version: %s" % __version__)

from rdflib.uriref import URIRef
from rdflib.bnode import BNode
from rdflib.literal import Literal
from rdflib.variable import Variable

from rdflib.namespace import Namespace

# from rdflib.graph import Graph # perhaps in 3.0, but for 2.x we
# don't want to break compatibility.
from rdflib.graph import BackwardCompatGraph as Graph
from rdflib.graph import ConjunctiveGraph

from rdflib import RDF
from rdflib import RDFS

from rdflib.fileinputsource import FileInputSource
from rdflib.urlinputsource import URLInputSource
from rdflib.stringinputsource import StringInputSource

