"""
A Graph and ConjunctiveGraph interface for working with an RDF Graph.

    >>> from rdflib.graph import Graph, ConjunctiveGraph
    >>> from rdflib.graph import ReadOnlyGraphAggregate

    >>> from rdflib.term import URIRef, BNode, Literal
    >>> from rdflib.namespace import RDF, RDFS

    >>> from rdflib import plugin
    >>> from rdflib.store import Store

Instanciating Graphs with default store (Memory) and default identifier (a BNode):


    >>> g=Graph()
    >>> g.store.__class__.__name__
    'Memory'
    >>> g.identifier.__class__
    <class 'rdflib.term.BNode'>

Instanciating Graphs with a specific kind of store (IOMemory) and a default identifier (a BNode):

Other store kinds: Sleepycat, MySQL, ZODB, SQLite

    >>> graph = Graph(store="Sleepycat")
    >>> graph.store.__class__.__name__
    'Sleepycat'

Instanciating Graphs with Sleepycat store and an identifier - <http://rdflib.net>:

    >>> g=Graph('Sleepycat',URIRef("http://rdflib.net"))
    >>> g.identifier
    rdflib.URIRef('http://rdflib.net')
    >>> str(g)
    "<http://rdflib.net> a rdfg:Graph;rdflib:storage [a rdflib:Store;rdfs:label 'Sleepycat']."

Creating a ConjunctiveGraph - The top level container for all named Graphs in a 'database':

    >>> from rdflib.graph import ConjunctiveGraph
    >>> g=ConjunctiveGraph()
    >>> str(g.default_context)
    "[a rdfg:Graph;rdflib:storage [a rdflib:Store;rdfs:label 'IOMemory']]."

Adding / removing reified triples to Graph and iterating over it directly or via triple pattern:
    
    >>> g=Graph('IOMemory')
    >>> statementId = BNode()
    >>> print len(g)
    0
    >>> g.add((statementId,RDF.type,RDF.Statement))
    >>> g.add((statementId,RDF.subject,URIRef('http://rdflib.net/store/ConjunctiveGraph')))
    >>> g.add((statementId,RDF.predicate,RDFS.label))
    >>> g.add((statementId,RDF.object,Literal("Conjunctive Graph")))
    >>> print len(g)
    4
    >>> for s,p,o in g:  print type(s)
    ...
    <class 'rdflib.term.BNode'>
    <class 'rdflib.term.BNode'>
    <class 'rdflib.term.BNode'>
    <class 'rdflib.term.BNode'>
    
    >>> for s,p,o in g.triples((None,RDF.object,None)):  print o
    ...
    Conjunctive Graph
    >>> g.remove((statementId,RDF.type,RDF.Statement))
    >>> print len(g)
    3

None terms in calls to triple can be thought of as 'open variables'  

Graph Aggregation - ConjunctiveGraphs and ReadOnlyGraphAggregate within the same store:
    
    >>> store = plugin.get('IOMemory',Store)()
    >>> g1 = Graph(store)
    >>> g2 = Graph(store)
    >>> g3 = Graph(store)
    >>> stmt1 = BNode()
    >>> stmt2 = BNode()
    >>> stmt3 = BNode()
    >>> g1.add((stmt1,RDF.type,RDF.Statement))
    >>> g1.add((stmt1,RDF.subject,URIRef('http://rdflib.net/store/ConjunctiveGraph')))
    >>> g1.add((stmt1,RDF.predicate,RDFS.label))
    >>> g1.add((stmt1,RDF.object,Literal("Conjunctive Graph")))
    >>> g2.add((stmt2,RDF.type,RDF.Statement))
    >>> g2.add((stmt2,RDF.subject,URIRef('http://rdflib.net/store/ConjunctiveGraph')))
    >>> g2.add((stmt2,RDF.predicate,RDF.type))
    >>> g2.add((stmt2,RDF.object,RDFS.Class))
    >>> g3.add((stmt3,RDF.type,RDF.Statement))
    >>> g3.add((stmt3,RDF.subject,URIRef('http://rdflib.net/store/ConjunctiveGraph')))
    >>> g3.add((stmt3,RDF.predicate,RDFS.comment))
    >>> g3.add((stmt3,RDF.object,Literal("The top-level aggregate graph - The sum of all named graphs within a Store")))
    >>> len(list(ConjunctiveGraph(store).subjects(RDF.type,RDF.Statement)))
    3
    >>> len(list(ReadOnlyGraphAggregate([g1,g2]).subjects(RDF.type,RDF.Statement)))
    2

ConjunctiveGraphs have a 'quads' method which returns quads instead of triples, where the fourth item
is the Graph (or subclass thereof) instance in which the triple was asserted:
    
    >>> from sets import Set    
    >>> uniqueGraphNames = Set([graph.identifier for s,p,o,graph in ConjunctiveGraph(store).quads((None,RDF.predicate,None))])
    >>> len(uniqueGraphNames)
    3
    >>> unionGraph = ReadOnlyGraphAggregate([g1,g2])
    >>> uniqueGraphNames = Set([graph.identifier for s,p,o,graph in unionGraph.quads((None,RDF.predicate,None))])
    >>> len(uniqueGraphNames)
    2
     
Parsing N3 from StringIO

    >>> from cStringIO import StringIO
    >>> g2=ConjunctiveGraph()
    >>> src = '''
    ... @prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    ... @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    ... [ a rdf:Statement ;
    ...   rdf:subject <http://rdflib.net/store#ConjunctiveGraph>;
    ...   rdf:predicate rdfs:label;
    ...   rdf:object "Conjunctive Graph" ] '''
    >>> g2=g2.parse(StringIO(src),format='n3')
    >>> print len(g2)
    4

Using Namespace class:

    >>> from rdflib.namespace import Namespace

    >>> RDFLib = Namespace('http://rdflib.net')
    >>> RDFLib.ConjunctiveGraph
    rdflib.URIRef('http://rdflib.netConjunctiveGraph')
    >>> RDFLib['Graph']
    rdflib.URIRef('http://rdflib.netGraph')

# SPARQL Queries

#     >>> print len(g)
#     3
#     >>> q = \'\'\'
#     ... PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> SELECT ?pred WHERE { ?stmt rdf:predicate ?pred. }
#     ... \'\'\'   
#     >>> for pred in g.query(q):  print pred
#     (rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#label'),)

# SPARQL Queries with namespace bindings as argument

#     >>> nsMap = {u"rdf":RDF.RDFNS}
#     >>> for pred in g.query("SELECT ?pred WHERE { ?stmt rdf:predicate ?pred. }", initNs=nsMap): print pred
#     (rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#label'),)

# Parameterized SPARQL Queries

#     >>> top = { Variable("?term") : RDF.predicate }
#     >>> for pred in g.query("SELECT ?pred WHERE { ?stmt ?term ?pred. }", initBindings=top<): print pred
#     (rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#label'),)

"""
from __future__ import generators

from urlparse import urljoin, urldefrag
from urllib import pathname2url, url2pathname
import os, sys, new

from rdflib.term import URIRef, Literal, Variable
from rdflib.namespace import split_uri

