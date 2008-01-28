import warnings

from rdflib.store import Store
from rdflib.syntax import serializer, serializers
from rdflib.syntax import parsers
from rdflib import query
from rdflib.QueryResult import QueryResult

entry_points = [
    ('rdflib.plugins.store', Store),
    ('rdflib.plugins.serializer', serializers.Serializer),
    ('rdflib.plugins.parser', parsers.Parser),
    ('rdflib.plugins.query_processor', query.Processor), 
    ('rdflib.plugins.query_result', QueryResult)
    ]

_kinds = {}
_adaptors = {}

def register(name, kind, module_path, class_name):
    _module_info = _kinds.get(kind, None)
    if _module_info is None:
        _module_info = _kinds[kind] = {}
    _module_info[name] = (module_path, class_name)

def get(name, kind):
    register_from_entry_points(name, kind)
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
            #print "kind id:", id(kind)
            raise Exception("could not get plugin for %s, %s: %s" % (name, kind, e))
        def const(*args, **keywords):
            return Adaptor(Adaptee(*args, **keywords))
        return const

def register_adaptor(adaptor, adaptee):
    _adaptors[adaptor] = adaptee


_entry_point_loaded = {}
def register_from_entry_points(name=None, kind=None):
    if name is not None and kind is not None:
        if (name, kind) in _entry_point_loaded:
            return
    #print "register_from_entry_points: ", name, kind
    from pkg_resources import iter_entry_points
    for entry_point, entry_point_kind in entry_points:
        for ep in iter_entry_points(entry_point):
            #print "ep.name", ep.name
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
            #print "registering: ", ep.name, id(kind)
            register(ep.name, kind, plugcls.__module__, plugcls.__name__)

    

register_adaptor(serializer.Serializer, serializers.Serializer)


         
