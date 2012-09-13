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


"""Package defining the data connector for YAML.

The data connector (subclass of DataConnector) is described in
this file.

"""

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
    
    def __init__(self):
        """Check the driver presence.
        
        If not found, raise a DriverNotFound exception.
        
        """
        if not driver:
            raise exceptions.DriverNotFound(
                    "the yaml library can not be found")
        
        self.location = None
    
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
        Each dictionary is a line of data which sould describe a model
        object.
        
        """
        name = table_name
        content = file.read()
        datas = yaml.load(content)
        if not isinstance(datas, list):
            raise exceptions.DataFormattingError(
                    "the file {} must contain a YAML formatted list".format(
                    self.files[name]))
        
        class_table = self.tables[name]
        objects = []
        for line in datas:
            object = class_table(**line)
            objects.append(object)
        
        self.objects_tree[name] = objects
