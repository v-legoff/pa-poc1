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


"""This module contains the exceptions raised when manipulating models.

Exception classes:
    ModelException
        ObjectNotFound
        UpdateDeletedObject

"""

class ModelException(RuntimeError):
    
    """Parent classes of all model exceptions."""
    
    pass

class ObjectNotFound(ModelException):
    
    """Exception raised when an object can not be found.
    
    It stores the model and primary attributes.
    
    """
    
    def __init__(self, model=None, pkey_values=None):
        self.model = model
        self.pkey_values = pkey_values if pkey_values else {}
    
    def __str__(self):
        msg = "can not find " + repr(self.model)
        if self.pkey_values:
            msg += " with "
            attrs = []
            for name, value in self.pkey_values.items():
                attrs.append(name + "=" + repr(value))
            
            msg += " and ".join(attrs)
        
        return msg

class UpdateDeletedObject(ModelException):
    
    """Exception raised when trying to update a deleted object."""
    
    def __init__(self, object):
        self.object = object
    
    def __str__(self):
        return "Try to update {} whereas it had been previously " \
                "deleted".format(self.object)
