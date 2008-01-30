import unittest

from rdflib.graph import Graph

from rdflib.term import URIRef, BNode, Literal

from rdflib.namespace import Namespace, RDF

class GraphTestCase(unittest.TestCase):

    def setUp(self):
        self.g = Graph()

    def testLen(self):
        self.assertEquals(len(self.g), 0)

    def testHash(self):
        self.assertNotEquals(hash(self.g), 0)


if __name__ == "__main__":
    unittest.main()


