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


"""Module defining the MongoConnector class."""

import os

driver = True

try:
    import pymongo
except ImportError:
    driver = False

from dc.connector import DataConnector
from dc import exceptions
from model.functions import *

class MongoDBConnector(DataConnector):
    
    """Data connector for MongoDB.
    
    This data connector accesses and stores datas through the pymongo
    library.  It needs a mongoDB server running on the same host.
    
    The stored datas in MongoDB are documents.  A document is free-schema
    (that is, it doesn't need a standard schema like ANY user HAS one
    username (string), one password (string), and so forth.  However,
    as Python Aboard uses schemas to define models, every document in a
    collection should contain the same types of information.
    
    """
    
    name = "mongo"
    def __init__(self):
        """Check the driver presence.
        
        If not found, raise a DriverNotFound exception.
        
        """
        if not driver:
            raise exceptions.DriverNotFound(
                    "the pymongo library can not be found")
        
        DataConnector.__init__(self)
        self.db_name = "datas"
        self.inc_name = "increments"
    
    def setup(self, datas=None, increments=None):
        """Setup the data connector."""
        datas = datas if datas else self.db_name
        increments = increments if increments else self.inc_name
        self.db_name = datas
        self.inc_name = increments
        
        # Try to connect
        self.connection = pymongo.Connection()
        
        # Create the datas and increments collections
        self.datas = self.connection[datas]
        self.increments = self.connection[increments]
        
        # Set the collections
        self.collections = {}
        self.inc_collections = {}
        
        # Keep the IDs in cache
        self.object_ids = {}
    
    def close(self):
        """Close the data connector."""
        self.connection.close()
    
    def clear(self):
        """Clear the stored datas."""
        for name in self.models.keys():
            self.datas[name].remove()
            self.datas.drop_collection(name)
            self.increments[name].remove({})
            self.increments.drop_collection(name)
        DataConnector.clear(self)
    
    def destroy(self):
        """Erase EVERY stored data."""
        self.connection.drop_database(self.db_name)
        self.connection.drop_database(self.inc_name)
        self.connection.close()
        self.clear_cache()
    
    def record_model(self, model):
        """Record the given model."""
        DataConnector.record_model(self, model)
        name = DataConnector.record_model(self, model)
        self.collections[name] = self.datas[name]
        self.inc_collections[name] = self.increments[name]
        self.object_ids[name] = {}
    
    def get_and_update_increment(self, table, field):
        """Get and update an auto-increment field.
        
        If not found in the specified table, return 1 but update to 2.
        
        """
        value = self.increments[table].find_one({
                "name": field})
        if value:
            value = value["current"]
        else:
            value = 1
        
        self.increments[table].remove({"name": field})
        self.increments[table].insert({
                "name": field,
                "current": value + 1,
        })
        
        return value
    
    def get_all_objects(self, model):
        """Return all the model's object in a list."""
        name = get_name(model)
        datas = self.datas[name].find()
        objects = []
        for data in datas:
            m_id = data["_id"]
            del data["_id"]
            object = self.get_from_cache(model, data)
            if object is None:
                object = model()
                update(object, data)
                self.cache_object(object)
                self.object_ids[name][object] = m_id
            
            objects.append(object)
        
        return objects
    
    def find_object(self, model, pkey_values):
        """Return, if found, the selected object.
        
        Raise a model.exceptions.ObjectNotFound if not found.
        
        """
        # Look for the object in the cached tree
        name = get_name(model)
        object = self.get_from_cache(model, pkey_values)
        if object:
            return object
        
        # Look for the object in the datas
        datas = self.datas[name].find_one(pkey_values)
        if datas:
            m_id = datas["_id"]
            del datas["_id"]
            object = model()
            update(object, datas)
            self.cache_object(object)
            self.object_ids[name][object] = m_id
            return object
        
        raise ValueError("not found")
    
    def add_object(self, mod_object):
        """Save the object, issued from a model."""
        name = get_name(type(mod_object))
        fields = get_fields(type(mod_object))
        for field in fields:
            if not field.auto_increment:
                continue
            
            value = self.get_and_update_increment(name, field.field_name)
            update_attr(mod_object, field.field_name, value)
        
        m_id = self.datas[name].insert(mod_object.__dict__)
        self.cache_object(mod_object)
        self.object_ids[name][mod_object] = m_id
    
    def update_object(self, object, attribute):
        """Update an object."""
        self.check_update(object)
        name = get_name(type(object))
        m_id = self.object_ids[name][object]
        f_update = dict(object.__dict__)
        f_update["_id"] = m_id
        self.datas[name].update({"_id": m_id}, f_update)
    
    def remove_object(self, object):
        """Delete the object."""
        # Delete from cache
        self.uncache_object(object)
        name = get_name(type(object))
        m_id = self.object_ids[name][object]
        self.datas[name].remove(m_id, safe=True)
        del self.object_ids[name][object]
