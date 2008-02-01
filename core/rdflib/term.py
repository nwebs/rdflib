"""
This module defines the different types of terms...

"""

import base64
import logging
import threading

from sys import version_info
from datetime import date,time,datetime
from time import strptime
from string import rsplit

try:
    from hashlib import md5
except ImportError:
    from md5 import md5    

# if version_info[0:2] > (2, 2):
#     from unicodedata import normalize
# else:
#     normalize = None

from urlparse import urlparse, urljoin, urldefrag


_logger = logging.getLogger(__name__)


class Term(object):
    """
    A Term...
    """
    __slots__ = ()


class Identifier(Term, unicode): 
    """
    See http://www.w3.org/2002/07/rdf-identifer-terminology/
    regarding choice of terminology.
    """
    __slots__ = ()
    def __new__(cls, value):
        return unicode.__new__(cls,value)


"""
This module defines a BNode class.

Applications should typically create a BNode instance without
specifying a specific value. Support for specifying a specific value
is primarily for store implementations to be able to create BNodes
with a specific value (AKA label).

    >>> from rdflib.term import BNode
    >>> b = BNode()
    >>> b.__class__
    <class 'rdflib.term.BNode'>

"""

def _unique_id():
    """
    Create a (hopefully) unique prefix
    """
    from string import ascii_letters
    from random import choice

    id = ""
    for i in xrange(0,8):
        id += choice(ascii_letters)
    return id

def _serial_number_generator():
    i = 0
    while 1:
        yield i
        i = i + 1


bNodeLock = threading.RLock()

class BNode(Identifier):
    """
    Blank Node: http://www.w3.org/TR/rdf-concepts/#section-blank-nodes

    "In non-persistent O-O software construction, support for object
    identity is almost accidental: in the simplest implementation,
    each object resides at a certain address, and a reference to the
    object uses that address, which serves as immutable object
    identity.

    ...

    Maintaining object identity in shared databases raises problems:
    every client that needs to create objects must obtain a unique
    identity for them; " -- Bertand Meyer
    """
    __slots__ = ()

    def __new__(cls, value=None, # only store implementations should pass in a value
                _sn_gen=_serial_number_generator(), _prefix=_unique_id()):
        if value==None:
            # so that BNode values do not
            # collide with ones created with a different instance of this module
            # at some other time.
            bNodeLock.acquire()
            node_id = _sn_gen.next()
            bNodeLock.release()
            value = "%s%s" % (_prefix, node_id)
        else:
            # TODO: check that value falls within acceptable bnode value range
            # for RDF/XML needs to be something that can be serialzed as a nodeID
            # for N3 ??
            # Unless we require these constraints be enforced elsewhere?
            pass #assert is_ncname(unicode(value)), "BNode identifiers must be valid NCNames"

        return Identifier.__new__(cls, value)

    def n3(self):
        return "_:%s" % self

    def __getnewargs__(self):
        return (unicode(self), )

    def __reduce__(self):
        return (BNode, (unicode(self),))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        """
        >>> from rdflib.term import URIRef
        >>> from rdflib.term import BNode
        >>> BNode("foo")==None
        False
        >>> BNode("foo")==URIRef("foo")
        False
        >>> URIRef("foo")==BNode("foo")
        False
        >>> BNode("foo")!=URIRef("foo")
        True
        >>> URIRef("foo")!=BNode("foo")
        True

        """
        if isinstance(other, BNode):
            return unicode(self)==unicode(other)
        else:
            return False

    def __str__(self):
        return self.encode("unicode-escape")

    def __repr__(self):
        return """rdflib.BNode('%s')""" % str(self)

    def md5_term_hash(self):
        d = md5(str(self))
        d.update("B")
        return d.hexdigest()





