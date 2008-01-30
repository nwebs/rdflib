"""


"""

import os
import warnings
from urllib import pathname2url
from urllib2 import urlopen, Request
from urlparse import urljoin
from StringIO import StringIO
from xml.sax import xmlreader
from xml.sax.saxutils import prepare_input_source

from rdflib import __version__
from rdflib.namespace import Namespace
from rdflib.term import URIRef


class Parser(object):

    def __init__(self):
        pass

    def parse(self, source, sink):
        pass


class InputSource(xmlreader.InputSource):

    def content_type():
        return None
        

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
            if hasattr(source, "read") and not isinstance(source, Namespace):

                # TODO: ah... create_input_source is not always called
                # directly... so we want stacklevel of 2 or 3. So not
                # sure how we can make this useful. Also, does not
                # seem to give useful information when being called
                # from doctests.

                # warnings.warn("Use g.parse(file=my_file) instead of using source argument. ",
                #              DeprecationWarning, stacklevel=3)

                # we need to make sure it's not an instance of Namespace since
                # Namespace instances have a read attr
                input_source = prepare_input_source(source)
            else:
                location = source

    if location is not None:
        base = urljoin("file:", pathname2url(os.getcwd()))
        absolute_location = URIRef(location, base=base).defrag()
        input_source = URLInputSource(absolute_location)
        publicID = publicID or absolute_location

    if file is not None:
        input_source = prepare_input_source(file)

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
        

