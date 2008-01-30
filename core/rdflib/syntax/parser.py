"""


"""

import os
import __builtin__
import warnings
from urllib import pathname2url
from urllib2 import urlopen, Request
from urlparse import urljoin
from StringIO import StringIO
from xml.sax import xmlreader
from xml.sax.saxutils import prepare_input_source
import types
try:
    _StringTypes = (types.StringType, types.UnicodeType)
except AttributeError:
    _StringTypes = (types.StringType,)

from rdflib import __version__
from rdflib.namespace import Namespace
from rdflib.term import URIRef


class Parser(object):

    def __init__(self):
        pass

    def parse(self, source, sink):
        pass


class InputSource(xmlreader.InputSource):

    def __init__(self, system_id = None):
        xmlreader.InputSource.__init__(self, system_id=system_id)
        self.content_type = None
        

class StringInputSource(InputSource, object):
    def __init__(self, value, system_id=None):
        super(StringInputSource, self).__init__(system_id)
        stream = StringIO(value)
        self.setByteStream(stream)
        # TODO:
        #   encoding = value.encoding
        #   self.setEncoding(encoding)


# TODO: add types for n3. text/rdf+n3 ?
headers = {
    'Accept': 'application/rdf+xml,application/xhtml+xml;q=0.5',
    'User-agent':
    'rdflib-%s (http://rdflib.net/; eikeon@eikeon.com)' % __version__
    }


class URLInputSource(InputSource, object):
    def __init__(self, system_id=None):
        super(URLInputSource, self).__init__(system_id)
        self.url = system_id
        # So that we send the headers we want to...
        req = Request(system_id, None, headers)
        
        file = urlopen(req)
        self.content_type = file.info().get('content-type')
        self.content_type = self.content_type.split(";", 1)[0]
        self.setByteStream(file)
        # TODO: self.setEncoding(encoding)

    def __repr__(self):
        return self.url

class FileInputSource(InputSource, object):
    def __init__(self, file):
        super(FileInputSource, self).__init__(`file`)
        self.file = file
        self.setByteStream(file)
        # TODO: self.setEncoding(encoding)

    def __repr__(self):
        return `self.file`


def create_input_source(source=None, publicID=None, 
                        location=None, file=None, data=None):
    """
    Return an appropriate InputSource instance for the given
    parameters.
    """

    # TODO: test that exactly one of source, location, file, and data
    # is not None.

    input_source = None

    if source is not None:
        if isinstance(source, InputSource):
            input_source = source
        else:
            if isinstance(source, _StringTypes):
                location = source
            elif hasattr(source, "read") and not isinstance(source, Namespace):
                f = source
                input_source = InputSource()
                input_source.setByteStream(f)
                if hasattr(f, "name"):
                    input_source.setSystemId(f.name)
            else:
                raise Exception("NYI")

    if location is not None:
        base = urljoin("file:", pathname2url(os.getcwd()))
        absolute_location = URIRef(location, base=base).defrag()
        if absolute_location.startswith("file:"):
            filename = os.path.join(os.getcwd(), location)
            file = __builtin__.file(filename, "rb")
        else:
            input_source = URLInputSource(absolute_location)
        publicID = publicID or absolute_location

    if file is not None:
        input_source = FileInputSource(file)

    if data is not None:
        input_source = StringInputSource(data)

    if input_source is None:
        raise Exception("could not create InputSource")
    else:
        if publicID:
            input_source.setPublicId(publicID)

        # TODO: what motivated this bit?
        id = input_source.getPublicId()
        if id is None:
            input_source.setPublicId("")
        return input_source
        

