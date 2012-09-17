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


"""This module contains the MetaModel metaclass."""

from model.functions import *

class MetaModel(type):
    
    """The model's metaclass.
    
    Its job is to set the field list right.  The most important things are:
    -   Check that every field inherited from another class is copied
    -   Check that the field NIDs are properly set.
    
    """
    
    def __init__(cls, name, parents, attributes):
        type.__init__(cls, name, parents, attributes)
        fields = get_fields(cls)
        clean_fields = []
        for field in fields:
            if field not in attributes.values():
                # The field is obviously defined in a parent class
                copied = field.copy()
                # We can count on the field_name attribute whic has been set
                # previously
                name = field.field_name
                setattr(cls, name, copied)
                field = copied
            else:
                name = [name for name, attr in attributes.items() if attr is \
                        field][0]
            field.field_name = name
            clean_fields.append(field)
        
        # We set the NIDs
        nids = sorted(field.nid for field in clean_fields)
        for i, nid in enumerate(nids):
            field = clean_fields[i]
            field.nid = nid
            field.model = cls
    
    def __repr__(self):
        """Return the model's name."""
        return get_name(self)
