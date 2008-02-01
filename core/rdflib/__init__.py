"""
Library for working with RDF

The primary interface rdflib exposes to work with RDF is
rdflib.graph.Graph. See rdflib.graph for more information.

A tiny example:


    >>> from rdflib.graph import Graph
    >>> g = Graph()
    >>> result = g.parse("http://eikeon.com/foaf.rdf")

    >>> print "graph has %s statements." % len(g)
    graph has 34 statements.
    >>> 
    >>> for s, p, o in g:
    ...     if (s, p, o) not in g:
    ...         raise Exception("It better be!")

    >>> s = g.serialize(format='n3')

"""

__version__ = "3.0"
__date__ = "not/yet/released"

