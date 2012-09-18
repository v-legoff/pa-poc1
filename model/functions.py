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


"""This module contains different useful functions for manipulating models.

Functions defined here:
    get_fields(class) -- return the class's field
    get_name(class) -- return the model's name
    get_plural_name(class) -- return the plural class name
    get_pkey_names -- return a list of primary key fields name
    get_pkey_values -- return a list of primary key fields values

"""

from model.types import BaseType

def get_fields(model):
    """Return a list of the defined fields in this model."""
    fields = [getattr(model, name) for name in dir(model)]
    fields = [field for field in fields if isinstance(field, BaseType)]
    fields = sorted(fields, key=lambda field: field.nid)
    return fields

def get_name(model):
    """Return the model name."""
    name = model.__name__
    name = name.split(".")[-1]
    return name.lower()

def get_plural_name(model):
    """Return the plural model's name.
    
    The plural name is:
        The value of the 'plural_name' class attribute if exists
        The singular name extended with the 's / es' rule
    
    """
    if hasattr(model, "plural_name"):
        return model.plural_name
    else:
        singular_name = get_name(model)
        if singular_name.endswith("y"):
            singular_name = singular_name[:-1] + "ies"
        elif singular_name.endswith("s"):
            singular_name += "es"
        else:
            singular_name += "s"
        
        return singular_name

def get_pkey_names(model):
    """Return a list of field names (those defined as primary key)."""
    fields = get_fields(model)
    p_fields = [field.field_name for field in fields if field.pkey]
    return p_fields

def get_pkey_values(object):
    """Return a tuple of datas (those defined as primary key).
    
    NOTE: the 'get_fields_name' function expects a model as argument
    (a class).  This function, however, expects an object created on a
    Model class.
    
    """
    fields = get_fields(type(object))
    p_fields = [field.field_name for field in fields if field.pkey]
    p_fields = [getattr(object, field) for field in p_fields]
    return tuple(p_fields)