import random
import warnings
import tempfile
import shutil
import os
from urlparse import urlparse

try:
    from hashlib import md5
except ImportError:
    from md5 import md5    

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


from rdflib.term import URIRef, BNode, Literal, Variable
from rdflib.namespace import Namespace, RDF, RDFS

from rdflib.term import Term

from rdflib import plugin, exceptions

from rdflib.store import Store

from rdflib import query

from rdflib.serializer import Serializer
from rdflib.parser import Parser, create_input_source


# def describe(terms,bindings,graph):
#     """ 
#     Default DESCRIBE returns all incomming and outgoing statements about the given terms 
#     """
#     from rdflib.sparql.sparqlOperators import getValue
#     g=Graph()
#     terms=[getValue(i)(bindings) for i in terms]
#     for s,p,o in graph.triples_choices((terms,None,None)):
#         g.add((s,p,o))
#     for s,p,o in graph.triples_choices((None,None,terms)):
#         g.add((s,p,o))
#     return g

class Graph(Term):
    """An RDF Graph

    The constructor accepts one argument, the 'store'
    that will be used to store the graph data (see the 'store'
    package for stores currently shipped with rdflib).

    Stores can be context-aware or unaware.  Unaware stores take up
    (some) less space but cannot support features that require
    context, such as true merging/demerging of sub-graphs and
    provenance.

    The Graph constructor can take an identifier which identifies the Graph
    by name.  If none is given, the graph is assigned a BNode for it's identifier.
    For more on named graphs, see: http://www.w3.org/2004/03/trix/

    Ontology for __str__ provenance terms:

    @prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix : <http://rdflib.net/store#> .
    @prefix rdfg: <http://www.w3.org/2004/03/trix/rdfg-1/>.
    @prefix owl: <http://www.w3.org/2002/07/owl#>.
    @prefix log: <http://www.w3.org/2000/10/swap/log#>.
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

    :Store a owl:Class;
        rdfs:subClassOf <http://xmlns.com/wordnet/1.6/Electronic_database>;
        rdfs:subClassOf
            [a owl:Restriction;
             owl:onProperty rdfs:label;
             owl:allValuesFrom [a owl:DataRange;
                                owl:oneOf ("IOMemory"
                                           "Sleepcat"
                                           "MySQL"
                                           "Redland"
                                           "REGEXMatching"
                                           "ZODB"
                                           "AuditableStorage"
                                           "Memory")]
            ].

    :ConjunctiveGraph a owl:Class;
        rdfs:subClassOf rdfg:Graph;
        rdfs:label "The top-level graph within the store - the union of all the Graphs within."
        rdfs:seeAlso <http://rdflib.net/rdf_store/#ConjunctiveGraph>.

    :DefaultGraph a owl:Class;
        rdfs:subClassOf rdfg:Graph;
        rdfs:label "The 'default' subgraph of a conjunctive graph".


    :identifier a owl:Datatypeproperty;
        rdfs:label "The store-associated identifier of the formula. ".
        rdfs:domain log:Formula
        rdfs:range xsd:anyURI;

    :storage a owl:ObjectProperty;
        rdfs:domain [
            a owl:Class;
            owl:unionOf (log:Formula rdfg:Graph :ConjunctiveGraph)
        ];
        rdfs:range :Store.

    :default_context a owl:FunctionalProperty;
        rdfs:label "The default context for a conjunctive graph";
        rdfs:domain :ConjunctiveGraph;
        rdfs:range :DefaultGraph.


    {?cg a :ConjunctiveGraph;:storage ?store}
      => {?cg owl:sameAs ?store}.

    {?subGraph rdfg:subGraphOf ?cg;a :DefaultGraph}
      => {?cg a :ConjunctiveGraph;:default_context ?subGraphOf} .
    """

    def __init__(self, store='Memory', identifier=None,
                 namespace_manager=None):
        super(Graph, self).__init__()
        self.__identifier = identifier or BNode()
        if not isinstance(store, Store):
            # TODO: error handling
            self.__store = store = plugin.get(store, Store)()
        else:
            self.__store = store
        self.__namespace_manager = namespace_manager
        self.context_aware = False
        self.formula_aware = False

    def __get_store(self):
        return self.__store
    store = property(__get_store)

    def __get_identifier(self):
        return self.__identifier
    identifier = property(__get_identifier)

    def _get_namespace_manager(self):
        if self.__namespace_manager is None:
            self.__namespace_manager = NamespaceManager(self)
        return self.__namespace_manager

    def _set_namespace_manager(self, nm):
        self.__namespace_manager = nm
    namespace_manager = property(_get_namespace_manager, _set_namespace_manager)

    def __repr__(self):
        return "<Graph identifier=%s (%s)>" % (self.identifier, type(self))

    def __str__(self):
        if isinstance(self.identifier,URIRef):
            return "%s a rdfg:Graph;rdflib:storage [a rdflib:Store;rdfs:label '%s']."%(self.identifier.n3(),self.store.__class__.__name__)
        else:
            return "[a rdfg:Graph;rdflib:storage [a rdflib:Store;rdfs:label '%s']]."%(self.store.__class__.__name__)

    def destroy(self, configuration):
        """Destroy the store identified by `configuration` if supported"""
        self.__store.destroy(configuration)

    #Transactional interfaces (optional)
    def commit(self):
        """Commits active transactions"""
        self.__store.commit()

    def rollback(self):
        """Rollback active transactions"""
        self.__store.rollback()

    def open(self, configuration, create=False):
        """Open the graph store

        Might be necessary for stores that require opening a connection to a
        database or acquiring some resource.
        """
        return self.__store.open(configuration, create)

    def close(self, commit_pending_transaction=False):
        """Close the graph store

        Might be necessary for stores that require closing a connection to a
        database or releasing some resource.
        """
        self.__store.close(commit_pending_transaction=commit_pending_transaction)

    def add(self, (s, p, o)):
        """Add a triple with self as context"""
        self.__store.add((s, p, o), self, quoted=False)

    def addN(self, quads):
        """Add a sequence of triple with context"""
        self.__store.addN([(s, p, o, c) for s, p, o, c in quads
                                        if isinstance(c, Graph)
                                        and c.identifier is self.identifier])

    def remove(self, (s, p, o)):
        """Remove a triple from the graph

        If the triple does not provide a context attribute, removes the triple
        from all contexts.
        """
        self.__store.remove((s, p, o), context=self)

    def triples(self, (s, p, o)):
        """Generator over the triple store

        Returns triples that match the given triple pattern. If triple pattern
        does not provide a context, all contexts will be searched.
        """
        for (s, p, o), cg in self.__store.triples((s, p, o), context=self):
            yield (s, p, o)

    def __len__(self):
        """Returns the number of triples in the graph

        If context is specified then the number of triples in the context is
        returned instead.
        """
        return self.__store.__len__(context=self)

    def __iter__(self):
        """Iterates over all triples in the store"""
        return self.triples((None, None, None))

    def __contains__(self, triple):
        """Support for 'triple in graph' syntax"""
        for triple in self.triples(triple):
            return 1
        return 0

    def __hash__(self):
        return hash(self.identifier)

    def md5_term_hash(self):
        d = md5(str(self.identifier))
        d.update("G")
        return d.hexdigest()

    def __cmp__(self, other):
        if other is None:
            return -1
        elif isinstance(other, Graph):
            return cmp(self.identifier, other.identifier)
        else:
            #Note if None is considered equivalent to owl:Nothing
            #Then perhaps a graph with length 0 should be considered
            #equivalent to None (if compared to it)?
            return 1

    def __iadd__(self, other):
        """Add all triples in Graph other to Graph"""
        for triple in other:
            self.add(triple)
        return self

    def __isub__(self, other):
        """Subtract all triples in Graph other from Graph"""
        for triple in other:
            self.remove(triple)
        return self

    def __add__(self,other) :
        """Set theoretical union"""
        retval = Graph()
        for x in self.graph:
            retval.add(x)
        for y in other.graph:
            retval.add(y)
        return retval

    def __mul__(self,other) :
        """Set theoretical intersection"""
        retval = Graph()
        for x in other.graph:
            if x in self.graph: 
                retval.add(x)
        return retval

    def __sub__(self,other) :
        """Set theoretical difference"""
        retval = Graph()
        for x in self.graph:
            if not x in other.graph : 
                retval.add(x)
        return retval

    # Conv. methods

    def set(self, (subject, predicate, object)):
        """Convenience method to update the value of object

        Remove any existing triples for subject and predicate before adding
        (subject, predicate, object).
        """
        self.remove((subject, predicate, None))
        self.add((subject, predicate, object))

    def subjects(self, predicate=None, object=None):
        """A generator of subjects with the given predicate and object"""
        for s, p, o in self.triples((None, predicate, object)):
            yield s

    def predicates(self, subject=None, object=None):
        """A generator of predicates with the given subject and object"""
        for s, p, o in self.triples((subject, None, object)):
            yield p

    def objects(self, subject=None, predicate=None):
        """A generator of objects with the given subject and predicate"""
        for s, p, o in self.triples((subject, predicate, None)):
            yield o

    def subject_predicates(self, object=None):
        """A generator of (subject, predicate) tuples for the given object"""
        for s, p, o in self.triples((None, None, object)):
            yield s, p

    def subject_objects(self, predicate=None):
        """A generator of (subject, object) tuples for the given predicate"""
        for s, p, o in self.triples((None, predicate, None)):
            yield s, o

    def predicate_objects(self, subject=None):
        """A generator of (predicate, object) tuples for the given subject"""
        for s, p, o in self.triples((subject, None, None)):
            yield p, o

    def triples_choices(self, (subject, predicate, object_),context=None):
        for (s, p, o), cg in self.store.triples_choices(
            (subject, predicate, object_), context=self):
            yield (s, p, o)

    def value(self, subject=None, predicate=RDF.value, object=None,
              default=None, any=True):
        """Get a value for a pair of two criteria

        Exactly one of subject, predicate, object must be None. Useful if one
        knows that there may only be one value.

        It is one of those situations that occur a lot, hence this
        'macro' like utility

        Parameters:
        -----------
        subject, predicate, object  -- exactly one must be None
        default -- value to be returned if no values found
        any -- if True:
                 return any value in the case there is more than one
               else:
                 raise UniquenessError
        """
        retval = default

        if (subject is None and predicate is None) or \
                (subject is None and object is None) or \
                (predicate is None and object is None):
            return None
        
        if object is None:
            values = self.objects(subject, predicate)
        if subject is None:
            values = self.subjects(predicate, object)
        if predicate is None:
            values = self.predicates(subject, object)

        try:
            retval = values.next()
        except StopIteration, e:
            retval = default
        else:
            if any is False:
                try:
                    next = values.next()
                    msg = ("While trying to find a value for (%s, %s, %s) the "
                           "following multiple values where found:\n" %
                           (subject, predicate, object))
                    triples = self.store.triples((subject, predicate, object), None)
                    for (s, p, o), contexts in triples:
                        msg += "(%s, %s, %s)\n (contexts: %s)\n" % (
                            s, p, o, list(contexts))
                    raise exceptions.UniquenessError(msg)
                except StopIteration, e:
                    pass
        return retval

    def label(self, subject, default=''):
        """Query for the RDFS.label of the subject

        Return default if no label exists
        """
        if subject is None:
            return default
        return self.value(subject, RDFS.label, default=default, any=True)

    def comment(self, subject, default=''):
        """Query for the RDFS.comment of the subject

        Return default if no comment exists
        """
        if subject is None:
            return default
        return self.value(subject, RDFS.comment, default=default, any=True)

    def items(self, list):
        """Generator over all items in the resource specified by list

        list is an RDF collection.
        """
        while list:
            item = self.value(list, RDF.first)
            if item:
                yield item
            list = self.value(list, RDF.rest)

    def transitiveClosure(self,func,arg):
        """
        Generates transitive closure of a user-defined 
        function against the graph
        
        >>> from rdflib.graph import Collection
        >>> g=Graph()
        >>> a=BNode('foo')
        >>> b=BNode('bar')
        >>> c=BNode('baz')
        >>> g.add((a,RDF.first,RDF.type))
        >>> g.add((a,RDF.rest,b))
        >>> g.add((b,RDF.first,RDFS.label))
        >>> g.add((b,RDF.rest,c))
        >>> g.add((c,RDF.first,RDFS.comment))
        >>> g.add((c,RDF.rest,RDF.nil))
        >>> def topList(node,g):
        ...    for s in g.subjects(RDF.rest,node):
        ...       yield s
        >>> def reverseList(node,g):
        ...    for f in g.objects(node,RDF.first):
        ...       print f
        ...    for s in g.subjects(RDF.rest,node):
        ...       yield s
        
        >>> [rt for rt in g.transitiveClosure(topList,RDF.nil)]
        [rdflib.BNode('baz'), rdflib.BNode('bar'), rdflib.BNode('foo')]
        
        >>> [rt for rt in g.transitiveClosure(reverseList,RDF.nil)]
        http://www.w3.org/2000/01/rdf-schema#comment
        http://www.w3.org/2000/01/rdf-schema#label
        http://www.w3.org/1999/02/22-rdf-syntax-ns#type
        [rdflib.BNode('baz'), rdflib.BNode('bar'), rdflib.BNode('foo')]
        
        """
        for rt in func(arg,self):
            yield rt
            for rt_2 in self.transitiveClosure(func,rt):
                yield rt_2

    def transitive_objects(self, subject, property, remember=None):
        """Transitively generate objects for the `property` relationship

        Generated objects belong to the depth first transitive closure of the
        `property` relationship starting at `subject`.
        """
        if remember is None:
            remember = {}
        if subject in remember:
            return
        remember[subject] = 1
        yield subject
        for object in self.objects(subject, property):
            for o in self.transitive_objects(object, property, remember):
                yield o

    def transitive_subjects(self, predicate, object, remember=None):
        """Transitively generate objects for the `property` relationship

        Generated objects belong to the depth first transitive closure of the
        `property` relationship starting at `subject`.
        """
        if remember is None:
            remember = {}
        if object in remember:
            return
        remember[object] = 1
        yield object
        for subject in self.subjects(predicate, object):
            for s in self.transitive_subjects(predicate, subject, remember):
                yield s

    def seq(self, subject):
        """Check if subject is an rdf:Seq

        If yes, it returns a Seq class instance, None otherwise.
        """
        if (subject, RDF.type, RDF.Seq) in self:
            return Seq(self, subject)
        else:
            return None

    def qname(self, uri):
        return self.namespace_manager.qname(uri)

    def compute_qname(self, uri):
        return self.namespace_manager.compute_qname(uri)

    def bind(self, prefix, namespace, override=True):
        """Bind prefix to namespace

        If override is True will bind namespace to given prefix if namespace
        was already bound to a different prefix.
        """
        return self.namespace_manager.bind(prefix, namespace, override=override)

    def namespaces(self):
        """Generator over all the prefix, namespace tuples"""
        for prefix, namespace in self.namespace_manager.namespaces():
            yield prefix, namespace

    def absolutize(self, uri, defrag=1):
        """Turn uri into an absolute URI if it's not one already"""
        return self.namespace_manager.absolutize(uri, defrag)

    def serialize(self, destination=None, format="xml", base=None, encoding=None, **args):
        """Serialize the Graph to destination

        If destination is None serialize method returns the serialization as a
        string. Format defaults to xml (AKA rdf/xml).
        """
        serializer = plugin.get(format, Serializer)(self)
        if destination is None:
            stream = StringIO()
            serializer.serialize(stream, base=base, encoding=encoding)
            return stream.getvalue()
        if hasattr(destination, "write"):
            stream = destination
            serializer.serialize(stream, base=base, encoding=encoding)
        else:
            location = destination
            scheme, netloc, path, params, query, fragment = urlparse(location)
            if netloc!="":
                print "WARNING: not saving as location is not a local file reference"
                return
            name = tempfile.mktemp()
            stream = open(name, 'wb')
            serializer.serialize(stream, base=base, encoding=encoding, **args)
            stream.close()
            if hasattr(shutil,"move"):
                shutil.move(name, path)
            else:
                shutil.copy(name, path)
                os.remove(name)

    def parse(self, source=None, publicID=None, format=None, 
              location=None, file=None, data=None, **args):
        """ 
        Parse source adding the resulting triples to the Graph.

        The source is specified using one of source, location, file or
        data.

        :Parameters:

        - `source`: An InputSource, file-like object, or string. In
          the case of a string the string is the location of the
          source.
        - `location`: A string indicating the relative or absolute URL
          of the source. Graph's absolutize method is used if a
          relative location is specified.
        - `file`: A file-like object.
        - `data`: A string containing the data to be parsed.
        - `format`: Used if format can not be determined from
          source. Defaults to rdf/xml.
        - `publicID`: the logical URI to use as the document base. If
          None specified the document location is used (at least in
          the case where there is a document location).

        :Returns:

        self, the graph instance.

        :Examples:

        >>> my_data = '''
        ... <rdf:RDF 
        ...   xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
        ...   xmlns:rdfs='http://www.w3.org/2000/01/rdf-schema#'
        ... >
        ...   <rdf:Description> 
        ...     <rdfs:label>Example</rdfs:label>
        ...     <rdfs:comment>This is really just an example.</rdfs:comment>
        ...   </rdf:Description> 
        ... </rdf:RDF>
        ... '''
        >>> import tempfile
        >>> file_name = tempfile.mktemp()
        >>> f = file(file_name, "w")
        >>> f.write(my_data)
        >>> f.close()

        >>> g = Graph()
        >>> result = g.parse(data=my_data, format="application/rdf+xml")
        >>> len(g)
        2

        >>> g = Graph()
        >>> result = g.parse(location=file_name, format="application/rdf+xml")
        >>> len(g)
        2

        >>> g = Graph()
        >>> result = g.parse(file=file(file_name, "r"), format="application/rdf+xml")
        >>> len(g)
        2

        """

        if format=="xml":
            # warn... backward compat.
            format = "application/rdf+xml"
        source = create_input_source(source=source, publicID=publicID, location=location, file=file, data=data)
        if format is None:
            format = source.content_type
        if format is None:
            raise Exception("Could not determin format for %r. You can expicitly specify one with the format argument." % source)
        parser = plugin.get(format, Parser)()
        parser.parse(source, self, **args)
        return self

    def query(self, strOrQuery, initBindings={}, initNs={}, DEBUG=False,
              dataSetBase=None,
              processor="sparql",
              ): #extensionFunctions={sparql.DESCRIBE:describe}):
        """
        Executes a SPARQL query (eventually will support Versa queries with same method) against this Graph
        strOrQuery - Is either a string consisting of the SPARQL query or an instance of rdflib.sparql.bison.Query.Query
        initBindings - A mapping from a Variable to an RDFLib term (used as initial bindings for SPARQL query)
        initNS - A mapping from a namespace prefix to an instance of rdflib.Namespace (used for SPARQL query)
        DEBUG - A boolean flag passed on to the SPARQL parser and evaluation engine
        processor - The kind of RDF query (must be 'sparql' until Versa is ported)
        """
        assert processor == 'sparql',"SPARQL is currently the only supported RDF query language"
        p = plugin.get(processor, query.Processor)(self)
        return plugin.get('SPARQLQueryResult', query.Result)(p.query(strOrQuery,
                                                                   initBindings,
                                                                   initNs, 
                                                                   DEBUG, 
                                                                   dataSetBase,
                                                                   extensionFunctions))

        processor_plugin = plugin.get(processor, query.Processor)(self.store)
        qresult_plugin = plugin.get('SPARQLQueryResult', query.Result)

        res = processor_plugin.query(strOrQuery, 
                                     initBindings, 
                                     initNs, 
                                     DEBUG, 
                                     extensionFunctions=extensionFunctions)
        return qresult_plugin(res)

    def n3(self):
        """return an n3 identifier for the Graph"""
        return "[%s]" % self.identifier.n3()

    def __reduce__(self):
        return (Graph, (self.store, self.identifier,))

    def isomorphic(self, other):
        # TODO: this is only an approximation.
        if len(self) != len(other):
            return False
        for s, p, o in self:
            if not isinstance(s, BNode) and not isinstance(o, BNode):
                if not (s, p, o) in other:
                    return False
        for s, p, o in other:
            if not isinstance(s, BNode) and not isinstance(o, BNode):
                if not (s, p, o) in self:
                    return False
        # TODO: very well could be a false positive at this point yet.
        return True

    def connected(self):
        """Check if the Graph is connected

        The Graph is considered undirectional.

        Performs a search on the Graph, starting from a random node. Then
        iteratively goes depth-first through the triplets where the node is
        subject and object. Return True if all nodes have been visited and
        False if it cannot continue and there are still unvisited nodes left.
        """
        all_nodes = list(self.all_nodes())
        discovered = []

        # take a random one, could also always take the first one, doesn't
        # really matter.
        visiting = [all_nodes[random.randrange(len(all_nodes))]]
        while visiting:
            x = visiting.pop()
            if x not in discovered:
                discovered.append(x)
            for new_x in self.objects(subject=x):
                if new_x not in discovered and new_x not in visiting:
                    visiting.append(new_x)
            for new_x in self.subjects(object=x):
                if new_x not in discovered and new_x not in visiting:
                    visiting.append(new_x)

        # optimisation by only considering length, since no new objects can
        # be introduced anywhere.
        if len(all_nodes) == len(discovered):
            return True
        else:
            return False

    def all_nodes(self):
        obj = set(self.objects())
        allNodes = obj.union(set(self.subjects()))
        return allNodes