class URIRef(Identifier):
    """
    RDF URI Reference: http://www.w3.org/TR/rdf-concepts/#section-Graph-URIref

    >>> uri = URIRef("http://example.org/foo#bar")
    >>> uri
    rdflib.URIRef('http://example.org/foo#bar')

    >>> uri = URIRef("baz", base="http://example.org/")
    >>> uri.n3()
    u'<http://example.org/baz>'

    """

    __slots__ = ()

    def __new__(cls, value, base=None):
        if base is not None:
            ends_in_hash = value.endswith("#")
            value = urljoin(base, value, allow_fragments=1)
            if ends_in_hash:
                if not value.endswith("#"):
                    value += "#"
        #if normalize and value and value != normalize("NFC", value):
        #    raise Error("value must be in NFC normalized form.")
        try:
            rt = unicode.__new__(cls,value)
        except UnicodeDecodeError:
            rt = unicode.__new__(cls,value,'utf-8')
        return rt

    def n3(self):
        """
        Return the URIRef in n3 notation.
        """
        return "<%s>" % self

    def concrete(self):
        """
        Return the related concrete URIRef if this is a abstract
        URIRef. Else return the already concrete URIRef.

        NOTE: This is just one pattern for mapping between related
        concrete and abstract URIRefs.
        """
        if "#" in self:
            return URIRef("/".join(rsplit(self, "#", 1)))
        else:
            return self

    def abstract(self):
        """
        Return the related abstract URIRef if this is a concrete
        URIRef. Else return the already abstract URIRef.

        NOTE: This is just one pattern for mapping between related
        concrete and abstract URIRefs.
        """
        if "#" not in self:
            scheme, netloc, path, params, query, fragment = urlparse(self)
            if path:
                return URIRef("#".join(rsplit(self, "/", 1)))
            else:
                if not self.endswith("#"):
                    return URIRef("%s#" % self)
                else:
                    return self
        else:
            return self


    def defrag(self):
        """
        Defragment the URIRef and return the resulting URIRef.
        """
        if "#" in self:
            url, frag = urldefrag(self)
            return URIRef(url)
        else:
            return self

    def __reduce__(self):
        return (URIRef, (unicode(self),))

    def __getnewargs__(self):
        return (unicode(self), )


    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if isinstance(other, URIRef):
            return unicode(self)==unicode(other)
        else:
            return False

    def __str__(self):
        return self.encode("unicode-escape")

    def __repr__(self):
        return """rdflib.URIRef('%s')""" % str(self)

    def md5_term_hash(self):
        d = md5(str(self))
        d.update("U")
        return d.hexdigest()




