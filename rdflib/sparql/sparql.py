"""SPARQL implementation on top of RDFLib

Implementation of the <a href="http://www.w3.org/TR/rdf-sparql-query/">W3C SPARQL</a>
language (version April 2005). The basic class here is
supposed to be a superclass of L{rdflib.sparql.sparqlGraph}; it has
been separated only for a better maintainability.

There is a separate
U{description<http://dev.w3.org/cvsweb/%7Echeckout%7E/2004/PythonLib-IH/Doc/sparqlDesc.html>}
for the functionalities.

"""

##########################################################################
from rdflib.Literal     import Literal
from rdflib.BNode       import BNode
from rdflib.URIRef      import URIRef
from rdflib.exceptions  import Error
from rdflib.util        import check_predicate, check_subject, check_object, list2set

################
#This was used in a previous, work version of the
# implementation, but it may be unnecessary. I keep it for now,
# because the operators are also prepared to this. If it proves to be
# really unnecessary, I can always throw it away, it does not really
# influence efficiency or anything else.
JunkResource = URIRef("http://www.ivan-herman.net/SPARQLJunk")

import sys, sets, datetime
from types import *

Debug = False

##########################################################################
# XML Schema datatypes
type_string   = "http://www.w3.org/2001/XMLSchema#string"
type_integer  = "http://www.w3.org/2001/XMLSchema#integer"
type_long     = "http://www.w3.org/2001/XMLSchema#long"
type_double   = "http://www.w3.org/2001/XMLSchema#double"
type_float    = "http://www.w3.org/2001/XMLSchema#float"
type_decimal  = "http://www.w3.org/2001/XMLSchema#decimal"
type_dateTime = "http://www.w3.org/2001/XMLSchema#dateTime"
type_date     = "http://www.w3.org/2001/XMLSchema#date"
type_time     = "http://www.w3.org/2001/XMLSchema#time"

# Mapping from the Python types to the corresponding XML Schema types. Note that, for internal purposes, strings
# are just used in a plain format, not with the XML Schema version (the XML Schema string is a default for
# an RDF datatype, hence this here)
_basicTypes = {
    IntType     : type_integer,
    FloatType   : type_float,
    StringType  : "",
    UnicodeType : "",
    LongType    : type_long
}

# Some extra types that are not based on the basic Pythong types but on existing library classes.
_extraTypes = {
    datetime.datetime  : type_dateTime,
    datetime.date      : type_date,
    datetime.time      : type_time,
}

##########################################################################
# Utilities

# Note that the SPARQL draft allows the usage of a different query character, but I decided not to be that
# generous, and keep to one only. I put it into a separate variable to avoid problems if the group decides
# to change the syntax on that detail...
_questChar  = "?"

# Key (in the final bindings) for the background graph for the specific query
_graphKey = "$$GRAPH$$"

##
# SPARQL Error Exception (subclass of the RDFLib Exceptions)
class SPARQLError(Error) :
    """Am SPARQL error has been detected"""
    def __init__(self,msg):
        Error.__init__(self, ("SPARQL Error: %s." % msg))

class Unbound :
    """A class to encapsulate a query variable. This class should be used in conjunction with L{BasicGraphPattern<graphPattern.BasicGraphPattern>}."""
    def __init__(self,name) :
        """
        @param name: the name of the variable (without the '?' character)
        @type name: unicode or string
        """
        from sparql import _questChar, Debug
        if isinstance(name,basestring) :
            self.name     = _questChar + name
            self.origName = name
        else :
            raise SPARQLError("illegal argument, variable name must be a string or unicode")

    def __repr__(self) :
        retval  = "?%s" % self.origName
        return retval

    def __str__(self) :
        return self.__repr__()

class PatternBNode :
    """A class to encapsulate a BNode in a Pattern. This class should be used in conjunction
    with L{BasicGraphPattern<graphPattern.BasicGraphPattern>}.

    Usage of this class may be necessary when the query is used for a L{graph construction<Query.construct>}.
    """
    def __init__(self,name) :
        """
        @param name: the name of the bnode (without the '_:' characters)
        @type name: unicode or string
        """
        from sparql import _questChar, Debug
        if isinstance(name,basestring) :
            self.name     = name
        else :
            raise SPARQLError("illegal argument, variable name must be a string or unicode")

    def __repr__(self) :
        retval  = "_:%s" % self.name
        return retval

    def __str__(self) :
        return self.__repr__()

