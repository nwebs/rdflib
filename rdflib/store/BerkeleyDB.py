import warnings
warnings.warn("This Store implementation is still being debugged. It is currently running out of db lockers after adding around 2k triples.")

from rdflib.store import Store, VALID_STORE, CORRUPTED_STORE, NO_STORE, UNKNOWN
from rdflib.URIRef import URIRef
from bsddb import db
from os import mkdir, rmdir, makedirs
from os.path import exists, abspath, join
from urllib import pathname2url
from threading import Thread
from time import sleep, time
import logging

SUPPORT_MULTIPLE_STORE_ENVIRON = False

_logger = logging.getLogger(__name__)


class BerkeleyDB(Store):
    """
    A transaction-capable BerkeleyDB implementation
    The major difference are:
      - a dbTxn attribute which is the transaction object used for all bsddb databases
      - All operations (put,delete,get) take the dbTxn instance
      - The actual directory used for the bsddb persistence is the name of the identifier as a subdirectory of the 'path'
      
    """
    context_aware = True
    formula_aware = True
    transaction_aware = True
    def __init__(self, configuration=None, identifier=None):
        self.__open = False
        self.__identifier = identifier and identifier or 'home'
        super(BerkeleyDB, self).__init__(configuration)
        self.configuration = configuration
        self._loads = self.node_pickler.loads
        self._dumps = self.node_pickler.dumps
        #This state is needed to handle all possible combinations of calls to tx methods (close/rollback/commit)
        self.__dbTxn = None

    def __get_identifier(self):
        return self.__identifier
    identifier = property(__get_identifier)

    def destroy(self, configuration):
        """
        Destroy the underlying bsddb persistence for this store
        """
        if SUPPORT_MULTIPLE_STORE_ENVIRON:
            fullDir = join(configuration,self.identifier)
        else:
            fullDir = configuration
        if exists(configuration):
            #From bsddb docs:
            #A DB_ENV handle that has already been used to open an environment 
            #should not be used to call the DB_ENV->remove function; a new DB_ENV handle should be created for that purpose.
            self.close()
            db.DBEnv().remove(fullDir,db.DB_FORCE)

    def open(self, path, create=True):
        if self.__open:
            return
        homeDir = path
        #NOTE: The identifeir is appended to the path as the location for the db
        #This provides proper isolation for stores which have the same path but different identifiers
        if SUPPORT_MULTIPLE_STORE_ENVIRON:
            fullDir = join(homeDir,self.identifier)
        else:
            fullDir = homeDir
        envsetflags  = db.DB_CDB_ALLDB
        envflags = db.DB_INIT_MPOOL | db.DB_INIT_LOCK | db.DB_THREAD | db.DB_INIT_TXN | db.DB_RECOVER
        if not exists(fullDir):
            if create==True:
                makedirs(fullDir)
                self.create(path)
            else:                
                return NO_STORE
        if self.__identifier is None:
            self.__identifier = URIRef(pathname2url(abspath(fullDir)))
        self.db_env = db_env = db.DBEnv()
        db_env.set_cachesize(0, 1024*1024*50) # TODO
        #db_env.set_lg_max(1024*1024)
        #db_env.set_flags(envsetflags, 1)
        db_env.open(fullDir, envflags | db.DB_CREATE,0)

        #Transaction object
        self.dbTxn = db_env.txn_begin()

        self.__open = True

        dbname = None
        dbtype = db.DB_BTREE
        dbopenflags = db.DB_THREAD

        dbmode = 0660
        dbsetflags   = 0

        # create and open the DBs
        self.__indicies = [None,] * 3
        self.__indicies_info = [None,] * 3
        for i in xrange(0, 3):
            index_name = to_key_func(i)(("s", "p", "o"), "c")
            index = db.DB(db_env)
            index.set_flags(dbsetflags)
            index.open(index_name, dbname, dbtype, dbopenflags|db.DB_CREATE, dbmode,txn=self.dbTxn)
            self.__indicies[i] = index
            self.__indicies_info[i] = (index, to_key_func(i), from_key_func(i))

        lookup = {}
        for i in xrange(0, 8):
            results = []
            for start in xrange(0, 3):
                score = 1
                len = 0
                for j in xrange(start, start+3):
                    if i & (1<<(j%3)):
                        score = score << 1
                        len += 1
                    else:
                        break
                tie_break = 2-start
                results.append(((score, tie_break), start, len))

            results.sort()
            score, start, len = results[-1]

            def get_prefix_func(start, end):
                def get_prefix(triple, context):
                    if context is None:
                        yield ""
                    else:
                        yield context
                    i = start
                    while i<end:
                        yield triple[i%3]
                        i += 1
                    yield ""
                return get_prefix

            lookup[i] = (self.__indicies[start], get_prefix_func(start, start + len), from_key_func(start), results_from_key_func(start, self._from_string))


        self.__lookup_dict = lookup

        self.__contexts = db.DB(db_env)
        self.__contexts.set_flags(dbsetflags)
        self.__contexts.open("contexts", dbname, dbtype, dbopenflags|db.DB_CREATE, dbmode,txn=self.dbTxn)

        self.__namespace = db.DB(db_env)
        self.__namespace.set_flags(dbsetflags)
        self.__namespace.open("namespace", dbname, dbtype, dbopenflags|db.DB_CREATE, dbmode,txn=self.dbTxn)

        self.__prefix = db.DB(db_env)
        self.__prefix.set_flags(dbsetflags)
        self.__prefix.open("prefix", dbname, dbtype, dbopenflags|db.DB_CREATE, dbmode,txn=self.dbTxn)

        self.__i2k = db.DB(db_env)
        self.__i2k.set_flags(dbsetflags)
        self.__i2k.open("i2k", dbname, db.DB_HASH, dbopenflags|db.DB_CREATE, dbmode,txn=self.dbTxn)

        self.__needs_sync = False
        t = Thread(target=self.__sync_run)
        t.setDaemon(True)
        t.start()
        self.__sync_thread = t
        return VALID_STORE

    def __sync_run(self):
        min_seconds, max_seconds = 10, 300
        while self.__open:
            if self.__needs_sync:
                t0 = t1 = time()
                self.__needs_sync = False
                while self.__open:
                    sleep(.1)
                    if self.__needs_sync:
                        t1 = time()
                        self.__needs_sync = False
                    if time()-t1 > min_seconds or time()-t0 > max_seconds:
                        self.__needs_sync = False
                        _logger.debug("sync")
                        self.sync()
                        break
            else:
                sleep(1)

    def sync(self):
        if self.__open:
            for i in self.__indicies:
                i.sync()
            self.__contexts.sync()
            self.__namespace.sync()
            self.__prefix.sync()
            self.__i2k.sync()
            #self.__k2i.sync()

    #Transactional interfaces
    def commit(self):
        """
        Bsddb tx objects cannot be reused after commit 
        """         
        if self.dbTxn:
            _logger.debug("commiting")
            self.dbTxn.commit(0)
            #Note a new transaction handle is created to support
            #subsequent commit calls (bsddb doesn't support multiple commits by the same
            #tx handle)
            self.dbTxn = self.db_env.txn_begin()
        else:
            _logger.warning("No transaction to commit")

    def rollback(self):
        """
        Bsddb tx objects cannot be reused after commit
        """           
        if self.dbTxn is not None:
            _logger.debug("rollingback")
            self.dbTxn.abort()
            #The dbTxn is set to None to indicate to a susequent close
            #call that a rollback is not needed
            self.dbTxn = None
        else:
            _logger.warning("No transaction to rollback")
        
    def __del__(self):
        """
        Redirects python's native garbage collection into Store.close 
        """
        self.close()    

    def close(self, commit_pending_transaction=False):
        """
        Properly handles transactions explicitely (with parameter) or by default
        """
        if not self.__open:
            return
        if self.dbTxn:
            if not commit_pending_transaction:
                self.rollback()
            else:
                self.commit()            
                self.dbTxn.abort() # abort the new transaction commit just started since we're closing.
        self.__open = False
        self.__sync_thread.join()
        for i in self.__indicies:
            i.close()
        self.__contexts.close()
        self.__namespace.close()
        self.__prefix.close()
        self.__i2k.close()
        #self.__k2i.close()      
        self.db_env.close()

    def add(self, (subject, predicate, object_), context, quoted=False):
        """\
        Add a triple to the store of triples.
        """
        assert self.__open, "The Store must be open."
        assert context!=self, "Can not add triple directly to store"
        Store.add(self, (subject, predicate, object_), context, quoted)

        _to_string = self._to_string

        s = _to_string(subject)
        p = _to_string(predicate)
        o = _to_string(object_)
        c = _to_string(context)

        cspo, cpos, cosp = self.__indicies

        value = cspo.get("%s^%s^%s^%s^" % (c, s, p, o),txn=self.dbTxn)
        if value is None:
            self.__contexts.put(c, "",self.dbTxn)

            contexts_value = cspo.get("%s^%s^%s^%s^" % ("", s, p, o),txn=self.dbTxn) or ""
            contexts = set(contexts_value.split("^"))
            contexts.add(c)
            contexts_value = "^".join(contexts)
            assert contexts_value!=None

            cspo.put("%s^%s^%s^%s^" % (c, s, p, o), "",self.dbTxn)
            cpos.put("%s^%s^%s^%s^" % (c, p, o, s), "",self.dbTxn)
            cosp.put("%s^%s^%s^%s^" % (c, o, s, p), "",self.dbTxn)
            if not quoted:
                cspo.put("%s^%s^%s^%s^" % ("", s, p, o), contexts_value,self.dbTxn)
                cpos.put("%s^%s^%s^%s^" % ("", p, o, s), contexts_value,self.dbTxn)
                cosp.put("%s^%s^%s^%s^" % ("", o, s, p), contexts_value,self.dbTxn)

            self.__needs_sync = True

    def __remove(self, (s, p, o), c, quoted=False):
        cspo, cpos, cosp = self.__indicies
        contexts_value = cspo.get("^".join(("", s, p, o, "")),txn=self.dbTxn) or ""
        contexts = set(contexts_value.split("^"))
        contexts.discard(c)
        contexts_value = "^".join(contexts)
        for i, _to_key, _from_key in self.__indicies_info:
            i.delete(_to_key((s, p, o), c),txn=self.dbTxn)
        if not quoted:
            if contexts_value:
                for i, _to_key, _from_key in self.__indicies_info:
                    i.put(_to_key((s, p, o), ""), contexts_value,self.dbTxn)
            else:
                for i, _to_key, _from_key in self.__indicies_info:
                    try:
                        i.delete(_to_key((s, p, o), ""),txn=self.dbTxn)
                    except db.DBNotFoundError, e: 
                        pass # TODO: is it okay to ignore these?

    def remove(self, (subject, predicate, object_), context):
        assert self.__open, "The Store must be open."
        Store.remove(self, (subject, predicate, object_), context)
        _to_string = self._to_string
        if context is not None:
            if context == self:
                context = None

        if subject is not None and predicate is not None and object_ is not None and context is not None:
            s = _to_string(subject)
            p = _to_string(predicate)
            o = _to_string(object_)
            c = _to_string(context)
            value = self.__indicies[0].get("%s^%s^%s^%s^" % (c, s, p, o),txn=self.dbTxn)
            if value is not None:
                self.__remove((s, p, o), c)
                self.__needs_sync = True
        else:
            cspo, cpos, cosp = self.__indicies
            index, prefix, from_key, results_from_key = self.__lookup((subject, predicate, object_), context)

            cursor = index.cursor(txn=self.dbTxn)
            try:
                current = cursor.set_range(prefix)
                needs_sync = True
            except db.DBNotFoundError:
                current = None
                needs_sync = False
            cursor.close()
            while current:
                key, value = current
                cursor = index.cursor(txn=self.dbTxn)
                try:
                    cursor.set_range(key)
                    current = cursor.next()
                except db.DBNotFoundError:
                    current = None
                cursor.close()
                if key.startswith(prefix):
                    c, s, p, o = from_key(key)
                    if context is None:
                        contexts_value = index.get(key,txn=self.dbTxn) or ""
                        contexts = set(contexts_value.split("^")) # remove triple from all non quoted contexts
                        contexts.add("") # and from the conjunctive index
                        for c in contexts:
                            for i, _to_key, _ in self.__indicies_info:
                                i.delete(_to_key((s, p, o), c),txn=self.dbTxn)
                    else:
                        self.__remove((s, p, o), c)
                else:
                    break

            if context is not None:
                if subject is None and predicate is None and object_ is None:
                    # TODO: also if context becomes empty and not just on remove((None, None, None), c)
                    try:
                        self.__contexts.delete(_to_string(context),txn=self.dbTxn)
                    except db.DBNotFoundError, e:
                        pass

            self.__needs_sync = needs_sync

    def triples(self, (subject, predicate, object_), context=None):
        """A generator over all the triples matching """
        assert self.__open, "The Store must be open."

        if context is not None:
            if context == self:
                context = None

        _from_string = self._from_string
        index, prefix, from_key, results_from_key = self.__lookup((subject, predicate, object_), context)

        cursor = index.cursor(txn=self.dbTxn)
        try:
            current = cursor.set_range(prefix)
        except db.DBNotFoundError:
            current = None
        cursor.close()
        while current:
            key, value = current
            cursor = index.cursor(txn=self.dbTxn)
            try:
                cursor.set_range(key)
                current = cursor.next()
            except db.DBNotFoundError:
                current = None
            cursor.close()
            if key and key.startswith(prefix):
                contexts_value = index.get(key,txn=self.dbTxn)
                yield results_from_key(key, subject, predicate, object_, contexts_value)
            else:
                break

    def __len__(self, context=None):
        assert self.__open, "The Store must be open."
        if context is not None:
            if context == self:
                context = None

        if context is None:
            prefix = "^"
        else:
            prefix = "%s^" % self._to_string(context)

        index = self.__indicies[0]
        cursor = index.cursor(txn=self.dbTxn)
        current = cursor.set_range(prefix)
        count = 0
        while current:
            key, value = current
            if key.startswith(prefix):
                count +=1
                current = cursor.next()
            else:
                break
        cursor.close()
        return count

    def bind(self, prefix, namespace):
        prefix = prefix.encode("utf-8")
        namespace = namespace.encode("utf-8")
        bound_prefix = self.__prefix.get(namespace,txn=self.dbTxn)
        if bound_prefix:
            self.__namespace.delete(bound_prefix,txn=self.dbTxn)
        self.__prefix.put(namespace, prefix,self.dbTxn)
        #self.__prefix[namespace] = prefix
        self.__namespace.put(prefix, namespace,self.dbTxn)
        #self.__namespace[prefix] = namespace

    def namespace(self, prefix):
        prefix = prefix.encode("utf-8")
        return self.__namespace.get(prefix, None,txn=self.dbTxn)

    def prefix(self, namespace):
        namespace = namespace.encode("utf-8")
        return self.__prefix.get(namespace, None,txn=self.dbTxn)

    def namespaces(self):
        cursor = self.__namespace.cursor(txn=self.dbTxn)
        results = []
        current = cursor.first()
        while current:
            prefix, namespace = current
            results.append((prefix, namespace))
            current = cursor.next()
        cursor.close()
        for prefix, namespace in results:
            yield prefix, URIRef(namespace)

    def contexts(self, triple=None):
        _from_string = self._from_string
        _to_string = self._to_string

        if triple:
            s, p, o = triple
            s = _to_string(s)
            p = _to_string(p)
            o = _to_string(o)
            contexts = self.__indicies[0].get("%s^%s^%s^%s^" % ("", s, p, o),txn=self.dbTxn)
            if contexts:
                for c in contexts.split("^"):
                    if c:
                        yield _from_string(c)
        else:
            index = self.__contexts
            cursor = index.cursor(txn=self.dbTxn)
            current = cursor.first()
            cursor.close()
            while current:
                key, value = current
                context = _from_string(key)
                yield context
                cursor = index.cursor(txn=self.dbTxn)
                try:
                    cursor.set_range(key)
                    current = cursor.next()
                except db.DBNotFoundError:
                    current = None
                cursor.close()

    def _from_string(self, i):
        k = self.__i2k.get(i,txn=self.dbTxn)
        return self._loads(k)

    def _to_string(self, term):
        """
        i2k:  hashString -> pickledTerm
        
        i2k basically stores the reverse lookup of the MD5 hash of the term 
        
        """
        assert term is not None
        # depending on what the space time trade off looks like we
        # might still want to record k2i as well. Also recording would
        # protect against hash algo changing.
        i = term.md5_term_hash()
        k = self.__i2k.get(i, txn=self.dbTxn)
        if k is None:
            self.__i2k.put(i,self._dumps(term),txn=self.dbTxn)
        return i

    def __lookup(self, (subject, predicate, object_), context):
        _to_string = self._to_string
        if context is not None:
            context = _to_string(context)
        i = 0
        if subject is not None:
            i += 1
            subject = _to_string(subject)
        if predicate is not None:
            i += 2
            predicate = _to_string(predicate)
        if object_ is not None:
            i += 4
            object_ = _to_string(object_)
        index, prefix_func, from_key, results_from_key = self.__lookup_dict[i]
        prefix = "^".join(prefix_func((subject, predicate, object_), context))
        return index, prefix, from_key, results_from_key


