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


"""Package defining the data connector for sqlite3.

The data connector (subclass of DataConnector) is described in
this file.

"""

import os

from model.types import *

SQLITE_TYPES = {
    Integer: "integer",
    String: "text",
}

driver = True

try:
    import sqlite3
except ImportError:
    driver = False

from dc.connector import DataConnector
from dc import exceptions
from model.functions import *

class Sqlite3Connector(DataConnector):
    
    """Data connector for sqlite3.
    
    This data connector should read and write datas using the sqlite3
    module (part of the python standard library).
    
    """
    
    def __init__(self):
        """Check the driver presence.
        
        If not found, raise a DriverNotFound exception.
        
        """
        if not driver:
            raise exceptions.DriverNotFound(
                    "the sqlite3 library can not be found")
        
        self.location = None
        self.created_tables = ()
    
    def setup(self, location=None):
        """Setup the data connector."""
        if location is None:
            raise exceptions.InsufficientConfiguration(
                    "the location for storing datas was not specified for " \
                    "the sqlite3 data connector")
        
        location = location.replace("\\", "/")
        if location.startswith("~"):
            location = os.path.expanduser("~") + location[1:]
        
        DataConnector.__init__(self)
        self.location = location
        self.connection = sqlite3.connect(self.location)
    
    def record_tables(self, classes):
        """Record the tables."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        self.created_tables = tuple(tables)
        DataConnector.record_tables(self, classes)
        self.connection.commit()
    
    def record_model(self, model):
        """Record a single model."""
        DataConnector.record_model(self, model)
        name = get_plural_name(model)
        if name not in self.created_tables:
            self.create_table(name, model)
    
    def create_table(self, name, model):
        """Create the sqlite table related to the specified model."""
        fields = get_fields(model)
        sql_fields = []
        for field in fields:
            sql_field = SQLITE_TYPES[type(field)]
            instruction = field.field_name + " " + sql_field
            if field.pkey:
                instruction += " PRIMARY KEY"
            if field.auto_increment:
                instruction += " AUTOINCREMENT"
            sql_fields.append(instruction)
        
        query = "CREATE TABLE {} ({})".format(name, ", ".join(sql_fields))

        cursor = self.connection.cursor()
        cursor.execute(query)
    
    def loop(self):
        """Commit the database."""
        self.connection.commit()
    
    def find(self, model, pkey_values):
        """Return, if found, the specified object."""
        # First, look for the object in the cached tree
        pkey_values_list = list(pkey_values.values())
        table_name = get_name(model)
        cached_tree = self.objects_tree.get(table_name, {})
        object = cached_tree.get(*pkey_values_list)
        if object:
            return object
        
        query = "SELECT * FROM {} WHERE ".format(get_plural_name(model))
        params = []
        filters = []
        for name, value in pkey_values.items():
            filters.append("{}=?".format(name))
            params.append(value)
        
        query += " AND ".join(filters)
        cursor = self.connection.cursor()
        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
        if row is None:
            raise ValueError("not found")
        
        dict_fields = {}
        for i, field in enumerate(get_fields(model)):
            dict_fields[field.field_name] = row[i]
        
        object = model.build(**dict_fields)
        self.cache_object(object)
        return object
    
    def register_object(self, object):
        """Save the object, issued from a model."""
        name = get_name(type(object))
        fields = get_fields(type(object))
        plural_name = get_plural_name(type(object))
        query = "INSERT INTO " + plural_name + " ("
        names = []
        values = []
        auto_increments = []
        for field in fields:
            if field.auto_increment:
                auto_increments.append(field.field_name)
                continue
            
            names.append(field.field_name)
            values.append(getattr(object, field.field_name))
        
        query += ", ".join(names) + ") values("
        query += ", ".join("?" * len(values)) + ")"
        cursor = self.connection.cursor()
        cursor.execute(query, tuple(values))
        
        for field in auto_increments:
            query = "SELECT max(" + field + ") FROM " + plural_name
            cursor.execute(query)
            row = cursor.fetchone()
            value = row[0]
            setattr(object, field, value)
        
        self.cache_object(object)
    
    def get_all(self, model):
        """Return all the model's objects in a list."""
        name = get_name(model)
        plural_name = get_plural_name(model)
        fields = get_fields(model)
        objects = []
        query = "SELECT * FROM " + plural_name
        cursor = self.connection.cursor()
        cursor.execute(query)
        for row in cursor.fetchall():
            dict_fields = {}
            for i, field in enumerate(fields):
                dict_fields[field.field_name] = row[i]
            
            object = self.get_from_cache(model, dict_fields)
            if object is None:
                object = model.build(**dict_fields)
                self.cache_object(object)
            objects.append(object)
        
        return objects
    
    def update(self, object, attribute):
        """Update an object."""
        if self.was_deleted(object):
            raise ValueError("the object {} was deleted, can't update " \
                    "it".format(repr(object)))
        
        plural_name = get_plural_name(type(object))
        keys = get_pkey_names(type(object))
        params = [getattr(object, attribute)] + list(get_pkey_values(object))
        names = [name + "=?" for name in keys]
        query = "UPDATE " + plural_name + " SET " + attribute + "=?"
        query += " WHERE " + " AND ".join(names)
        cursor = self.connection.cursor()
        cursor.execute(query, tuple(params))
    
    def delete(self, object):
        """Delete the object."""
        name = get_name(type(object))
        plural_name = get_plural_name(type(object))
        keys = get_pkey_names(type(object))
        names = [name + "=?" for name in keys]
        values = tuple(get_pkey_values(object))
        query = "DELETE FROM " + plural_name
        query += " WHERE " + " AND ".join(names)
        cursor = self.connection.cursor()
        cursor.execute(query, values)
        
        # Delete from cache
        self.uncache_object(object)