class ConjunctiveGraph(Graph):

    def __init__(self, store='IOMemory', identifier=None):
        super(ConjunctiveGraph, self).__init__(store)
        assert self.store.context_aware, ("ConjunctiveGraph must be backed by"
                                          " a context aware store.")
        self.context_aware = True
        self.default_context = Graph(store=self.store,
                                     identifier=identifier or BNode())

    def __str__(self):
        pattern = ("[a rdflib:ConjunctiveGraph;rdflib:storage "
                   "[a rdflib:Store;rdfs:label '%s']]")
        return pattern % self.store.__class__.__name__

    def add(self, (s, p, o)):
        """Add the triple to the default context"""
        self.store.add((s, p, o), context=self.default_context, quoted=False)

    def addN(self, quads):
        """Add a sequence of triple with context"""
        self.store.addN(quads)

    def remove(self, (s, p, o)):
        """Removes from all its contexts"""
        self.store.remove((s, p, o), context=None)

    def triples(self, (s, p, o)):
        """Iterate over all the triples in the entire conjunctive graph"""
        for (s, p, o), cg in self.store.triples((s, p, o), context=None):
            yield s, p, o

    def quads(self,(s,p,o)):
        """Iterate over all the quads in the entire conjunctive graph"""
        for (s, p, o), cg in self.store.triples((s, p, o), context=None):
            for ctx in cg:
                yield s, p, o, ctx
            
    def triples_choices(self, (s, p, o)):
        """Iterate over all the triples in the entire conjunctive graph"""
        for (s1, p1, o1), cg in self.store.triples_choices((s, p, o),
                                                           context=None):
            yield (s1, p1, o1)

    def __len__(self):
        """Number of triples in the entire conjunctive graph"""
        return self.store.__len__()

    def contexts(self, triple=None):
        """Iterate over all contexts in the graph

        If triple is specified, iterate over all contexts the triple is in.
        """
        for context in self.store.contexts(triple):
            yield context

    def get_context(self, identifier, quoted=False):
        """Return a context graph for the given identifier

        identifier must be a URIRef or BNode.
        """
        return Graph(store=self.store, identifier=identifier, namespace_manager=self)

    def remove_context(self, context):
        """Removes the given context from the graph"""
        self.store.remove((None, None, None), context)

    def context_id(self, uri, context_id=None):
        """URI#context"""
        uri = uri.split("#", 1)[0]
        if context_id is None:
            context_id = "#context"
        return URIRef(context_id, base=uri)

    def parse(self, source=None, publicID=None, format="xml", 
              location=None, file=None, data=None, **args):
        """
        Parse source adding the resulting triples to it's own context
        (sub graph of this graph).

        See `rdflib.graph.Graph.parse` for documentation on arguments.a

        :Returns:

        The graph into which the source was parsed. In the case of n3
        it returns the root context.
        """

        source = create_input_source(source=source, publicID=publicID, location=location, file=file, data=data)

        id = self.context_id(self.absolutize(source.getPublicId()))
        context = Graph(store=self.store, identifier=id)
        context.remove((None, None, None))
        context.parse(source, publicID=publicID, format=format,
                      location=location, file=file, data=data, **args)
        return context

    def __reduce__(self):
        return (ConjunctiveGraph, (self.store, self.identifier))


