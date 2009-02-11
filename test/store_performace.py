import unittest

from rdflib.Graph import Graph
from rdflib import URIRef

import gc
import itertools
from time import time
from random import random

from tempfile import mkdtemp

def random_uri():
    return URIRef("%s" % random())

class StoreTestCase(unittest.TestCase):
    """
    Test case for testing store performance... probably should be
    something other than a unit test... but for now we'll add it as a
    unit test.
    """
    store = 'default'

    def setUp(self):
        self.gcold = gc.isenabled()
        gc.collect()
        gc.disable()
        self.graph = Graph(store=self.store)
        if self.store == "MySQL":
            from test.mysql import configString
            from rdflib.store.MySQL import MySQL
            path=configString
            MySQL().destroy(path)
        else:
            path = a_tmp_dir = mkdtemp()
        self.graph.open(path, create=True)
        self.input = input = Graph()
        input.parse("http://eikeon.com")

    def tearDown(self):
        self.graph.close()
        if self.gcold:
            gc.enable()
        # TODO: delete a_tmp_dir
        del self.graph

    def testTime(self):
        number = 1
        print self.store
        print "input:",
        for i in itertools.repeat(None, number):
            self._testInput()
        print "random:",
        for i in itertools.repeat(None, number):
            self._testRandom()
        print "."

    def _testRandom(self):
        number = len(self.input)
        store = self.graph

        def add_random():
            s = random_uri()
            p = random_uri()
            o = random_uri()
            store.add((s, p, o))

        it = itertools.repeat(None, number)
        t0 = time()
        for _i in it:
            add_random()
        t1 = time()
        print "%.3g" % (t1 - t0),

    def _testInput(self):
        number = 1
        store = self.graph

        def add_from_input():
            for t in self.input:
                store.add(t)

        it = itertools.repeat(None, number)
        t0 = time()
        for _i in it:
            add_from_input()
        t1 = time()
        print "%.3g" % (t1 - t0),


class MemoryStoreTestCase(StoreTestCase):
    store = "Memory"

try:
    from rdflib.store.Sleepycat import Sleepycat
    class SleepycatStoreTestCase(StoreTestCase):
        store = "Sleepycat"
except ImportError, e:
    print "Can not test Sleepycat store:", e

try:
    import persistent
    # If we can import persistent then test ZODB store
    class ZODBStoreTestCase(StoreTestCase):
        non_standard_dep = True
        store = "ZODB"
except ImportError, e:
    print "Can not test ZODB store:", e


try:
    import RDF
    # If we can import RDF then test Redland store
    class RedLandTestCase(StoreTestCase):
        non_standard_dep = True
        store = "Redland"
except ImportError, e:
    print "Can not test Redland store:", e

# TODO: add test case for 4Suite backends?  from Ft import Rdf

try:
#     import todo # what kind of configuration string does open need?

    import MySQLdb,sha,sys
    # If we can import RDF then test Redland store
    class MySQLTestCase(StoreTestCase):
        non_standard_dep = True
        store = "MySQL"
except ImportError, e:
    print "Can not test MySQL store:", e

if __name__ == '__main__':
    unittest.main()