class Literal(Identifier):
    """
    RDF Literal: http://www.w3.org/TR/rdf-concepts/#section-Graph-Literal

    >>> from rdflib.term import Literal
    >>> Literal(1).toPython()
    1L
    >>> cmp(Literal("adsf"), 1)
    1
    >>> from rdflib.term import _XSD_NS
    >>> from datetime import datetime
    >>> lit2006 = Literal('2006-01-01',datatype=_XSD_NS.date)
    >>> lit2006.toPython()
    datetime.date(2006, 1, 1)
    >>> lit2006 < Literal('2007-01-01',datatype=_XSD_NS.date)
    True
    >>> Literal(datetime.utcnow()).datatype
    rdflib.URIRef('http://www.w3.org/2001/XMLSchema#dateTime')
    >>> oneInt     = Literal(1)
    >>> twoInt     = Literal(2)
    >>> twoInt < oneInt
    False
    >>> Literal('1') < Literal(1)
    False
    >>> Literal('1') < Literal('1')
    False
    >>> Literal(1) < Literal('1')
    True
    >>> Literal(1) < Literal(2.0)
    True
    >>> Literal(1) < URIRef('foo')
    True
    >>> Literal(1) < 2.0
    True
    >>> Literal(1) < object  
    True
    >>> lit2006 < "2007"
    True
    >>> "2005" < lit2006
    True

    """

    __slots__ = ("language", "datatype", "_cmp_value")

    def __new__(cls, value, lang=None, datatype=None):
        if datatype:
            lang = None
        else:
            value,datatype = _castPythonToLiteral(value)
            if datatype:
                lang = None
        if datatype:
            datatype = URIRef(datatype)
        try:
            inst = unicode.__new__(cls,value)
        except UnicodeDecodeError:
            inst = unicode.__new__(cls,value,'utf-8')
        inst.language = lang
        inst.datatype = datatype
        inst._cmp_value = inst._toCompareValue()
        return inst

    def __reduce__(self):
        return (Literal, (unicode(self), self.language, self.datatype),)

    def __getstate__(self):
        return (None, dict(language=self.language, datatype=self.datatype))

    def __setstate__(self, arg):
        _, d = arg
        self.language = d["language"]
        self.datatype = d["datatype"]

    def __add__(self, val):
        """
        >>> Literal(1) + 1
        2L
        >>> Literal("1") + "1"
        rdflib.Literal(u'11', lang=None, datatype=None)

        """

        py = self.toPython()
        if isinstance(py, Literal):
            s = super(Literal, self).__add__(val)            
            return Literal(s, self.language, self.datatype)
        else:
            return py + val 


    
    def __lt__(self, other):
        r"""
        >>> Literal("YXNkZg==", datatype=_XSD_NS[u'base64Binary']) < "foo"
        True
        >>> u"\xfe" < Literal(u"foo")
        False
        >>> import base64
        >>> Literal(base64.encodestring(u"\xfe".encode("utf-8")), datatype=URIRef("http://www.w3.org/2001/XMLSchema#base64Binary")) < u"foo"
        False

        """

        if other is None:
            return False # Nothing is less than None
        try:
            return self._cmp_value < other
        except TypeError, te:
            return unicode(self._cmp_value) < other
        except UnicodeDecodeError, ue:
            if isinstance(self._cmp_value, str):
                return self._cmp_value < other.encode("utf-8")
            else:
                raise ue

    def __le__(self, other):
        if other is None:
            return False
        if self==other:
            return True
        else:
            return self < other

    def __gt__(self, other):
        if other is None:
            return True # Everything is greater than None
        try:
            return self._cmp_value > other
        except TypeError, te:
            return unicode(self._cmp_value) > other
        except UnicodeDecodeError, ue:
            if isinstance(self._cmp_value, str):
                return self._cmp_value > other.encode("utf-8")
            else:
                raise ue

    def __ge__(self, other):
        if other is None:
            return False
        if self==other:
            return True
        else:
            return self > other

    def __ne__(self, other):
        """
        Overriden to ensure property result for comparisons with None via !=.
        Routes all other such != and <> comparisons to __eq__
        
        >>> Literal('') != None
        True
        >>> Literal('2') <> Literal('2')
        False
         
        """
        return not self.__eq__(other)

    def __hash__(self):
        """
        >>> a = {Literal('1',datatype=_XSD_NS.integer):'one'}
        >>> Literal('1',datatype=_XSD_NS.double) in a
        False
        
        [[
        Called for the key object for dictionary operations, 
        and by the built-in function hash(). Should return 
        a 32-bit integer usable as a hash value for 
        dictionary operations. The only required property 
        is that objects which compare equal have the same 
        hash value; it is advised to somehow mix together 
        (e.g., using exclusive or) the hash values for the 
        components of the object that also play a part in 
        comparison of objects. 
        ]] -- 3.4.1 Basic customization (Python)

    
        [[
        Two literals are equal if and only if all of the following hold:
        * The strings of the two lexical forms compare equal, character by character.
        * Either both or neither have language tags.
        * The language tags, if any, compare equal.
        * Either both or neither have datatype URIs.
        * The two datatype URIs, if any, compare equal, character by character.
        ]] -- 6.5.1 Literal Equality (RDF: Concepts and Abstract Syntax)
        
        """
        return hash(u"%s"%self) ^ hash(self.language) ^ hash(self.datatype) 

    def __eq__(self, other):
        """        
        >>> f = URIRef("foo")
        >>> f is None or f == ''
        False
        >>> Literal("1", datatype=URIRef("foo")) == Literal("1", datatype=URIRef("foo"))
        True
        >>> Literal("1", datatype=URIRef("foo")) == Literal("2", datatype=URIRef("foo"))
        False
        >>> Literal("1", datatype=URIRef("foo")) == "asdf"
        False
        >>> Literal('2007-01-01', datatype=_XSD_NS.date) == Literal('2007-01-01', datatype=_XSD_NS.date)
        True
        >>> from datetime import date
        >>> Literal('2007-01-01', datatype=_XSD_NS.date) == date(2007, 1, 1)
        True
        >>> oneInt     = Literal(1)
        >>> oneNoDtype = Literal('1')
        >>> oneInt == oneNoDtype
        False
        >>> Literal("1",_XSD_NS[u'string']) == Literal("1",_XSD_NS[u'string'])
        True
        >>> Literal("one",lang="en") == Literal("one",lang="en")
        True
        >>> Literal("hast",lang='en') == Literal("hast",lang='de')
        False
        >>> oneInt == Literal(1)
        True
        >>> oneFloat   = Literal(1.0)
        >>> oneInt == oneFloat
        True
        >>> oneInt == 1
        True
        
        """
        if other is None:
            return False
        if isinstance(other, Literal):
            return self._cmp_value == other._cmp_value
        else:
            return self._cmp_value == other

    def n3(self):
        language = self.language
        datatype = self.datatype
        # unfortunately this doesn't work: a newline gets encoded as \\n, which is ok in sourcecode, but we want \n
        #encoded = self.encode('unicode-escape').replace('\\', '\\\\').replace('"','\\"')
        #encoded = self.replace.replace('\\', '\\\\').replace('"','\\"')

        # TODO: We could also chose quotes based on the quotes appearing in the string, i.e. '"' and "'" ...

        # which is nicer?
        #if self.find("\"")!=-1 or self.find("'")!=-1 or self.find("\n")!=-1:
        if self.find("\n")!=-1:
            # Triple quote this string.
            encoded=self.replace('\\', '\\\\')
            if self.find('"""')!=-1: 
                # is this ok?
                encoded=encoded.replace('"""','\\"""')
            if encoded.endswith('"'): encoded=encoded[:-1]+"\\\""
            encoded='"""%s"""'%encoded
        else: 
            encoded='"%s"'%self.replace('\n','\\n').replace('\\', '\\\\').replace('"','\\"')
        if language:
            if datatype:    
                return '%s@%s^^<%s>' % (encoded, language, datatype)
            else:
                return '%s@%s' % (encoded, language)
        else:
            if datatype:
                return '%s^^<%s>' % (encoded, datatype)
            else:
                return '%s' % encoded

    def __str__(self):
        r"""
        >>> from rdflib.term import Literal
        >>> a = Literal("This \t is a test")

        The following need not be true in general as str() returns an
        'informal' string:

            >>> Literal(str(a))==a
            False

        But the following still needs to be true:

            >>> s = "%s" % a
            >>> s
            u'This \t is a test'

        We're using the unicode-escape encoding for the informal
        string:

            >>> str(a)
            'This \\t is a test'

            >>> b = Literal(u"\u00a9")
            >>> str(b)
            '\\xa9'

        """
        return self.encode("unicode-escape")

    def __repr__(self):
        return """rdflib.Literal(%s, lang=%s, datatype=%s)""" % (
                super(Literal, self).__repr__(),
                repr(self.language),
                repr(self.datatype))

    def toPython(self):
        """
        Returns an appropriate python datatype derived from this RDF Literal
        """
        convFunc = _toPythonMapping.get(self.datatype, None)

        if convFunc:
            rt = convFunc(self)
        else:
            rt = self
        return rt

    def _toCompareValue(self):
        try:
            rt = self.toPython()
        except Exception, e:
            _logger.warning("could not convert %s to a Python datatype" % repr(self))
            rt = self
                
        if rt is self:
            if self.language is None and self.datatype is None:
                return unicode(rt)
            else:
                return (unicode(rt), rt.datatype, rt.language)
        return rt

    def md5_term_hash(self):
        d = md5(str(self))
        d.update("L")
        return d.hexdigest()


