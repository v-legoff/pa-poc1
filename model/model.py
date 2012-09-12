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


"""This module contains the Model class, defined below."""

from model.functions import *
from model.meta import MetaModel
from model.types import *

class Model(metaclass=MetaModel):
    
    """Abstract class for a model.
    
    Each model must inherit from it.  This class provides:
    -   Methods to create, edit, update and delete objects
    -   Methods to find and filter objects.
    
    The Model class use a DataConnector object to access datas (read and write
    it).
    
    Each column is defined in the class body.  For isntance:
    >>> class User(Model):
    ...     '''A model for an user.'''
    ...     username = String(max_size=30)
    ...     password = String(max_size=255)  # hashed password
    ...     creation_date = Datetime()
    ... 
    
    The 'get_fields' function gives a list of the defined attributes:
    >>> get_fields(User)
    ... [<field 'username'>, <field 'password'>, <field 'creation_date'>]
    
    Methods defined (which can be redefined):
        create() -- create a new object
        save() -- save the object through the data connector
        delete() -- delete the object
        find(identifier) -- get an object through its ID
        filter(...) -- retrieve one or more object
    
    """
    
    id = Integer(key=True)
    
    def __init__(self, **kwargs):
        """Create an object from keyword parameters.
        
        This method SHOULD NOT be redefined in a subclass.
        
        """
        fields = get_fields(type(self))
        fields = dict((field.field_name, field) for field in fields)
        for name, value in kwargs.items():
            setattr(self, name, value)
    
    def __repr__(self):
        return "<model {}>".format(get_name(type(self)))
