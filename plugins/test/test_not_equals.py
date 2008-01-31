from rdflib.namespace import Namespace, RDF, RDFS
from rdflib.term import URIRef, Literal

from rdflib.graph import Graph,ReadOnlyGraphAggregate,ConjunctiveGraph

import sys
from pprint import pprint

def testSPARQLNotEquals():
    NS = u"http://example.org/"
    graph = ConjunctiveGraph()
    graph.parse(data = """
       @prefix    : <http://example.org/> .
       @prefix rdf: <%s> .
       :foo rdf:value 1.
       :bar rdf:value 2."""%RDF.RDFNS, format="n3")
    rt = graph.query("""SELECT ?node 
                        WHERE {
                                ?node rdf:value ?val.
                                FILTER (?val != 1)
                               }""",
                           initNs={'rdf':RDF.RDFNS},                           
                           DEBUG=False)
    for row in rt:        
        item = row[0]
        assert item == URIRef("http://example.org/bar")

if __name__ == '__main__':
    testSPARQLNotEquals()