class Namespace(Identifier):

    def term(self, name):
        return URIRef(self + name)

    def __getitem__(self, key, default=None):
        return self.term(key)

    def __getattr__(self, name):
        if name.startswith("__"): # ignore any special Python names!
            raise AttributeError
        else:
            return self.term(name)

_XSD_NS = Namespace(u'http://www.w3.org/2001/XMLSchema#')

#Casts a python datatype to a tuple of the lexical value and a datatype URI (or None)
def _castPythonToLiteral(obj):
    for pType,(castFunc,dType) in _PythonToXSD:
        if isinstance(obj,pType):
            if castFunc:
                return castFunc(obj),dType
            elif dType:
                return obj,dType
            else:
                return obj,None
    return obj, None # TODO: is this right for the fall through case?

# Mappings from Python types to XSD datatypes and back (burrowed from sparta)
# datetime instances are also instances of date... so we need to order these.
_PythonToXSD = [
    (basestring, (None,None)),
    (float     , (None,_XSD_NS[u'float'])),
    (int       , (None,_XSD_NS[u'integer'])),
    (long      , (None,_XSD_NS[u'long'])),
    (bool      , (None,_XSD_NS[u'boolean'])),
    (datetime  , (lambda i:i.isoformat(),_XSD_NS[u'dateTime'])),
    (date      , (lambda i:i.isoformat(),_XSD_NS[u'date'])),
    (time      , (lambda i:i.isoformat(),_XSD_NS[u'time'])),
]

