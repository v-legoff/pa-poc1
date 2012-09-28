# Copyright (c) 2012 LE GOFF Vincent
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


"""This file contains the DataConnector class, defined below."""

from model.functions import *

class DataConnector:
    
    """Class representing a data connector, a wrapper of a data access.
    
    The DataConnector is an abstrat class, which SHOULD NOT be
    instanciated, but inherited from the usable data connectors.
    Each data connector represents a way to access organized datas,
    as a SQL driver or alike.
    
    Method to define in the subclass:
        __init__(config) -- the constructor (only called at runtime)
        connect() -- connect (to) the data connector
        disconnect() -- close the connexion to the data connector
    
    For more informations, see the details of each method.
    
    """
    
    def __init__(self):
        """Initialize the data connector."""
        self.running = False
        self.objects_tree = {}
        self.tables = {}
        self.deleted_objects = []
    
    def destroy(self):
        """Destroy and erase EVERY stored data."""
        raise NotImplementedError
    
    def record_tables(self, classes):
        """Record the given classes.
        
        The parameter must be a list of classes. Each class must
        be a model.
        
        """
        for model in classes:
            self.record_model(model)
        
        self.running = True
    
    def record_model(self, model):
        """Record the given model, a subclass of model.Model."""
        name = get_name(model)
        self.tables[name] = model
        self.objects_tree[name] = {}
        return name
    
    def loop(self):
        """Record some datas or commit some changes if necessary."""
        pass
    
    def find(self, model, pkey_values):
        """Return, if found, the selected object.
        
        Raise a model.exceptions.ObjectNotFound if not found.
        
        """
        raise NotImplementedError
    
    def was_deleted(self, object):
        """Return whether the object was deleted (uncached)."""
        name = get_name(type(object))
        values = tuple(get_pkey_values(object))
        if len(values) == 1:
            values = values[0]
        
        return (name, values) in self.deleted_objects
    
    def get_from_cache(self, model, attributes):
        """Return, if found, the cached object.
        
        The expected parameters are:
            model -- the model (Model subclass)
            attributes -- a dictionary {name1: value1, ...}
        
        """
        name = get_name(model)
        pkey_names = get_pkey_names(model)
        cache = self.objects_tree.get(name, {})
        values = tuple(attributes.get(name) for name in pkey_names)
        if len(values) == 1:
            values = values[0]
        
        return cache.get(values)
    
    def cache_object(self, object):
        """Save the object in cache."""
        pkey = get_pkey_values(object)
        if len(pkey) == 1:
            pkey = pkey[0]
        
        self.objects_tree[get_name(type(object))][pkey] = object
    
    def uncache_object(self, object):
        """Remove the object from cache."""
        name = get_name(type(object))
        values = tuple(get_pkey_values(object))
        if len(values) == 1:
            values = values[0]
        
        cache = self.objects_tree.get(name, {})
        if values in cache.keys():
            del cache[values]
            self.deleted_objects.append((name, values))
    
    def clear_cache(self):
        """Clear the cache."""
        self.objects_tree = {}
    
    def register_object(self, object):
        """Save the object, issued from a model.
        
        Usually this method should:
        -   Save the object (in a database, for instance)
        -   Cache the object.
        
        """
        raise NotImplementedError
    
    def get_all(self, model):
        """Return all the model's object in a list."""
        raise NotImplementedError
    
    def update(self, object, attribute):
        """Update an object."""
        if self.was_deleted(object):
            raise ValueError("the object {} was deleted, can't update " \
                    "it".format(repr(object)))
    
    def delete(self, object):
        """Delete object from cache."""
        self.uncache_object(object)
