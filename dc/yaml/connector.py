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


"""Module defining the YAMLConnector class."""

import os

driver = True

try:
    import yaml
except ImportError:
    driver = False

from dc.connector import DataConnector
from dc import exceptions
from model.functions import *

class YAMLConnector(DataConnector):
    
    """Data connector for YAML.
    
    This data connector should read and write datas in YML format, using
    the yaml library.
    
    A very short example:
        # Table: users
        - id: 1
          username: admin
          email_address: admin@python-aboard.org
    
    """
    
    name = "yaml"
    def __init__(self):
        """Check the driver presence.
        
        If not found, raise a DriverNotFound exception.
        
        """
        if not driver:
            raise exceptions.DriverNotFound(
                    "the yaml library can not be found")
        
        self.location = None
        self.auto_increments = {}
        self.to_update = set()
    
    def setup(self, location=None):
        """Setup the data connector."""
        if location is None:
            raise exceptions.InsufficientConfiguration(
                    "the location for storing datas was not specified for " \
                    "the YAML data connector")
        
        location = location.replace("\\", "/")
        if location.startswith("~"):
            location = os.path.expanduser("~") + location[1:]
        
        if location.endswith("/"):
            location = location[:-1]
        
        if not os.path.exists(location):
            # Try to create it
            os.makedirs(location)
        
        if not os.access(location, os.R_OK):
            raise exceptions.DriverInitializationError(
                    "cannot read in {}".format(location))
        if not os.access(location, os.W_OK):
            raise exceptions.DriverInitializationError(
                    "cannot write in {}".format(location))
        
        DataConnector.__init__(self)
        self.location = location
        self.files = {}
    
    def close(self):
        """Close the data connector (nothing to be done)."""
        pass
    
    def destroy(self):
        """Erase EVERY stored data."""
        for file in os.listdir(self.location):
            os.remove(self.location + "/" + file)
        self.clear_cache()
        
    def record_model(self, model):
        """Record the given model."""
        name = DataConnector.record_model(self, model)
        filename = self.location + "/" + name + ".yml"
        if os.path.exists(filename):
            with open(filename, "r") as file:
                self.read_table(name, file)
        
        self.files[name] = filename
    
    def read_table(self, table_name, file):
        """Read a whoe table contained in a file.
        
        This file is supposed to be formatted as a YAML file.  Furthermore,
        the 'yaml.load' function should return a list of dictionaries.
        
        The first dictionary describes some table informations, as
        the status of the autoincrement fields.  Each following dictionary
        is a line of data which sould describe a model object.
        
        """
        name = table_name
        content = file.read()
        datas = yaml.load(content)
        if not isinstance(datas, list):
            raise exceptions.DataFormattingError(
                    "the file {} must contain a YAML formatted list".format(
                    self.files[name]))
        
        class_table = self.tables[name]
        class_datas = datas[0]
        if not isinstance(class_datas, dict):
            raise exceptions.DataFormattingError(
                    "the table informations are not stored in a YAML " \
                    "dictionary in the file {}".format(self.files[name]))
        
        self.read_table_header(name, class_datas)
        
        objects = {}
        for line in datas[1:]:
            object = class_table.build(**line)
            pkey = get_pkey_values(object)
            if len(pkey) == 1:
                pkey = pkey[0]
            
            objects[pkey] = object
        
        self.objects_tree[name] = objects
    
    def read_table_header(self, name, datas):
        """Read the table header.
        
        This header should describe some informations concerning the
        table (as the autoincrement fields).
        
        """
        auto_increments = datas.get("auto_increments", [])
        self.auto_increments[name] = auto_increments
    
    def loop(self):
        """Write the YAML tables."""
        for table in self.to_update:
            self.write_table(table)
        
        self.to_update.clear()
    
    def write_table(self, name):
        """Write the table in a file."""
        # First, we get the header
        header = {}
        if name in self.auto_increments:
            header["auto_increments"] = self.auto_increments[name]
        
        # Next we browse the object
        objects = []
        for object in self.objects_tree[name].values():
            objects.append(object.__dict__)
        
        objects.insert(0, header)
        content = yaml.dump(objects, default_flow_style=False)
        with open(self.location + "/" + name + ".yml", "w") as file:
            file.write(content)
    
    def find(self, model, pkey_values):
        """Return, if found, the selected object.
        
        Raise a model.exceptions.ObjectNotFound if not found.
        
        """
        # Look for the object in the cached tree
        object = self.get_from_cache(model, pkey_values)
        if object:
            return object
        
        raise ValueError("not found")
    
    def register_object(self, object):
        """Save the object, issued from a model."""
        name = get_name(type(object))
        fields = get_fields(type(object))
        auto_increments = self.auto_increments.get(name, {})
        for field in fields:
            if not field.auto_increment:
                continue
            
            value = auto_increments.get(field.field_name, 1)
            setattr(object, field.field_name, value)
            auto_increments[field.field_name] = value + 1
        
        self.cache_object(object)
        self.auto_increments[name] = auto_increments
        self.to_update.add(name)
    
    def get_all(self, model):
        """Return all the model's object in a list."""
        name = get_name(model)
        return list(self.objects_tree.get(name, {}).values())
    
    def update(self, object, attribute):
        """Update an object."""
        DataConnector.update(self, object, attribute)
        name = get_name(type(object))
        self.to_update.add(name)
    
    def delete(self, object):
        """Delete the object."""
        # Delete from cache only
        DataConnector.delete(self, object)
        name = get_name(type(object))
        self.to_update.add(name)