def _strToTime(v) :
    return strptime(v,"%H:%M:%S")

def _strToDate(v) :
    tstr = strptime(v,"%Y-%m-%d")
    return date(tstr.tm_year,tstr.tm_mon,tstr.tm_mday)

def _strToDateTime(v) :
    """
    Attempt to cast to datetime, or just return the string (otherwise)
    """
    try:
        tstr = strptime(v,"%Y-%m-%dT%H:%M:%S")
    except:
        try:
            tstr = strptime(v,"%Y-%m-%dT%H:%M:%SZ")
        except:
            try:
                tstr = strptime(v,"%Y-%m-%dT%H:%M:%S%Z")
            except:
                return v

    return datetime(tstr.tm_year,tstr.tm_mon,tstr.tm_mday,tstr.tm_hour,tstr.tm_min,tstr.tm_sec)

XSDToPython = {
    _XSD_NS[u'time']               : _strToTime,
    _XSD_NS[u'date']               : _strToDate,
    _XSD_NS[u'dateTime']           : _strToDateTime,
    _XSD_NS[u'string']             : None,
    _XSD_NS[u'normalizedString']   : None,
    _XSD_NS[u'token']              : None,
    _XSD_NS[u'language']           : None,
    _XSD_NS[u'boolean']            : lambda i:i.lower() in ['1','true'],
    _XSD_NS[u'decimal']            : float,
    _XSD_NS[u'integer']            : long,
    _XSD_NS[u'nonPositiveInteger'] : int,
    _XSD_NS[u'long']               : long,
    _XSD_NS[u'nonNegativeInteger'] : int,
    _XSD_NS[u'negativeInteger']    : int,
    _XSD_NS[u'int']                : long,
    _XSD_NS[u'unsignedLong']       : long,
    _XSD_NS[u'positiveInteger']    : int,
    _XSD_NS[u'short']              : int,
    _XSD_NS[u'unsignedInt']        : long,
    _XSD_NS[u'byte']               : int,
    _XSD_NS[u'unsignedShort']      : int,
    _XSD_NS[u'unsignedByte']       : int,
    _XSD_NS[u'float']              : float,
    _XSD_NS[u'double']             : float,
    _XSD_NS[u'base64Binary']       : base64.decodestring,
    _XSD_NS[u'anyURI']             : None,
}

_toPythonMapping = {}
_toPythonMapping.update(XSDToPython)

def bind(datatype, conversion_function):
    """bind a datatype to a function for converting it into a Python instance."""
    if datatype in _toPythonMapping:
        _logger.warning("datatype '%s' was already bound. Rebinding." % datatype)
    _toPythonMapping[datatype] = conversion_function





class Variable(Term, unicode):
    """
    """
    __slots__ = ()
    def __new__(cls, value):
        if value[0]=='?':
            value=value[1:]
        return unicode.__new__(cls, value)

    def __repr__(self):
        return self.n3()

    def n3(self):
        return "?%s" % self

    def __reduce__(self):
        return (Variable, (unicode(self),))

    def md5_term_hash(self):
        d = md5(str(self))
        d.update("V")
        return d.hexdigest()




class Statement(Term, tuple):

    def __new__(cls, (subject, predicate, object), context):
        return tuple.__new__(cls, ((subject, predicate, object), context))

    def __reduce__(self):
        return (Statement, (self[0], self[1]))

