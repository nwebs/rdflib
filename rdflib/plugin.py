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

from rdflib.store import Store
from rdflib.syntax import serializer, serializers
from rdflib.syntax import parsers
from rdflib import query

entry_points = {
    'rdflib.plugins.store': Store,
    'rdflib.plugins.serializer': serializers.Serializer,
    'rdflib.plugins.parser': parsers.Parser,
    'rdflib.plugins.query_processor': query.Processor,
    'rdflib.plugins.query_result': query.Result
    }

_kinds = {}
_adaptors = {}

def register(name, kind, module_path, class_name):
    _module_info = _kinds.get(kind, None)
    if _module_info is None:
        _module_info = _kinds[kind] = {}
    _module_info[name] = (module_path, class_name)

def get(name, kind):
    _register_from_entry_points(name, kind)
    _module_info = _kinds.get(kind)
    if _module_info and name in _module_info:
        module_path, class_name = _module_info[name]
        module = __import__(module_path, globals(), locals(), True)
        return getattr(module, class_name)
    else:
        Adaptor = kind # TODO: look up of adaptor, for now just use kind
        try:
            Adaptee = get(name, _adaptors[kind])
        except Exception, e:
            raise Exception("could not get plugin for %s, %s: %s" % (name, kind, e))
        def const(*args, **keywords):
            return Adaptor(Adaptee(*args, **keywords))
        return const

def register_adaptor(adaptor, adaptee):
    _adaptors[adaptor] = adaptee

# TODO: would be nice to get rid of the following bit of complexity,
# the adaptor bit.
register_adaptor(serializer.Serializer, serializers.Serializer) 


_entry_point_loaded = {}
def _register_from_entry_points(name=None, kind=None):
    if name is not None and kind is not None:
        if (name, kind) in _entry_point_loaded:
            return
    from pkg_resources import iter_entry_points
    for entry_point, entry_point_kind in entry_points.iteritems():
        for ep in iter_entry_points(entry_point):
            # only load if name and kind match. None matches all.
            if not (name is None or name==ep.name):
                continue
            if not (kind is None or kind==entry_point_kind):
                continue
            if (ep.name, kind) in _entry_point_loaded:
                continue

            _entry_point_loaded[(ep.name, kind)] = True
            try:
                plugcls = ep.load()
            except KeyboardInterrupt:
                raise
            except Exception, e:
                # never want a plugin load to kill the test run
                # but we can't log here because the logger is not yet
                # configured
                warnings.warn("Unable to load plugin %s: %s" % (ep, e),
                              RuntimeWarning)
                continue
            register(ep.name, kind, plugcls.__module__, plugcls.__name__)

