from rdflib import plugin,RDF,RDFS,URIRef
from rdflib.store import Store
from cStringIO import StringIO
from rdflib.Graph import Graph,ReadOnlyGraphAggregate
import sys
from pprint import pprint

testGraph1N3="""
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <http://test/> .
:foo a rdfs:Class.
:bar :d :c.
:a :d :c.
"""


testGraph2N3="""
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <http://test/> .
@prefix log: <http://www.w3.org/2000/10/swap/log#>.
:foo a rdfs:Resource.
:bar rdfs:isDefinedBy [ a log:Formula ].
:a :d :e.
"""

testGraph3N3="""
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix log: <http://www.w3.org/2000/10/swap/log#>.
@prefix : <http://test/> .
<> a log:N3Document.
"""

def testAggregateRaw():
    memStore = plugin.get('IOMemory',Store)()
    graph1 = Graph(memStore)
    graph2 = Graph(memStore)
    graph3 = Graph(memStore)
    
    for n3Str,graph in [(testGraph1N3,graph1),
                        (testGraph2N3,graph2),
                        (testGraph3N3,graph3)]:
        graph.parse(StringIO(n3Str),format='n3')
    
    G = ReadOnlyGraphAggregate([graph1,graph2,graph3])
    
    #Test triples
    assert len(list(G.triples((None,RDF.type,None))))                  == 4
    assert len(list(G.triples((URIRef("http://test/bar"),None,None)))) == 2
    assert len(list(G.triples((None,URIRef("http://test/d"),None))))   == 3
    
    #Test __len__
    assert len(G) == 8
    
    #Test __contains__
    assert (URIRef("http://test/foo"),RDF.type,RDFS.Resource) in G
 
    barPredicates = [URIRef("http://test/d"),RDFS.isDefinedBy]
    assert len(list(G.triples_choices((URIRef("http://test/bar"),barPredicates,None)))) == 2    

def testAggregateSPARQL():
    pass

if __name__ == '__main__':
    testAggregateRaw()