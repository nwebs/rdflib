from rdflib import Literal, ConjunctiveGraph, Namespace, BNode, URIRef, Literal, plugin
from rdflib.store import Store, VALID_STORE, CORRUPTED_STORE, NO_STORE, UNKNOWN
from rdflib.Graph import Graph, ConjunctiveGraph
from rdflib.store.FOPLRelationalModel.QuadSlot import *

def test_dType_encoding():
    correct=normalizeValue('http://www.w3.org/2001/XMLSchema#integer', 'U')
    wrong=normalizeValue('http://www.w3.org/2001/XMLSchema#integer', 'L')

    
    store = plugin.get('MySQL',Store)()
    store.open('user=..,password=..,db=test,host=..',create=False)
    Graph(store).add((BNode(),URIRef('foo'),Literal(1)))
    db=store._db
    cursor=db.cursor()
    cursor.execute(
    "select * from %s where data_type = '%s'"%
        (store.literalProperties,
         wrong))
    assert not cursor.fetchone(),"Datatype encoding bug!"
    for suffix,(relations_only,tables) in store.viewCreationDict.items():
        query='create view %s%s as %s'%(store._internedId,
                                        suffix,
        ' union all '.join([t.viewUnionSelectExpression(relations_only) 
                            for t in tables]))
        print "## Creating View ##\n",query
    
    store.rollback()    
    store.close()

if __name__ == '__main__':
    test_dType_encoding()