def _variablesToArray(variables,name='') :
    """Turn an array of Variables or query strings into an array of query strings. If the 'variables'
    is in fact a single string or Variable, then it is also put into an array.

    @param variables: a string, a unicode, or a Variable, or an array of those (can be mixed, actually). As a special case,
    if the value is "*", it returns None (this corresponds to the wildcard in SPARQL)
    @param name: the string to be used in the error message
    """
    if isinstance(variables,basestring) :
        if variables == "*" :
            return None
        else :
            return [variables]
    elif isinstance(variables,Unbound) :
        return [variables.name]
    elif type(variables) == list or type(variables) == tuple :
        retval = []
        for s in variables :
            if isinstance(s,basestring) :
                retval.append(s)
            elif isinstance(s,Unbound) :
                retval.append(s.name)
            else :
                raise SPARQLError("illegal type in '%s'; must be a string, unicode, or a Variable" % name)
    else :
        raise SPARQLError("'%s' argument must be a string, a Variable, or a list of those" % name)
    return retval

def _schemaType(v) :
    """Return an XML Schema type starting from a Python variable. An
    exception is raised if the variable does not corresponds to any of
    the schema types that are allowed by this implementation. A
    SPARQLError Exception is raised if the type represents a
    non-implemented type.

    @param v: Python variable
    @return: URI for the XML Datatype
    @rtype: string
    @raise SPARQLError: if the type of 'v' is not implemented
    """
    # First the basic Types
    for t in _basicTypes :
        if type(v) is t :
            return _basicTypes[t]
    # Then the extra types
    for t in _extraTypes :
        if isinstance(v,t) :
            return _extraTypes[t]
    # if we got here, the type is illegal...
    raise SPARQLError("%s is not an accepted datatype" % v)

def _createResource(v) :
    """Create an RDFLib Literal instance with the corresponding XML
    Schema datatype set. If the variable is already an RDFLib
    resource, it simply returns the resource; otherwise the
    corresponding Literal.  A SPARQLError Exception is raised if the
    type is not implemented.

    The Literal contains the string representation of the variable (as
    Python does it by default) with the corresponding XML Schema URI
    set.

    @param v: Python variable
    @return: either an RDFLib Literal (if 'v' is not an RDFLib Resource), or the same variable if it is already
    an RDFLib resource (ie, Literal, BNode, or URIRef)
    @raise SPARQLError: if the type of 'v' is not implemented
    """
    if isinstance(v,Literal) or isinstance(v,BNode) or isinstance(v,URIRef) :
        # just do nothing
        return v
    else :
        xmlDatatype = _schemaType(v)
        # note: if there was an error with the type, an exception has been raised at this point
        # unfortunately, some of the default python data->string conversions are not the same
        # as required by the XML Schema datatype document :-(
        # Otherwise, relies on the fact that the init of Literal uses, essentially, the `` operator of
        # python to store the value.
        if xmlDatatype == type_dateTime :
            # XML Schema requires a "T" separator, and this is not the default for the conversion...
            return Literal(v.isoformat(sep="T"),datatype=xmlDatatype)
        else :
            return Literal(v,datatype=xmlDatatype)

def _isResQuest(r) :
    """
    Is 'r' a request string (ie, of the form "?XXX")?

    @rtype: Boolean
    """
    if r and isinstance(r,basestring) and r[0] == _questChar :
        return True
    return False


