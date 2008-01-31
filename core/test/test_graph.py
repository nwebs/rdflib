import unittest

from rdflib.graph import Graph

from rdflib.term import URIRef, BNode, Literal

from rdflib.namespace import Namespace, RDF
from rdflib.serializer import Serializer
from rdflib import plugin

class GraphTestCase(unittest.TestCase):

    def setUp(self):
        self.g = Graph()

    def testLen(self):
        self.assertEquals(len(self.g), 0)

    def testHash(self):
        self.assertNotEquals(hash(self.g), 0)

    def testFinalNewline(self):
        """
        http://code.google.com/p/rdflib/issues/detail?id=5
        """
        failed = set()
        for p in plugin.plugins(None, Serializer):
            v = self.g.serialize(format=p.name)
            lines = v.split("\n")
            if "\n" not in v or (lines[-1]!=''):
                failed.add(p.name)
        self.assertEqual(len(failed), 0, "No final newline for formats: '%s'" % failed)
            

if __name__ == "__main__":
    unittest.main()