class QuotedGraph(Graph):

    def __init__(self, store, identifier):
        super(QuotedGraph, self).__init__(store, identifier)

    def add(self, triple):
        """Add a triple with self as context"""
        self.store.add(triple, self, quoted=True)

    def addN(self,quads):
        """Add a sequence of triple with context"""
        self.store.addN([(s,p,o,c) for s,p,o,c in quads
                                   if isinstance(c, QuotedGraph)
                                   and c.identifier is self.identifier])

    def n3(self):
        """Return an n3 identifier for the Graph"""
        return "{%s}" % self.identifier.n3()

    def __str__(self):
        identifier = self.identifier.n3()
        label = self.store.__class__.__name__
        pattern = ("{this rdflib.identifier %s;rdflib:storage "
                   "[a rdflib:Store;rdfs:label '%s']}")
        return pattern % (identifier, label)

    def __reduce__(self):
        return (QuotedGraph, (self.store, self.identifier))


class GraphValue(QuotedGraph):
    def __init__(self, store, identifier=None, graph=None):
        if graph is not None:
            assert identifier is None
            np = store.node_pickler
            identifier = md5()
            s = list(graph.triples((None, None, None)))
            s.sort()
            for t in s:
                identifier.update("^".join((np.dumps(i) for i in t)))
            identifier = URIRef("data:%s" % identifier.hexdigest())
            super(GraphValue, self).__init__(store, identifier)
            for t in graph:
                store.add(t, context=self)
        else:
            super(GraphValue, self).__init__(store, identifier)


    def add(self, triple):
        raise Exception("not mutable")

    def remove(self, triple):
        raise Exception("not mutable")

    def __reduce__(self):
        return (GraphValue, (self.store, self.identifier,))