def _processResults(select,arr) :
    '''
    The result in an expansion node is in the form of an array of
    binding dictionaries.  The caller should receive an array of
    tuples, each tuple representing the final binding (or None) I{in
    the order of the original select}. This method is the last step of
    processing by processing these values to produce the right result.

    @param select: the original selection list. If None, then the
    binding should be taken as a whole (this corresponds to the SELECT * feature of SPARQL)
    @param arr: the array of bindings
    @type arr:
    an array of dictionaries
    @return: a list of tuples with the selection results
    '''
    retval = []
    if select :
        for bind in arr :
            # each result binding must be taken separately
            qresult = []
            for s in select :
                if s in bind :
                    qresult.append(bind[s])
                else :
                    qresult.append(None)
            # as a courtesy to the user, if the selection has one single element only, than we do no
            # put in a tuple, just add it that way:
            if len(select) == 1 :
                retval.append(qresult[0])
            else :
                retval.append(tuple(qresult))
    else :
        # this is the case corresponding to a SELECT * query call
        for bind in arr:
            qresult = [val for key,val in bind.items() if key != _graphKey]
            if len(qresult) == 1 :
                retval.append(qresult[0])
            else :
                retval.append(tuple(qresult))
    return retval


class Query :
    """
    Result of a SPARQL query. It stores to the top of the query tree, and allows some subsequent
    inquiries on the expanded tree. B{This class should not be
    instantiated by the user,} it is done by the L{queryObject<SPARQL.queryObject>} method.

    """
    def __init__(self,sparqlnode,triples,parent1=None,parent2=None) :
        """
        @param sparqlnode: top of the expansion tree
        @type sparqlnode: _SPARQLNode
        @param triples: triple store
        @type triples: L{sparqlGraph<rdflib.sparql.sparqlGraph>}
        @param parent1: possible parent Query when queries are combined by summing them up
        @type parent1: L{Query}
        @param parent2: possible parent Query when queries are combined by summing them up
        @type parent2: L{Query}
        """
        self.top             = sparqlnode
        self.triples         = triples
        # if this node is the result of a sum...
        self.parent1         = parent1
        self.parent2         = parent2

    def __add__(self,other) :
        """This may be useful when several queries are performed and
        one wants the 'union' of those.  Caveat: the triple store must
        be the same for each argument. This method is used internally
        only anyway...  Efficiency trick (I hope it works): the
        various additions on subgraphs are not done here; the results
        are calculated only if really necessary, ie, in a lazy
        evaluation manner.  This is achieved by storing self and the
        'other' in the new object
        """
        return Query(None,self.triples,self,other)

    def _getFullBinding(self) :
        """Retrieve the full binding, ie, an array of binding dictionaries
        """
        if self.parent1 != None and self.parent2 != None :
            return self.parent1._getFullBinding() + self.parent2._getFullBinding()
        else :
            # remember: returnResult returns an array of dictionaries
            return self.top.returnResult(None)

    def _getAllVariables(self):
       """Retrieve the list of all variables, to be returned"""
       if self.parent1 and self.parent2:
           return list2set(self.parent1._getAllVariables() + self.parent2._getAllVariables())
       else:
           return list2set(self.top.bindings.keys())

    def _orderedSelect(self,selection,orderedBy,orderDirection) :
        """
        The variant of the selection (as below) that also includes the sorting. Because that is much less efficient, this is
        separated into a distinct method that is called only if necessary. It is called from the L{select<select>} method.
		
        Because order can be made on variables that are not part of the final selection, this method retrieves a I{full}
        binding from the result to be able to order it (whereas the core L{select<select>} method retrieves from the result
        the selected bindings only). The full binding is an array of (binding) dictionaries; the sorting sorts this array
        by comparing the bound variables in the respective dictionaries. Once this is done, the final selection is done.

        @param selection: Either a single query string, or an array or tuple thereof.
        @param orderBy: either a function or a list of strings (corresponding to variables in the query). If None, no sorting occurs
        on the results. If the parameter is a function, it must take two dictionary arguments (the binding dictionaries), return
        -1, 0, and 1, corresponding to smaller, equal, and greater, respectively.
        @param orderDirection: if not None, then an array of integers of the same length as orderBy, with values the constants
        ASC or DESC (defined in the module). If None, an ascending order is used.
        @return: selection results
        @rtype: list of tuples
        @raise SPARQLError: invalid sorting arguments
        """
        fullBinding = self._getFullBinding()
        if type(orderedBy) is FunctionType :
            _sortBinding = orderedBy
        else :
            orderKeys = _variablesToArray(orderedBy,"orderBy")
            # see the direction
            oDir = None # this is just to fool the interpreter's error message
            if orderDirection is None :
                oDir = [ True for i in xrange(0,len(orderKeys)) ]
            elif type(orderDirection) is BooleanType :
                oDir = [ orderDirection ]
            elif type(orderDirection) is not ListType and type(orderDirection) is not TupleType :
                raise SPARQLError("'orderDirection' argument must be a list")
            elif len(orderDirection) != len(orderKeys) :
                raise SPARQLError("'orderDirection' must be of an equal length to 'orderBy'")
            else :
                oDir = orderDirection
            def _sortBinding(b1,b2) :
                """The sorting method used by the array sort, with return values as required by the python run-time
                The to-be-compared data are dictionaries of bindings
                """
                for i in xrange(0,len(orderKeys)) :
					# each key has to be compared separately. If there is a clear comparison result on that key
					# then we are done, but when that is not the case, the next in line should be used
                    key       = orderKeys[i]
                    direction = oDir[i]
                    if key in b1 and key in b2 :
                        val1 = b1[key]
                        val2 = b2[key]
                        if val1 != None and val2 != None :
                            if direction :
                                if   val1 < val2 : return -1
                                elif val1 > val2 : return 1
                            else :
                                if   val1 > val2 : return -1
                                elif val1 < val2 : return 1
                return 0
        # get the full Binding sorted
        fullBinding.sort(_sortBinding)
        # remember: _processResult turns the expansion results (an array of dictionaries)
        # into an array of tuples in the right, original order
        retval = _processResults(selection,fullBinding)
        return retval

    def select(self,selection,distinct=True,limit=None,orderBy=None,orderAscend=None,offset=0) :
        """
        Run a selection on the query.

        @param selection: Either a single query string, or an array or tuple thereof.
        @param distinct: if True, identical results are filtered out
        @type distinct: Boolean
        @param limit: if set to an integer value, the first 'limit' number of results are returned; all of them otherwise
        @type limit: non negative integer
        @param orderBy: either a function or a list of strings (corresponding to variables in the query). If None, no sorting occurs
        on the results. If the parameter is a function, it must take two dictionary arguments (the binding dictionaries), return
        -1, 0, and 1, corresponding to smaller, equal, and greater, respectively.
        @param orderAscend: if not None, then an array of booelans of the same length as orderBy, True for ascending and False
		for descending. If None, an ascending order is used.
        @offset the starting point of return values in the array of results. Obviously, this parameter makes real sense if
        some sort of order is defined.
        @return: selection results
        @rtype: list of tuples
        @raise SPARQLError: invalid selection argument
        """
        def _uniquefyList(lst) :
            """Return a copy of the list but possible duplicate elements are taken out. Used to
            post-process the outcome of the query
            @param lst: input list
            @return: result list
            """
            if len(lst) <= 1 :
                return lst
            else :
                # must be careful! Using the quick method of Sets destroy the order. Ie, if this was ordered, then
                # a slower but more secure method should be used
                if orderBy != None :
                    retval = []
                    for i in xrange(0,len(lst)) :
                        v = lst[i]
                        skip = False
                        for w in retval :
                            if w == v :
                                skip = True
                                break
                        if not skip :
                            retval.append(v)
                    return retval
                else :
                    return list(sets.Set(lst))
        # Select may be a single query string, or an array/tuple thereof
        selectionF = _variablesToArray(selection,"selection")

        if type(offset) is not IntType or offset < 0 :
            raise SPARQLError("'offset' argument is invalid")

        if limit != None :
            if type(limit) is not IntType or limit < 0 :
                raise SPARQLError("'offset' argument is invalid")

        if orderBy != None :
            results = self._orderedSelect(selectionF,orderBy,orderAscend)
        else :
            if self.parent1 != None and self.parent2 != None :
                results = self.parent1.select(selectionF) + self.parent2.select(selectionF)
            else :
                # remember: _processResult turns the expansion results (an array of dictionaries)
                # into an array of tuples in the right, original order
                results = _processResults(selectionF,self.top.returnResult(selectionF))
        if distinct :
            retval = _uniquefyList(results)
        else :
            retval = results

        if limit != None :
            return retval[offset:limit+offset]
        elif offset > 0 :
            return retval[offset:]
        else :
            return retval

    def construct(self,pattern=None) :
        """
        Expand the subgraph based on the pattern or, if None, the
        internal bindings.

        In the former case the binding is used to instantiate the
        triplets in the patterns; in the latter, the original
        statements are used as patterns.

        The result is a separate triple store containing the subgraph.

        @param pattern: a L{GraphPattern<rdflib.sparql.graphPattern.GraphPattern>} instance or None
        @return: a new triple store
        @rtype: L{sparqlGraph<rdflib.sparql.sparqlGraph>}
        """
        from sparqlGraph import SPARQLGraph

        if self.parent1 != None and self.parent2 != None :
            return self.parent1.construct(pattern) + self.parent2.construct(pattern)
        else :
            subgraph = SPARQLGraph()
            self.top.expandSubgraph(subgraph,pattern)
            return subgraph

    def ask(self) :
        """
        Whether a specific pattern has a solution or not.
        @rtype: Boolean
        """
        return len(self.select('*')) != 0

    #########################################################################################################
    # The methods below are not really part of SPARQL, or may be used to a form of DESCRIBE. However, that latter
    # is still in a flux in the draft, so we leave it here, pending

    def clusterForward(self,selection) :
        """
        Forward clustering, using all the results of the query as
        seeds (when appropriate). It is based on the usage of the
        L{cluster forward<rdflib.sparql.sparqlGraph.clusterForward>}
        method for triple store.

        @param selection: a selection to define the seeds for
        clustering via the selection; the result of select used for
        the clustering seed

        @return: a new triple store
        @rtype: L{sparqlGraph<rdflib.sparql.sparqlGraph>}
        """
        from sparqlGraph import SPARQLGraph

        if self.parent1 != None and self.parent2 != None :
            return self.parent1.clusterForward(selection) + self.parent2.clusterForward(selection)
        else :
            clusterF = SPARQLGraph()
            for r in reduce(lambda x,y: list(x) + list(y),self.select(selection),()) :
                try :
                    check_subject(r)
                    self.triples.clusterForward(r,clusterF)
                except :
                    # no real problem, this is a literal, just forget about it
                    continue
            return clusterF

    def clusterBackward(self,selection) :
        """
        Backward clustering, using all the results of the query as
        seeds (when appropriate). It is based on the usage of the
        L{cluster backward<rdflib.sparql.sparqlGraph.clusterBackward>}
        method for triple store.

        @param selection: a selection to define the seeds for
        clustering via the selection; the result of select used for
        the clustering seed

        @return: a new triple store
        @rtype: L{sparqlGraph<rdflib.sparql.sparqlGraph>}
        """
        from sparqlGraph import SPARQLGraph

        if self.parent1 != None and self.parent2 != None :
            return self.parent1.clusterBackward(selection) + self.parent2.clusterBackward(selection)
        else :
            clusterB = SPARQLGraph()
            # to be on the safe side, see if the query has been properly finished
            for r in reduce(lambda x,y: list(x) + list(y),self.select(selection),()) :
                self.triples.clusterBackward(r,clusterB)
            return clusterB

    def cluster(self,selection) :
        """
        Cluster: a combination of L{Query.clusterBackward} and
        L{Query.clusterForward}.  @param selection: a selection to
        define the seeds for clustering via the selection; the result
        of select used for the clustering seed
        """
        return self.clusterBackward(selection) + self.clusterForward(selection)

    def describe(self,selection,forward=True,backward=True) :
        """
        The DESCRIBE Form in the SPARQL draft is still in state of
        flux, so this is just a temporary method, in fact.  It may not
        correspond to what the final version of describe will be (if
        it stays in the draft at all, that is).  At present, it is
        simply a wrapper around L{cluster}.

        @param selection: a selection to define the seeds for
        clustering via the selection; the result of select used for
        the clustering seed

        @param forward: cluster forward yes or no
        @type forward: Boolean
        @param backward: cluster backward yes or no
        @type backward: Boolean
        """
        from sparqlGraph import SPARQLGraph

        if forward and backward :
            return self.cluster(selection)
        elif forward :
            return self.clusterForward(selection)
        elif backward :
            return self.clusterBackward(selection)
        else :
            return SPARQLGraph()

