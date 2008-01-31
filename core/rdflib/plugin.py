"""
Plugin support for rdflib.

There are a number of plugin points for rdflib: parser, serializer,
store, query processor, and query result. Plugins can be registered
either through setuptools entry_points or by calling
rdflib.plugin.register directly.

If you have a package that uses a setuptools based setup.py you can add the following to your setup:

    entry_points = {        
        'rdflib.plugins.parser': [
            'nt =     rdflib.syntax.parsers.NTParser:NTParser',
            ],
        'rdflib.plugins.serializer': [
            'nt =     rdflib.syntax.serializers.NTSerializer:NTSerializer',
            ],
        }

For more information see:

  http://peak.telecommunity.com/DevCenter/setuptools#dynamic-discovery-of-services-and-plugins

"""

import warnings

from pkg_resources import iter_entry_points

from rdflib.store import Store
from rdflib.syntax import serializer
from rdflib.syntax import parser
from rdflib import query
from rdflib.exceptions import Error

entry_points = {
    'rdflib.plugins.store': Store,
    'rdflib.plugins.serializer': serializer.Serializer,
    'rdflib.plugins.parser': parser.Parser,
    'rdflib.plugins.query_processor': query.Processor,
    'rdflib.plugins.query_result': query.Result
    }

_plugins = dict()


class PluginException(Error):
    pass


class Plugin(object):

    def __init__(self, module_path, class_name):
        self.module_path = module_path
        self.class_name = class_name
        self._class = None

    def getClass(self):
        if self._class is None:
            module = __import__(self.module_path, globals(), locals(), True)
            self._class = getattr(module, self.class_name)
        return self._class


class PKGPlugin(Plugin):

    def __init__(self, ep):
        self.ep = ep
        self._class = None

    def getClass(self):
        if self._class is None:
            self._class = self.ep.load()
        return self._class


def register(name, kind, module_path, class_name):
    """
    Register the plugin for (name, kind). The module_path and
    class_name should be the path to a plugin class.
    """
    p = Plugin(name, kind, module_path, class_name)
    _plugins[(name, kind)] = p


def get(name, kind):
    """
    Return the class for the specified (name, kind). Raises a
    PluginException if unable to do so.
    """
    try:
        p = _plugins[(name, kind)]
    except KeyError, e:
        raise PluginException("No plugin registered for (%s, %s)" % (name, kind))        
    return p.getClass()


# add the plugins specified via pkg_resources' EntryPoints.
for entry_point, kind in entry_points.iteritems():
    for ep in iter_entry_points(entry_point):
        _plugins[(ep.name, kind)] = PKGPlugin(ep)


# TODO: plugins currently don't know there name and kind.
#
# def plugins(name=None, kind=None):
#     """
#     A generator of the plugins.
#     """
#     for p in _plugins.values():
#         if (name is None or name==p.name) and (kind is None or kind==p.kind):
#             yield p