class Seq(object):
    """Wrapper around an RDF Seq resource

    It implements a container type in Python with the order of the items
    returned corresponding to the Seq content. It is based on the natural
    ordering of the predicate names _1, _2, _3, etc, which is the
    'implementation' of a sequence in RDF terms.
    """

    def __init__(self, graph, subject):
        """Parameters:

        - graph:
            the graph containing the Seq

        - subject:
            the subject of a Seq. Note that the init does not
            check whether this is a Seq, this is done in whoever
            creates this instance!
        """

        _list = self._list = list()
        LI_INDEX = RDF.RDFNS + "_"
        for (p, o) in graph.predicate_objects(subject):
            if p.startswith(LI_INDEX): #!= RDF.Seq: #
                i = int(p.replace(LI_INDEX, ''))
                _list.append((i, o))

        # here is the trick: the predicates are _1, _2, _3, etc. Ie,
        # by sorting the keys (by integer) we have what we want!
        _list.sort()

    def __iter__(self):
        """Generator over the items in the Seq"""
        for _, item in self._list:
            yield item

    def __len__(self):
        """Length of the Seq"""
        return len(self._list)

    def __getitem__(self, index):
        """Item given by index from the Seq"""
        index, item = self._list.__getitem__(index)
        return item


class ModificationException(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return ("Modifications and transactional operations not allowed on "
                "ReadOnlyGraphAggregate instances")

class UnSupportedAggregateOperation(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return ("This operation is not supported by ReadOnlyGraphAggregate "
                "instances")

class ReadOnlyGraphAggregate(ConjunctiveGraph):
    """Utility class for treating a set of graphs as a single graph

    Only read operations are supported (hence the name). Essentially a
    ConjunctiveGraph over an explicit subset of the entire store.
    """

    def __init__(self, graphs,store='IOMemory'):
        if store is not None:
            super(ReadOnlyGraphAggregate, self).__init__(store)
        assert isinstance(graphs, list) and graphs\
               and [g for g in graphs if isinstance(g, Graph)],\
               "graphs argument must be a list of Graphs!!"
        self.graphs = graphs

    def __repr__(self):
        return "<ReadOnlyGraphAggregate: %s graphs>" % len(self.graphs)

    def destroy(self, configuration):
        raise ModificationException()

    #Transactional interfaces (optional)
    def commit(self):
        raise ModificationException()

    def rollback(self):
        raise ModificationException()

    def open(self, configuration, create=False):
        # TODO: is there a use case for this method?
        for graph in self.graphs:
            graph.open(self, configuration, create)

    def close(self):
        for graph in self.graphs:
            graph.close()

    def add(self, (s, p, o)):
        raise ModificationException()

    def addN(self, quads):
        raise ModificationException()

    def remove(self, (s, p, o)):
        raise ModificationException()

    def triples(self, (s, p, o)):
        for graph in self.graphs:
            for s1, p1, o1 in graph.triples((s, p, o)):
                yield (s1, p1, o1)

    def quads(self,(s,p,o)):
        """Iterate over all the quads in the entire aggregate graph"""
        for graph in self.graphs:
            for s1, p1, o1 in graph.triples((s, p, o)):
                yield (s1, p1, o1, graph)

    def __len__(self):
        return reduce(lambda x, y: x + y, [len(g) for g in self.graphs])

    def __hash__(self):
        raise UnSupportedAggregateOperation()

    def __cmp__(self, other):
        if other is None:
            return -1
        elif isinstance(other, Graph):
            return -1
        elif isinstance(other, ReadOnlyGraphAggregate):
            return cmp(self.graphs, other.graphs)
        else:
            return -1

    def __iadd__(self, other):
        raise ModificationException()

    def __isub__(self, other):
        raise ModificationException()

    # Conv. methods

    def triples_choices(self, (subject, predicate, object_), context=None):
        for graph in self.graphs:
            choices = graph.triples_choices((subject, predicate, object_))
            for (s, p, o) in choices:
                yield (s, p, o)

    def qname(self, uri):
        raise UnSupportedAggregateOperation()

    def compute_qname(self, uri):
        raise UnSupportedAggregateOperation()

    def bind(self, prefix, namespace, override=True):
        raise UnSupportedAggregateOperation()

    def namespaces(self):
        if hasattr(self,'namespace_manager'):
            for prefix, namespace in self.namespace_manager.namespaces():
                yield prefix, namespace
        else:
            for graph in self.graphs:
                for prefix, namespace in graph.namespaces():
                    yield prefix, namespace

    def absolutize(self, uri, defrag=1):
        raise UnSupportedAggregateOperation()

    def parse(self, source, publicID=None, format="xml", **args):
        raise ModificationException()

    def n3(self):
        raise UnSupportedAggregateOperation()

    def __reduce__(self):
        raise UnSupportedAggregateOperation()


class Collection(object):
    """
    See 3.3.5 Emulating container types: http://docs.python.org/ref/sequence-types.html#l2h-232

    >>> from rdflib.term import BNode
    >>> from rdflib.term import Literal
    >>> from rdflib.graph import Graph    
    >>> listName = BNode()
    >>> g = Graph('IOMemory')
    >>> listItem1 = BNode()
    >>> listItem2 = BNode()
    >>> g.add((listName,RDF.first,Literal(1)))
    >>> g.add((listName,RDF.rest,listItem1))
    >>> g.add((listItem1,RDF.first,Literal(2)))
    >>> g.add((listItem1,RDF.rest,listItem2))
    >>> g.add((listItem2,RDF.rest,RDF.nil))
    >>> g.add((listItem2,RDF.first,Literal(3)))
    >>> c=Collection(g,listName)
    >>> print list(c)
    [rdflib.Literal(u'1', lang=None, datatype=rdflib.URIRef('http://www.w3.org/2001/XMLSchema#integer')), rdflib.Literal(u'2', lang=None, datatype=rdflib.URIRef('http://www.w3.org/2001/XMLSchema#integer')), rdflib.Literal(u'3', lang=None, datatype=rdflib.URIRef('http://www.w3.org/2001/XMLSchema#integer'))]
    >>> 1 in c
    True
    >>> len(c)
    3
    >>> c._get_container(1) == listItem1
    True
    >>> c.index(Literal(2)) == 1
    True
    """
    def __init__(self, graph, uri, seq=[]):
        self.graph = graph
        self.uri = uri or BNode()
        for item in seq:
            self.append(item)

    def n3(self):
        """
        >>> from rdflib.term import BNode
        >>> from rdflib.term import Literal
        >>> from rdflib.graph import Graph    
        >>> listName = BNode()
        >>> g = Graph('IOMemory')
        >>> listItem1 = BNode()
        >>> listItem2 = BNode()
        >>> g.add((listName,RDF.first,Literal(1)))
        >>> g.add((listName,RDF.rest,listItem1))
        >>> g.add((listItem1,RDF.first,Literal(2)))
        >>> g.add((listItem1,RDF.rest,listItem2))
        >>> g.add((listItem2,RDF.rest,RDF.nil))
        >>> g.add((listItem2,RDF.first,Literal(3)))
        >>> c=Collection(g,listName)
        >>> print c.n3()
        ( "1"^^<http://www.w3.org/2001/XMLSchema#integer> "2"^^<http://www.w3.org/2001/XMLSchema#integer> "3"^^<http://www.w3.org/2001/XMLSchema#integer> )
        """
        return "( %s )"%(' '.join([i.n3() for i in self]))

    def _get_container(self, index):
        """Gets the first, rest holding node at index."""
        assert isinstance(index, int)
        graph = self.graph
        container = self.uri
        i = 0
        while i<index:
            i += 1
            container = graph.value(container, RDF.rest)
            if container is None:
                break
        return container

    def __len__(self):
        """length of items in collection."""
        count = 0
        links=set()
        for item in self.graph.items(self.uri):
            assert item not in links,"There is a loop in the RDF list! (%s has been processed before)"%item
            links.add(item)
            count += 1
        return count

    def index(self, item):
        """
        Returns the 0-based numerical index of the item in the list          
        """
        listName = self.uri
        index = 0
        while True:
            if (listName,RDF.first,item) in self.graph:
                return index
            else:
                newLink = list(self.graph.objects(listName,RDF.rest))
                index += 1
                if newLink == [RDF.nil]:
                    raise ValueError("%s is not in %s"%(item,self.uri))
                elif not newLink:
                    raise Exception("Malformed RDF Collection: %s"%self.uri)
                else:
                    assert len(newLink)==1, "Malformed RDF Collection: %s"%self.uri
                    listName = newLink[0]

    def __getitem__(self, key):
        """TODO"""
        c = self._get_container(key)
        if c:
            v = self.graph.value(c, RDF.first)
            if v:
                return v
            else:
                raise KeyError, key
        else:
            raise IndexError, key

    def __setitem__(self, key, value):
        """TODO"""
        c = self._get_container(key)
        if c:
            self.graph.add((c, RDF.first, value))
        else:
            raise IndexError, key


    def __delitem__(self, key):
        """
        >>> from rdflib.namespace import RDF, RDFS
        >>> from pprint import pformat
        >>> g=Graph()
        >>> a=BNode('foo')
        >>> b=BNode('bar')
        >>> c=BNode('baz')
        >>> g.add((a,RDF.first,RDF.type))
        >>> g.add((a,RDF.rest,b))
        >>> g.add((b,RDF.first,RDFS.label))
        >>> g.add((b,RDF.rest,c))
        >>> g.add((c,RDF.first,RDFS.comment))
        >>> g.add((c,RDF.rest,RDF.nil))
        >>> len(g)
        6
        >>> def listAncestry(node,graph):
        ...   for i in graph.subjects(RDF.rest,node): 
        ...     yield i
        >>> [str(node.n3()) for node in g.transitiveClosure(listAncestry,RDF.nil)]
        ['_:baz', '_:bar', '_:foo']
        >>> lst=Collection(g,a)
        >>> len(lst)
        3
        >>> b==lst._get_container(1)
        True
        >>> c==lst._get_container(2)
        True
        >>> del lst[1]
        >>> len(lst)
        2
        >>> len(g)
        4
        
        """
        self[key] # to raise any potential key exceptions
        graph = self.graph
        current = self._get_container(key)
        assert current
        if len(self)==1 and key>0:
            pass
        elif key==len(self)-1:
            #the tail
            priorLink = self._get_container(key-1)
            self.graph.set((priorLink,RDF.rest,RDF.nil))
            graph.remove((current, None, None))
        else:
            next = self._get_container(key+1)
            prior = self._get_container(key-1)
            assert next and prior
            graph.remove((current, None, None))
            graph.set((prior, RDF.rest, next))

    def __iter__(self):
        """Iterator over items in Collections"""
        return self.graph.items(self.uri)

    def append(self, item):
        """
        >>> from rdflib.graph import Graph    
        >>> listName = BNode()
        >>> g = Graph()
        >>> c=Collection(g,listName,[Literal(1),Literal(2)])
        >>> links = [list(g.subjects(object=i,predicate=RDF.first))[0] for i in c]
        >>> len([i for i in links if (i,RDF.rest,RDF.nil) in g])
        1
        
        """
        container = self.uri
        graph = self.graph
        #iterate to the end of the linked list
        rest = graph.value(container, RDF.rest)
        while rest:
            if rest == RDF.nil:
                #the end, append to the end of the linked list
                node = BNode()
                graph.set((container, RDF.rest, node))
                container=node                
                break
            else:
                #move down one link
                if container != self.uri:
                    rest = graph.value(rest, RDF.rest)
                if not rest == RDF.nil:
                    container=rest
        graph.add((container, RDF.first, item))
        graph.add((container, RDF.rest, RDF.nil))

    def clear(self):
        container = self.uri
        graph = self.graph
        while container:
            rest = graph.value(container, RDF.rest)
            graph.remove((container, RDF.first, None))
            graph.remove((container, RDF.rest, None))
            container = rest


class NamespaceManager(object):
    def __init__(self, graph):
        self.graph = graph
        self.__cache = {}
        self.__log = None
        self.bind("xml", u"http://www.w3.org/XML/1998/namespace")
        self.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")

    def reset(self):
        self.__cache = {}

    def __get_store(self):
        return self.graph.store
    store = property(__get_store)

    def qname(self, uri):
        prefix, namespace, name = self.compute_qname(uri)
        if prefix=="":
            return name
        else:
            return ":".join((prefix, name))

    def normalizeUri(self,rdfTerm):
        """
        Takes an RDF Term and 'normalizes' it into a QName (using the registered prefix)
        or (unlike compute_qname) the Notation 3 form for URIs: <...URI...> 
        """
        try:
            namespace, name = split_uri(rdfTerm)
            namespace = URIRef(namespace)
        except:
            if isinstance(rdfTerm,Variable):
                return "?%s"%rdfTerm
            else:
                return "<%s>"%rdfTerm
        prefix = self.store.prefix(namespace)
        if prefix is None and isinstance(rdfTerm,Variable):
            return "?%s"%rdfTerm
        elif prefix is None:
            return "<%s>"%rdfTerm
        else:
            qNameParts = self.compute_qname(rdfTerm)         
            return ':'.join([qNameParts[0],qNameParts[-1]])    

    def compute_qname(self, uri):
        if not uri in self.__cache:
            namespace, name = split_uri(uri)
            namespace = URIRef(namespace)
            prefix = self.store.prefix(namespace)
            if prefix is None:
                prefix = "_%s" % len(list(self.store.namespaces()))
                self.bind(prefix, namespace)
            self.__cache[uri] = (prefix, namespace, name)
        return self.__cache[uri]

    def bind(self, prefix, namespace, override=True):
        namespace = URIRef(namespace)
        # When documenting explain that override only applies in what cases
        if prefix is None:
            prefix = ''
        bound_namespace = self.store.namespace(prefix)
        if bound_namespace and bound_namespace!=namespace:
            # prefix already in use for different namespace
            #
            # append number to end of prefix until we find one
            # that's not in use.
            if not prefix:
                prefix = "default"
            num = 1
            while 1:
                new_prefix = "%s%s" % (prefix, num)
                if not self.store.namespace(new_prefix):
                    break
                num +=1
            self.store.bind(new_prefix, namespace)
        else:
            bound_prefix = self.store.prefix(namespace)
            if bound_prefix is None:
                self.store.bind(prefix, namespace)
            elif bound_prefix == prefix:
                pass # already bound
            else:
                if override or bound_prefix.startswith("_"): # or a generated prefix
                    self.store.bind(prefix, namespace)

    def namespaces(self):
        for prefix, namespace in self.store.namespaces():
            namespace = URIRef(namespace)
            yield prefix, namespace

    def absolutize(self, uri, defrag=1):
        base = urljoin("file:", pathname2url(os.getcwd()))
        result = urljoin("%s/" % base, uri, allow_fragments=not defrag)
        if defrag:
            result = urldefrag(result)[0]
        if not defrag:
            if uri and uri[-1]=="#" and result[-1]!="#":
                result = "%s#" % result
        return URIRef(result)


# TODO: find a home for any of the following 
#   
# from string import rsplit

# from rdflib.term import URIRef
# from rdflib.term import BNode
# from rdflib.term import Literal
# from rdflib.term import Variable
# from rdflib.term import Statement
# from rdflib.graph import Graph, QuotedGraph

# from rdflib.exceptions import SubjectTypeError, PredicateTypeError, ObjectTypeError, ContextTypeError


# def list2set(seq):
#     seen = set()
#     return [ x for x in seq if x not in seen and not seen.add(x)]

# def first(seq):
#     for result in seq:
#         return result
#     return None

# def uniq(sequence, strip=0):
#     """removes duplicate strings from the sequence."""
#     set = {}
#     if strip:
#         map(lambda val, default: set.__setitem__(val.strip(), default),
#             sequence, [])
#     else:
#         map(set.__setitem__, sequence, [])
#     return set.keys()

# def more_than(sequence, number):
#     "Returns 1 if sequence has more items than number and 0 if not."
#     i = 0
#     for item in sequence:
#         i += 1
#         if i > number:
#             return 1
#     return 0

# def term(str, default=None):
#     """See also from_n3"""
#     if not str:
#         return default
#     elif str.startswith("<") and str.endswith(">"):
#         return URIRef(str[1:-1])
#     elif str.startswith('"') and str.endswith('"'):
#         return Literal(str[1:-1])
#     elif str.startswith("_"):
#         return BNode(str)
#     else:
#         msg = "Unknown Term Syntax: '%s'" % str
#         raise Exception(msg)



# from time import mktime, time, gmtime, localtime, timezone, altzone, daylight

# def date_time(t=None, local_time_zone=False):
#     """http://www.w3.org/TR/NOTE-datetime ex: 1997-07-16T19:20:30Z

#     >>> date_time(1126482850)
#     '2005-09-11T23:54:10Z'

#     @@ this will change depending on where it is run
#     #>>> date_time(1126482850, local_time_zone=True)
#     #'2005-09-11T19:54:10-04:00'

#     >>> date_time(1)
#     '1970-01-01T00:00:01Z'

#     >>> date_time(0)
#     '1970-01-01T00:00:00Z'
#     """
#     if t is None:
#         t = time()

#     if local_time_zone:
#         time_tuple = localtime(t)
#         if time_tuple[8]:
#             tz_mins = altzone // 60
#         else:
#             tz_mins = timezone // 60
#         tzd = "-%02d:%02d" % (tz_mins // 60, tz_mins % 60)
#     else:
#         time_tuple = gmtime(t)
#         tzd = "Z"

#     year, month, day, hh, mm, ss, wd, y, z = time_tuple
#     s = "%0004d-%02d-%02dT%02d:%02d:%02d%s" % ( year, month, day, hh, mm, ss, tzd)
#     return s

# def parse_date_time(val):
#     """always returns seconds in UTC

#     # tests are written like this to make any errors easier to understand
#     >>> parse_date_time('2005-09-11T23:54:10Z') - 1126482850.0
#     0.0

#     >>> parse_date_time('2005-09-11T16:54:10-07:00') - 1126482850.0
#     0.0

#     >>> parse_date_time('1970-01-01T00:00:01Z') - 1.0
#     0.0

#     >>> parse_date_time('1970-01-01T00:00:00Z') - 0.0
#     0.0
#     >>> parse_date_time("2005-09-05T10:42:00") - 1125916920.0
#     0.0
#     """

#     if "T" not in val:
#         val += "T00:00:00Z"

#     ymd, time = val.split("T")
#     hms, tz_str = time[0:8], time[8:]

#     if not tz_str or tz_str=="Z":
#         time = time[:-1]
#         tz_offset = 0
#     else:
#         signed_hrs = int(tz_str[:3])
#         mins = int(tz_str[4:6])
#         secs = (cmp(signed_hrs, 0) * mins + signed_hrs * 60) * 60
#         tz_offset = -secs

#     year, month, day = ymd.split("-")
#     hour, minute, second = hms.split(":")

#     t = mktime((int(year), int(month), int(day), int(hour),
#                 int(minute), int(second), 0, 0, 0))
#     t = t - timezone + tz_offset
#     return t

# def from_n3(s, default=None, backend=None):
#     """ Creates the Identifier corresponding to the given n3 string. WARNING: untested, may contain bugs. TODO: add test cases."""
#     if not s:
#         return default
#     if s.startswith('<'):
#         return URIRef(s[1:-1])
#     elif s.startswith('"'):
#         # TODO: would a regex be faster?
#         value, rest = rsplit(s, '"', 1)
#         value = value[1:] # strip leading quote
#         if rest.startswith("@"):
#             if "^^" in rest:
#                 language, rest = rsplit(rest, '^^', 1)
#                 language = language[1:] # strip leading at sign
#             else:
#                 language = rest[1:] # strip leading at sign
#                 rest = ''
#         else:
#             language = None
#         if rest.startswith("^^"):
#             datatype = rest[3:-1]
#         else:
#             datatype = None
#         value = value.replace('\\"', '"').replace('\\\\', '\\').decode("unicode-escape")
#         return Literal(value, language, datatype)
#     elif s.startswith('{'):
#         identifier = from_n3(s[1:-1])
#         return QuotedGraph(backend, identifier)
#     elif s.startswith('['):
#         identifier = from_n3(s[1:-1])
#         return Graph(backend, identifier)
#     else:
#         if s.startswith("_:"):
#             return BNode(s[2:])
#         else:
#             return BNode(s)

# def check_context(c):
#     if not (isinstance(c, URIRef) or \
#             isinstance(c, BNode)):
#         raise ContextTypeError("%s:%s" % (c, type(c)))

# def check_subject(s):
#     """ Test that s is a valid subject identifier."""
#     if not (isinstance(s, URIRef) or isinstance(s, BNode)):
#         raise SubjectTypeError(s)

# def check_predicate(p):
#     """ Test that p is a valid predicate identifier."""
#     if not isinstance(p, URIRef):
#         raise PredicateTypeError(p)

# def check_object(o):
#     """ Test that o is a valid object identifier."""
#     if not (isinstance(o, URIRef) or \
#             isinstance(o, Literal) or \
#             isinstance(o, BNode)):
#         raise ObjectTypeError(o)

# def check_statement((s, p, o)):
#     if not (isinstance(s, URIRef) or isinstance(s, BNode)):
#         raise SubjectTypeError(s)

#     if not isinstance(p, URIRef):
#         raise PredicateTypeError(p)

#     if not (isinstance(o, URIRef) or \
#             isinstance(o, Literal) or \
#             isinstance(o, BNode)):
#         raise ObjectTypeError(o)

# def check_pattern((s, p, o)):
#     if s and not (isinstance(s, URIRef) or isinstance(s, BNode)):
#         raise SubjectTypeError(s)

#     if p and not isinstance(p, URIRef):
#         raise PredicateTypeError(p)

#     if o and not (isinstance(o, URIRef) or \
#                   isinstance(o, Literal) or \
#                   isinstance(o, BNode)):
#         raise ObjectTypeError(o)

# def graph_to_dot(graph, dot):
#     """ Turns graph into dot (graphviz graph drawing format) using pydot. """
#     import pydot
#     nodes = {}
#     for s, o in graph.subject_objects():
#         for i in s,o:
#             if i not in nodes.keys():
#                 nodes[i] = i
#     for s, p, o in graph.triples((None,None,None)):
#         dot.add_edge(pydot.Edge(nodes[s], nodes[o], label=p))


 


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
