import unittest

from rdflib.graph import Graph
from rdflib.term import URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS


class ParserTestCase(unittest.TestCase):
    backend = 'Memory'
    path = 'store'

    def setUp(self):
        self.graph = Graph(store=self.backend)
        self.graph.open(self.path)

    def tearDown(self):
        self.graph.close()

    def testNoPathWithHash(self):
        g = self.graph
        g.parse(data="""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<rdf:RDF
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
>

<rdfs:Class rdf:about="http://example.org#">
  <rdfs:label>testing</rdfs:label>
</rdfs:Class>

</rdf:RDF>
""", publicID="http://example.org")

        subject = URIRef("http://example.org#")
        label = g.value(subject, RDFS.label)
        self.assertEquals(label, Literal("testing"))
        type = g.value(subject, RDF.type)
        self.assertEquals(type, RDFS.Class)


if __name__ == "__main__":
    unittest.main()
