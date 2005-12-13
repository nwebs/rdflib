import unittest

from tempfile import mkdtemp

from rdflib import URIRef, BNode, Literal, RDF
from rdflib.Graph import Graph, ConjunctiveGraph

class GraphTestCase(unittest.TestCase):
    store_name = 'default'
    path = None
    graph_class = ConjunctiveGraph

    def setUp(self):
        self.store = self.graph_class(store=self.store_name)
        a_tmp_dir = mkdtemp()
        self.path = self.path or a_tmp_dir
        self.store.open(self.path)

        self.michel = URIRef(u'michel')
        self.tarek = URIRef(u'tarek')
        self.bob = URIRef(u'bob')
        self.likes = URIRef(u'likes')
        self.hates = URIRef(u'hates')
        self.pizza = URIRef(u'pizza')
        self.cheese = URIRef(u'cheese')

    def tearDown(self):
        self.store.close()

    def addStuff(self):
        tarek = self.tarek
        michel = self.michel
        bob = self.bob
        likes = self.likes
        hates = self.hates
        pizza = self.pizza
        cheese = self.cheese

        self.store.add((tarek, likes, pizza))
        self.store.add((tarek, likes, cheese))
        self.store.add((michel, likes, pizza))
        self.store.add((michel, likes, cheese))
        self.store.add((bob, likes, cheese))
        self.store.add((bob, hates, pizza))
        self.store.add((bob, hates, michel)) # gasp!        

    def removeStuff(self):
        tarek = self.tarek
        michel = self.michel
        bob = self.bob
        likes = self.likes
        hates = self.hates
        pizza = self.pizza
        cheese = self.cheese

        self.store.remove((tarek, likes, pizza))
        self.store.remove((tarek, likes, cheese))
        self.store.remove((michel, likes, pizza))
        self.store.remove((michel, likes, cheese))
        self.store.remove((bob, likes, cheese))
        self.store.remove((bob, hates, pizza))
        self.store.remove((bob, hates, michel)) # gasp!

    def testAdd(self):
        self.addStuff()

    def testRemove(self):
        self.addStuff()
        self.removeStuff()

    def testTriples(self):
        tarek = self.tarek
        michel = self.michel
        bob = self.bob
        likes = self.likes
        hates = self.hates
        pizza = self.pizza
        cheese = self.cheese
        asserte = self.assertEquals
        triples = self.store.triples
        Any = None

        self.addStuff()

        # unbound subjects
        asserte(len(list(triples((Any, likes, pizza)))), 2)
        asserte(len(list(triples((Any, hates, pizza)))), 1)
        asserte(len(list(triples((Any, likes, cheese)))), 3)
        asserte(len(list(triples((Any, hates, cheese)))), 0)

        # unbound objects
        asserte(len(list(triples((michel, likes, Any)))), 2)
        asserte(len(list(triples((tarek, likes, Any)))), 2)
        asserte(len(list(triples((bob, hates, Any)))), 2)
        asserte(len(list(triples((bob, likes, Any)))), 1)

        # unbound predicates
        asserte(len(list(triples((michel, Any, cheese)))), 1)
        asserte(len(list(triples((tarek, Any, cheese)))), 1)
        asserte(len(list(triples((bob, Any, pizza)))), 1)
        asserte(len(list(triples((bob, Any, michel)))), 1)

        # unbound subject, objects
        asserte(len(list(triples((Any, hates, Any)))), 2)
        asserte(len(list(triples((Any, likes, Any)))), 5)

        # unbound predicates, objects
        asserte(len(list(triples((michel, Any, Any)))), 2)
        asserte(len(list(triples((bob, Any, Any)))), 3)
        asserte(len(list(triples((tarek, Any, Any)))), 2)        

        # unbound subjects, predicates
        asserte(len(list(triples((Any, Any, pizza)))), 3)
        asserte(len(list(triples((Any, Any, cheese)))), 3)
        asserte(len(list(triples((Any, Any, michel)))), 1)        

        # all unbound
        asserte(len(list(triples((Any, Any, Any)))), 7)
        self.removeStuff()
        asserte(len(list(triples((Any, Any, Any)))), 0)


    def testStatementNode(self):
        store = self.store
        
        from rdflib.Statement import Statement
        c = URIRef("http://example.org/foo#c")
        r = URIRef("http://example.org/foo#r")
        s = Statement((self.michel, self.likes, self.pizza), c)
        store.add((s, RDF.value, r))
        self.assertEquals(r, store.value(s, RDF.value))
        self.assertEquals(s, store.value(predicate=RDF.value, object=r))


class MemoryGraphTestCase(GraphTestCase):
    store = "Memory"
    graph_class = Graph

try:
    from rdflib.store.Sleepycat import Sleepycat
    class SleepycatGraphTestCase(GraphTestCase):
        store = "Sleepycat"
except ImportError, e:
    print "Can not test Sleepycat store:", e

try:
    import persistent
    # If we can import persistent then test ZODB store
    class ZODBGraphTestCase(GraphTestCase):
        store = "ZODB"
except ImportError, e:
    print "Can not test ZODB store:", e


try:
    import RDF
    # If we can import RDF then test Redland store
    class RedLandTestCase(GraphTestCase):
        store = "Redland"
except ImportError, e:
    print "Can not test Redland store:", e    

if __name__ == '__main__':
    unittest.main()    
