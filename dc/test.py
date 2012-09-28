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


"""This module contains a generic class for testing data connectors.

Note that this class DOES NOT inherit from unittest.TestCase, being
an abstract test.  If you create a new data connector and would like
to test it, simply create a test.py file in your data connector package
and create a class inherited from AbstractDCTest.
Your test.py file should contains something like:
# Dont' forget the license and at least a line of documentation

from unittest import TestCase

from dc.test import AbstractDCTest

class DCTest(AbstractDCTest, TestCase):
    
    name = "dc_name"

"""

import os
import yaml

from model import Model
from model.test import *

class AbstractDCTest:
    
    """Abstract class for testing data connectors.
    
    This class is abstract.  It shouldn't be considered a regular
    test case and doesn't have enough information to perform a test.
    It's a base test for a data connector (each data connector should
    have a class inherited from it).  This allows to test different
    data connector to check that each one has the same basic abilities
    as any other.
    
    Testing methods (some could be added, NOT MODIFIED):
        test_create -- try to create an object from a model
        test_update -- try to update an object
        test_save -- try to save and retrieve stored datas
        test_delete -- try to delete an object
        test_primary_keys -- test that the primary keys are unique
        test_auto_increment -- test the behavior of an autoincrement field
        test_find -- try to a retrieve a single object
        test_get_all -- try to retrieve all the created objects
    
    Other methods:
        setUp -- set up the test case
        tearDown -- tear down the test case
    
    """
    
    def setUp(self):
        """Set up the driver."""
        self.setup_driver()
    
    def tearDown(self):
        """Destroy the data connector and tear it down."""
        dc = self.dc
        self.teardown_driver()
        dc.destroy()
    
    def setup_driver(self):
        """Setup the driver.
        
        If available, read the configuration file found in
        test/dc/{driver_name}.yml.  Otherwise, the file is created with
        the default configuration found in dc/{driver_name}/parameters.yml.
        
        """
        cfg_dir = "test/dc"
        cfg_path = cfg_dir + "/" + self.name + ".yml"
        def_cfg_path = "dc/" + self.name + "/parameters.yml"
        if not os.path.exists(cfg_path):
            if not os.path.exists(cfg_dir):
                os.makedirs(cfg_dir)
            
            with open(def_cfg_path, "r") as cfg_file:
                cfg_content = cfg_file.read()
            
            with open(cfg_path, "w") as cfg_file:
                cfg_file.write(cfg_content)
        else:
            with open(cfg_path, "r") as cfg_file:
                cfg_content = cfg_file.read()
        
        cfg_dict = yaml.load(cfg_content)
        self.dc = type(self).connector()
        self.dc.setup(**cfg_dict)
        self.dc.record_tables(models)
        Model.data_connector = self.dc
    
    def teardown_driver(self):
        """Tear down the data connector."""
        self.dc.loop()
        self.dc = None
        Model.data_connector = None
    
    def test_create(self):
        """Create a simple user."""
        user = User(username="Kredh")
        self.assertEqual(user.username, "Kredh")
    
    def test_update(self):
        """Create and update a simple user."""
        user = User(username="Nitrate")
        user.username = "Erwyn"
        self.assertEqual(user.username, "Erwyn")
    
    def test_save(self):
        """Create a simple user and start a new data connector.
        
        This tests that the created datas are stored and can be retrieved
        exactly as they were stored.
        
        """
        user = User(username="Percyst")
        uid = user.id
        username = user.username
        users = User.get_all()
        self.teardown_driver()
        self.setup_driver()
        retrieved = User.find(uid)
        self.assertEqual(retrieved.id, uid)
        self.assertEqual(retrieved.username, username)
        self.assertIsNot(retrieved, user)        
        self.assertEqual(len(User.get_all()), len(users))
    
    def test_delete(self):
        """Create and delete an user.
        
        After the user was deleted, try to update it (which souldn't
        work).
        
        NOTE: the exception raised by now when a deleted object is
        updated is ValuError, which is not appropriate.  Update the
        test when necessary.
        
        """
        user = User(username="Noway")
        user.delete()
        self.assertRaises(ValueError, setattr, user, "username", "no")
    
    def test_primary_keys(self):
        """Test that no created user has the same ID as another."""
        users = User.get_all()
        uids = set()
        for user in users:
            uids.add(user.id)
        
        self.assertEqual(len(uids), len(users))
    
    def test_auto_increment(self):
        """Test the bood behavior of a autoincrement field.
        
        First, we get the user with the highest id.  When we create
        another user, its id should be greater than the previous one.
        This should still be true when we start a new data connection.
        
        """
        # Create at least one u ser (otherwise max will go crazy)
        at_least_one_user = User(username="Atlist")
        
        # Get the user with the biggest id
        max_user = max(User.get_all(), key=lambda user: user.id)
        new_user = User(username="Ideafix")
        self.assertTrue(max_user.id < new_user.id)
        
        # Reset the data connection
        self.teardown_driver()
        self.setup_driver()
        still_new_user = User(username="Overall")
        self.assertTrue(new_user.id < still_new_user.id)
    
    def test_find(self):
        """Create and try to find the created user."""
        user = User(username="Martha")
        
        # Test the find method with a positional argument
        found_1 = User.find(user.id)
        self.assertIs(user, found_1)
        
        # Test the find method with keyword arguments
        found_2 = User.find(id=user.id)
        self.assertIs(found_1, found_2)
    
    def test_get_all(self):
        """Create an user and look for it in the User.get_all()."""
        user = User(username="Crowd")
        users = User.get_all()
        self.assertIn(user, users)
