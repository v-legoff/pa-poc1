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
    
    def setup(self, location=None):
        """Setup the data connector."""
        if location is None:
            raise exceptions.InsufficientConfiguration(
                    "the location for storing datas was not specified for " \
                    "the sqlite3 data connector")
        
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
        self.connection = sqlite3.connect(self.location)