def to_key_func(i):
    def to_key(triple, context):
        "Takes a string; returns key"
        return "^".join((context, triple[i%3], triple[(i+1)%3], triple[(i+2)%3], "")) # "" to tac on the trailing ^
    return to_key

def from_key_func(i):
    def from_key(key):
        "Takes a key; returns string"
        parts = key.split("^")
        return parts[0], parts[(3-i+0)%3+1], parts[(3-i+1)%3+1], parts[(3-i+2)%3+1]
    return from_key

def results_from_key_func(i, from_string):
    def from_key(key, subject, predicate, object_, contexts_value):
        "Takes a key and subject, predicate, object; returns tuple for yield"
        parts = key.split("^")
        if subject is None:
            # TODO: i & 1: # dis assemble and/or measure to see which is faster
            # subject is None or i & 1
            s = from_string(parts[(3-i+0)%3+1])
        else:
            s = subject
        if predicate is None:#i & 2:
            p = from_string(parts[(3-i+1)%3+1])
        else:
            p = predicate
        if object_ is None:#i & 4:
            o = from_string(parts[(3-i+2)%3+1])
        else:
            o = object_
        return (s, p, o), (from_string(c) for c in contexts_value.split("^") if c)
    return from_key

def readable_index(i):
    s, p, o = "?" * 3
    if i & 1: s = "s"
    if i & 2: p = "p"
    if i & 4: o = "o"
    return "%s,%s,%s" % (s, p, o)
