#!/usr/bin/env python
#
# $Revision: 1.4 $
# $Date: 2005/09/26 20:25:13 $
# $Author: dwelch $
#
# (c) Copyright 2003-2005 Hewlett-Packard Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#

# Std Lib
import sys, os.path

#from pprint import pprint

# Local
from base.g import *
from base.codes import *
from base import device, utils, status, pml
from base.kirbybase import KirbyBase

# **************************************************************************** #

class FaxAddressBook(KirbyBase):
    def __init__(self):
        KirbyBase.__init__(self)
        self._fab = os.path.expanduser( '~/.hplip.fab' ) # Table name (filename)

        if not os.path.exists(self._fab):
            log.debug("Creating new fax address book: %s" % self._fab)
            self.create()


    def create(self):
        return KirbyBase.create(self, self._fab,
            ['name:str',
             'title:str',
             'firstname:str',
             'lastname:str',
             'fax:str',
             'groups:str', # comma sep list of group names
             'notes:str'])


    def filename(self):
        return self._fab


    def insert(self, values):
        return KirbyBase.insert(self, self._fab, values)


    def insertBatch(self, batchRecords):
        return KirbyBase.insertBatch(self, self._fab, batchRecords)


    def update(self, fields, searchData, updates, filter=None, useRegExp=False):
        return KirbyBase.update(self, self._fab, fields, searchData, updates, filter, useRegExp)


    def delete(self, fields, searchData, useRegExp=False):
        return KirbyBase.delete(self, self._fab, fields, searchData, useRegExp)


    def select(self, fields, searchData, filter=None, useRegExp=False, sortFields=[],
        sortDesc=[], returnType='list', rptSettings=[0,False]):
        return KirbyBase.select(self, self._fab, fields, searchData, filter,
            useRegExp, sortFields, sortDesc, returnType, rptSettings)


    def pack(self):
        return KirbyBase.pack(self, self._fab)


    def validate(self):
        return KirbyBase.validate(self, self._fab)


    def drop(self):
        return KirbyBase.drop(self, self._fab)


    def getFieldNames(self):
        return KirbyBase.getFieldNames(self, self._fab)


    def getFieldTypes(self):
        return KirbyBase.getFieldTypes(self, self._fab)


    def len(self):
        return KirbyBase.len(self, self._fab)


    def GetEntryByRecno(self, recno):
        return AddressBookEntry(self.select(['recno'], [recno])[0])


    def AllRecords(self):
        return self.select(['recno'], ['*'])


    def AllRecordEntries(self):
        return [ AddressBookEntry(rec) for rec in self.select(['recno'], ['*'])]


    def GroupEntries(self, group):
        return [abe.name for abe in self.AllRecordEntries() if group in abe.group_list]


    def AllGroups(self):
        temp = {}
        for abe in self.AllRecordEntries():
            for g in abe.group_list:
                temp.setdefault(g)

        return temp.keys()


    def UpdateGroupEntries(self, group_name, member_entries):
        for entry in self.AllRecordEntries():

            if entry.name in member_entries: # membership indicated

                if not group_name in entry.group_list: # entry already member of group
                    # add it
                    entry.group_list.append( group_name )
                    self.update(['recno'], [entry.recno], [','.join( entry.group_list)], ['groups'])
            else:

                if group_name in entry.group_list: # remove from entry
                    entry.group_list.remove( group_name )
                    self.update(['recno'], [entry.recno], [','.join( entry.group_list)], ['groups'])


    def DeleteGroup(self, group_name):
        for entry in self.AllRecordEntries():
            if group_name in entry.group_list:
                entry.group_list.remove(group_name)
                self.update(['recno'], [entry.recno], [','.join( entry.group_list)], ['groups'])


# **************************************************************************** #

class AddressBookEntry( object ):
    def __init__( self, rec=None ):
        if rec is not None:
            rec = [ x or '' for x in rec ]
            self.recno, self.name, \
            self.title, self.firstname, self.lastname, \
            self.fax, self.groups, self.notes = rec
            self.group_list = []

            if len( self.groups ):
                for g in self.groups.split( ',' ):
                    self.group_list.append( g.strip() )

    def __str__( self ):
        return "Recno=%d, Name=%s, Title=%s, First=%s, Last=%s, Fax=%s, Groups=%s, Notes=%s\n" % \
            ( self.recno, self.name, self.title, self.firstname,
              self.lastname, self.fax, self.group_list, self.notes )


# **************************************************************************** #

class FaxDevice(device.Device):

    def __init__(self, device_uri=None, printer_name=None,
                 hpssd_sock=None, callback=None,
                 cups_printers=[]):

        device.Device.__init__(self, device_uri, printer_name,
                               hpssd_sock, callback, cups_printers)


    def setPhoneNum(self, num):
        return self.setPML(pml.OID_FAX_LOCAL_PHONE_NUM, str(num))

    def getPhoneNum(self):
        return utils.printable(self.getPML(pml.OID_FAX_LOCAL_PHONE_NUM)[0])

    phone_num = property(getPhoneNum, setPhoneNum, doc="OID_FAX_LOCAL_PHONE_NUM")


    def setStationName(self, name):
        return self.setPML(pml.OID_FAX_STATION_NAME, str(name))

    def getStationName(self):
        return utils.printable(self.getPML(pml.OID_FAX_STATION_NAME)[0])

    station_name = property(getStationName, setStationName, doc="OID_FAX_STATION_NAME")


    def sendFax(self):
        pass





