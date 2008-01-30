"""
Library for working with RDF

The primary interface rdflib exposes to work with RDF is
rdflib.graph.Graph. See rdflib.graph for more information.

A tiny example:

g = Graph()
g.parse("http://eikeon.com/foaf.rdf")

print "graph has %s statements." % len(g)

for s, p, o in g:
    print s, p, o

g.serialize(format='n3')

"""

__version__ = "2.5.0"
__date__ = "not/yet/released"

