"""
KirbyBase v1.8.1 (applied patch introduced in v1.8.2)

Contains classes for a plain-text, client-server dbms.

NOTE: This copy has been modified from the standard distribution of KirbyBase. 
To get the complete distribution of KirbyBase, please visit: 
http://www.netpromi.com/kirbybase.html

Classes:
    KirbyBase - database class
    KBError - exceptions

Example:
    from db import *

    db = KirbyBase()
    db.create('plane.tbl', ['name:str', 'country:str', 'speed:int',
     'range:int'])
    db.insert('plane.tbl', ['P-51', 'USA', 403, 1201])
    db.insert('plane.tbl', ['P-38', 'USA', 377, 999])
    db.select('plane.tbl', ['country', 'speed'], ['USA', '>400'])
    db.update('plane.tbl', ['country'], ['USA'], ['United States'],
     ['country'])
    db.delete('plane.tbl', ['speed'], ['<400'])
    db.close()

Author:
    Jamey Cribbs -- jcribbs@twmi.rr.com
    www.netpromi.com

License:
    KirbyBase is licensed under the Python Software Foundation License.
    KirbyBase carries no warranty!  Use at your own risk. 
"""
import re
import socket
import os.path
import datetime
import cPickle
import cStringIO
import operator


#--------------------------------------------------------------------------
# KirbyBase Class
#--------------------------------------------------------------------------
class KirbyBase:
    """Database Management System.

    Public Methods:
        __init__      - Create an instance of database.
        close         - Close database.
        create        - Create a table.
        insert        - Insert a record into a table.
        insertBatch   - Insert a list of records into a table.
        update        - Update a table.
        delete        - Delete record(s) from a table.
        select        - select record(s) from a table.
        pack          - remove deleted records from a table.
        validate      - validate data in table records.
        drop          - Remove a table.
        getFieldNames - Get a list of a table's field names.
        getFieldTypes - Get a list of a table's field types.
        len           - Total number of records in table.
    """

    #----------------------------------------------------------------------
    # PUBLIC METHODS
    #----------------------------------------------------------------------

    #----------------------------------------------------------------------
    # init
    #----------------------------------------------------------------------
    def __init__(self):
        """Create an instance of the database and return a reference to it.
        """
        self.connect_type = type

        # Regular expression used to determine if field needs to be
        # encoded.
        self.encodeRegExp = re.compile(r'\n|\r|\032|\|')

        # Regular expression used to determine if field needs to be
        # un-encoded.
        self.unencodeRegExp = re.compile(
         r'&linefeed;|&carriage_return;|&substitute;|&pipe;')

        # This will be used to validate the select statements.
        self.cmpFuncs = {"<":operator.lt, "<=":operator.le, 
         ">=":operator.ge, ">":operator.gt, "==":operator.eq,
         "!=":operator.ne, "<>":operator.ne}

        # This will be used to validate and convert the field types in
        # the header rec of the table into valid python types.
        self.strToTypes = {'int':int, 'Integer':int, 'float':float, 
         'Float':float, 'datetime.date':datetime.date, 
         'Date':datetime.date, 'datetime.datetime':datetime.datetime,
         'DateTime':datetime.datetime, 'bool':bool, 'Boolean':bool,
         'str':str, 'String':str}

    #----------------------------------------------------------------------
    # close
    #----------------------------------------------------------------------
    def close(self):
        """Close connection to database server.
        """
        pass

    #----------------------------------------------------------------------
    # create
    #----------------------------------------------------------------------
    def create(self, name, fields):
        """Create a new table and return True on success.

        Arguments:
            name   - physical filename, including path, that will hold
                     table.
            fields - list holding strings made up of multiple fieldname,
                     fieldtype pairs (i.e. ['plane:str','speed:int']).
                     Valid fieldtypes are: str, int, float, datetime.date,
                     datetime.datetime, bool or, for compatibility with 
                     the Ruby version of KirbyBase use String, Integer,
                     Float, Date, DateTime, and Boolean.

        Returns True if no exceptions are raised.
        """
        # Check to see if file already exists.
        if os.path.exists(name):
            raise KBError(name + ' already exists!')

        # Validate field types. Integer, String, Float, Date, DateTime, and
        # Boolean types are compatible between the Ruby and Python versions
        # of KirbyBase.
        for x in [y.split(':')[1] for y in fields]:
            if x not in self.strToTypes:
                raise KBError('Invalid field type: %s' % x)

        # Make copy of fields list so that value passed in is not changed.
        # Add recno counter, delete counter, and recno field definition at
        # beginning.
        header_rec = list(['000000','000000','recno:int'] + fields)

        # Open the table in write mode since we are creating it new, write
        # the header record to it and close it.
        fptr = self._openTable(name, 'w')
        fptr.write('|'.join(header_rec) + '\n')
        self._closeTable(fptr)

        # Return success.
        return True

    #----------------------------------------------------------------------
    # insert
    #----------------------------------------------------------------------
    def insert(self, name, values):
        """Insert a new record into table, return unique record number.

        Arguments:
            name   - physical file name, including path, that holds table.
            values - list, dictionary, or object containing field values
                     of new record.

        Returns unique record number assigned to new record when it is
        created.
        """

        # Open the table.
        fptr = self._openTable(name, 'r+')

        # Update the instance variables holding table header info
        self._updateHeaderVars(fptr)

        # If values is a dictionary or an object, we are going to convert
        # it into a list.  That way, we can use the same validation and 
        # updating routines regardless of whether the user passed in a 
        # dictionary, an object, or a list.  This returns a copy of 
        # values so that we are not messing with the original values.
        record = self._convertInput(values)

        # Check input fields to make sure they are valid.
        self._validateUpdateCriteria(record, self.field_names[1:])

        try:
            # Get a new record number.
            rec_no = self._incrRecnoCounter(fptr)

            # Add record number to front of record.
            record.insert(0, rec_no)

            # Append the new record to the end of the table and close the
            # table.  Run each field through encoder to take care of 
            # special characters.
            self._writeRecord(fptr, 'end', '|'.join(map(self._encodeString,
             [str(item) for item in record])))
        finally:
            self._closeTable(fptr)

        # Return the unique record number created for this new record.
        return rec_no

    #----------------------------------------------------------------------
    # insertBatch
    #----------------------------------------------------------------------
    def insertBatch(self, name, batchRecords):
        """Insert a batch of records into table, return a list of rec #s.

        Arguments:
            name         - physical file name, including path, that holds 
                           table.
            batchRecords - list of records.  Each record can be a list, a 
                           dictionary, or an object containing field values
                           of new record.

        Returns list of unique record numbers assigned.
        """
        # Open the table, update the instance variables holding table
        # header info and close table.
        fptr = self._openTable(name, 'r')
        self._updateHeaderVars(fptr)
        self._closeTable(fptr)

        # Create an empty list to hold the batch after it has been
        # validated and any records within it that are in dictionary format
        # have been converted to list format.
        records = []

        for values in batchRecords:
            # If values is a dictionary or an object, we are going to 
            # convert it into a list.  That way, we can use the same 
            # validation and updating routines regardless of whether the
            # user passed in a dictionary, an object, or a list.  This 
            # returns a copy of values so that we are not messing with the
            # original values.
            record = self._convertInput(values)
            # Check input fields to make sure they are valid.
            self._validateUpdateCriteria(record, self.field_names[1:])

            # Add the validated (and possibly converted) record to the
            # records list.
            records.append(record)

        # Create empty list to hold new record numbers.
        rec_nos = []

        # Open the table again, this time in read-write mode.
        fptr = self._openTable(name, 'r+')

        try:
            # Now that the batch has been validated, add it to the database
            # table.
            for record in records:
                # Get a new record number.
                rec_no = self._incrRecnoCounter(fptr)

                # Add record number to front of record.
                record.insert(0, rec_no)

                # Append the new record to the end of the table.  Run each 
                # field through encoder to take care of special characters.
                self._writeRecord(fptr, 'end', '|'.join(
                 map(self._encodeString, [str(item) for item in record])))

                # Add the newly create record number to the list of that we
                # we return back to the user.
                rec_nos.append(rec_no)
        finally:
            self._closeTable(fptr)

        # Return the unique record number created for this new record.
        return rec_nos

    #----------------------------------------------------------------------
    # update
    #----------------------------------------------------------------------
    def update(self, name, fields, searchData, updates, filter=None, 
     useRegExp=False):
        """Update record(s) in table, return number of records updated.

        Arguments:
            name       - physical file name, including path, that holds
                         table.
            fields     - list containing names of fields to search on. If 
                         any of the items in this list is 'recno', then the
                         table will be searched by the recno field only and
                         will update, at most, one record, since recno is 
                         the system generated primary key.
            searchData - list containing actual data to search on.  Each 
                         item in list corresponds to item in the 'fields' 
                         list.
            updates    - list, dictionary, or object containing actual data
                         to put into table field.  If it is a list and 
                         'filter' list is empty or equal to None, then 
                         updates list must have a value for each field in
                         table record.
            filter     - only used if 'updates' is a list.  This is a
                         list containing names of fields to update.  Each
                         item in list corresponds to item in the 'updates'
                         list.  If 'filter' list is empty or equal to None,
                         and 'updates' is a list, then 'updates' list must 
                         have an item for each field in table record, 
                         excepting the recno field.
            useRegExp  - if true, match string fields using regular 
                         expressions, else match string fields using
                         strict equality (i.e. '==').  Defaults to true.

        Returns integer specifying number of records that were updated.

        Example:
            db.update('plane.tbl',['country','speed'],['USA','>400'],
             [1230],['range'])

            This will search for any plane from the USA with a speed
            greater than 400mph and update it's range to 1230 miles.
        """

        # Make copy of searchData list so that value passed in is not 
        # changed if I edit it in validateMatchCriteria.
        patterns = list(searchData)

        # Open the table.
        fptr = self._openTable(name, 'r+')

        # Update the instance variables holding table header info.
        self._updateHeaderVars(fptr)

        # If no update filter fields were specified, that means user wants
        # to update all field in record, so we set the filter list equal
        # to the list of field names of table, excluding the recno field,
        # since user is not allowed to update recno field.
        if filter:
            if isinstance(updates, list):
                pass
            # If updates is a dictionary, user cannot specify a filter,
            # because the keys of the dictionary will function as the
            # filter.
            elif isinstance(updates, dict):
                raise KBError('Cannot specify filter when updates is a ' +
                 'dictionary.')
            else:
                raise KBError('Cannot specify filter when updates is an ' +
                 'object.')

        else:
            # If updates is a list and no update filter
            # fields were specified, that means user wants to update
            # all fields in record, so we set the filter list equal
            # to the list of field names of table, excluding the recno
            # field, since user is not allowed to update recno field.
            if isinstance(updates, list): filter = self.field_names[1:]

        # If updates is a list, do nothing because it is already in the
        # proper format and filter has either been supplied by the user
        # or populated above.
        if isinstance(updates, list): pass
        # If updates is a dictionary, we are going to convert it into an
        # updates list and a filters list.  This will allow us to use the
        # same routines for validation and updating.
        elif isinstance(updates, dict):
            filter = [k for k in updates.keys() if k in 
             self.field_names[1:]]
            updates = [updates[i] for i in filter]
        # If updates is an object, we are going to convert it into an
        # updates list and a filters list.  This will allow us to use the
        # same routines for validation and updating.
        else:
            filter = [x for x in self.field_names[1:] if hasattr(updates,x)]
            updates = [getattr(updates,x) for x in self.field_names[1:] if 
             hasattr(updates,x)]

        try:
            # Check input arguments to make sure they are valid.
            self._validateMatchCriteria(fields, patterns)
            self._validateUpdateCriteria(updates, filter)
        except KBError:
            # If something didn't check out, close the table and re-raise
            # the error.
            fptr.close()
            raise

        # Search the table and populate the match list.
        match_list = self._getMatches(fptr, fields, patterns, useRegExp)

        # Create a list with each member being a list made up of a
        # fieldname and the corresponding update value, converted to a
        # safe string.
        filter_updates = zip(filter, 
         [self._encodeString(str(u)) for u in updates])

        updated = 0
        # Step through the match list.
        for line, fpos in match_list:
            # Create a copy of the current record.
            new_record = line.strip().split('|')
            # For each filter field, apply the updated value to the
            # table record.
            for field, update in filter_updates:
                new_record[self.field_names.index(field)] = update

            # Convert the updated record back into a text line so we
            # can write it back out to the file.
            new_line = '|'.join(new_record)

            # Since we are changing the current record, we will first
            # write over it with all blank spaces in the file.
            self._deleteRecord(fptr, fpos, line)

            # If the updated copy of the record is not bigger than the
            # old copy, then we can just write it in the same spot in
            # the file.  If it is bigger, then we will have to append
            # it to the end of the file.
            if len(new_line) > len(line):
                self._writeRecord(fptr, 'end', new_line)
                # If we didn't overwrite the current record, that means
                # we have another blank record (i.e. delete record) out
                # there, so we need to increment the deleted records
                # counter.
                self._incrDeleteCounter(fptr)
            else:
                self._writeRecord(fptr, fpos, new_line)
            updated+=1

        # Close the table.
        self._closeTable(fptr)

        # Return the number of records updated.
        return updated

    #----------------------------------------------------------------------
    # delete
    #----------------------------------------------------------------------
    def delete(self, name, fields, searchData, useRegExp=False):
        """Delete record(s) from table, return number of records deleted.

        Arguments:
            name       - physical file name, including path, that holds
                         table.
            fields     - list containing names of fields to search on. if
                         any of the items in this list is 'recno', then the
                         table will be searched by the recno field only and
                         will delete, at most, one record, since recno is 
                         the system generated primary key.
            searchData - list containing actual data to search on.  Each 
                         item in list corresponds to item in the 'fields'
                         list.
            useRegExp  - if true, match string fields using regular 
                         expressions, else match string fields using
                         strict equality (i.e. '==').  Defaults to true.

        Returns integer specifying number of records that were deleted.

        Example:
            db.delete('plane.tbl',['country','speed'],['USA','>400'])

            This will search for any plane from the USA with a speed
            greater than 400mph and delete it.
        """

        # Make copy of searchData list so that value passed in is not 
        # changed if I edit it in validateMatchCriteria.
        patterns = list(searchData)

        # Open the table.
        fptr = self._openTable(name, 'r+')

        # Update the instance variables holding table header info.
        self._updateHeaderVars(fptr)

        try:
            # Check input arguments to make sure they are valid.
            self._validateMatchCriteria(fields, patterns)
        except KBError:
            # If something didn't check out, close the table and re-raise
            # the error.
            fptr.close()
            raise

        # Search the table and populate the match list.
        match_list = self._getMatches(fptr, fields, patterns, useRegExp)
        deleted = 0

        # Delete any matches found.
        for line, fpos in match_list:
            self._deleteRecord(fptr, fpos, line)
            # Increment the delete counter.
            self._incrDeleteCounter(fptr)
            deleted+=1

        # Close the table.
        self._closeTable(fptr)

        # Return the number of records deleted.
        return deleted

    #----------------------------------------------------------------------
    # select
    #----------------------------------------------------------------------
    def select(self, name, fields, searchData, filter=None, 
     useRegExp=False, sortFields=[], sortDesc=[], returnType='list', 
     rptSettings=[0,False]):
        """Select record(s) from table, return list of records selected.

        Arguments:
            name          - physical file name, including path, that holds
                            table.
            fields        - list containing names of fields to search on. 
                            If any of the items in this list is 'recno', 
                            then the table will be searched by the recno 
                            field only and will select, at most, one record,
                            since recno is the system generated primary key.
            searchData    - list containing actual data to search on.  Each
                            item in list corresponds to item in the 
                            'fields' list.
            filter        - list containing names of fields to include for
                            selected records.  If 'filter' list is empty or
                            equal to None, then all fields will be included
                            in result set.
            useRegExp     - if true, match string fields using regular 
                            expressions, else match string fields using
                            strict equality (i.e. '==').  Defaults to False.
            sortFields    - list of fieldnames to sort on.  Each must be a
                            valid field name, and, if filter list is not
                            empty, the same fieldname must be in the filter
                            list.  Result set will be sorted in the same
                            order as fields appear in sortFields in 
                            ascending order unless the same field name also 
                            appears in sortDesc, then they will be sorted in
                            descending order.
            sortDesc      - list of fieldnames that you want to sort result
                            set by in descending order.  Each field name
                            must also be in sortFields.
            returnType    - a string specifying the type of the items in the
                            returned list.  Can be 'list' (items are lists
                            of values), 'dict' (items are dictionaries with
                            keys = field names and values = matching
                            values), 'object' (items = instances of the
                            generic Record class) or 'report' (result set
                            is formatted as a table with a header, suitable
                            for printing).  Defaults to list.
            rptSettings   - a list with two elements.  This is only used if
                            returnType is 'report'.  The first element
                            specifies the number of records to print on each
                            page.  The default is 0, which means do not do
                            any page breaks.  The second element is a 
                            boolean specifying whether to print a row 
                            separator (a line of dashes) between each 
                            record.  The default is False.

        Returns list of records matching selection criteria.

        Example:
            db.select('plane.tbl',['country','speed'],['USA','>400'])

            This will search for any plane from the USA with a speed
            greater than 400mph and return it.
        """

        # Check returnType argument to make sure it is either 'list',
        # 'dict', or 'object'.
        if returnType not in ['list', 'dict', 'object', 'report']:
            raise KBError('Invalid return type: %s' % returnType)

        # Check rptSettings list to make sure it's items are valid.
        if type(rptSettings[0]) != int:
            raise KBError('Invalid report setting: %s' % rptSettings[0])
        if type(rptSettings[1]) != bool:        
            raise KBError('Invalid report setting: %s' % rptSettings[1])

        # Make copy of searchData list so that value passed in is not 
        # changed if I edit it in validateMatchCriteria.
        patterns = list(searchData)

        # Open the table in read-only mode since we won't be updating it.
        fptr = self._openTable(name, 'r')

        # Update the instance variables holding table header info.
        self._updateHeaderVars(fptr)

        try:
            # Check input arguments to make sure they are valid.
            self._validateMatchCriteria(fields, patterns)
            if filter: self._validateFilter(filter)
            else: filter = self.field_names
        except KBError:
            # If something didn't check out, close the table and re-raise
            # the error.
            fptr.close()
            raise

        # Validate sort field argument.  It needs to be one of the field
        # names included in the filter.
        for field in [sf for sf in sortFields if sf not in filter]:
            raise KBError('Invalid sort field specified: %s' % field)
        # Make sure any fields specified in sort descending list are also
        # in sort fields list.    
        for field in [sf for sf in sortDesc if sf not in sortFields]:
            raise KBError('Cannot specify a field to sort in descending ' +
             'order if you have not specified that field as a sort field')

        # Search table and populate match list.
        match_list = self._getMatches(fptr, fields, patterns, useRegExp)

        # Initialize result set.
        result_set = []
        # Get a list of filter field indexes (i.e., where in the
        # table record is the field that the filter item is
        # referring to.
        filterIndeces = [self.field_names.index(x) for x in filter]

        # For each record in match list, add it to the result set.
        for record, fpos in match_list:
            # Initialize a record to hold the filtered fields of
            # the record.
            result_rec = []
            # Split the record line into it's fields.
            fields = record.split('|')

            # Step through each field index in the filter list. Grab the
            # result field at that position, convert it to
            # proper type, and put it in result set.
            for i in filterIndeces:
                # If the field is empty, just append it to the result rec.
                # CHANGE TO KIRBYBASE CODE:                
                #if fields[i] == '':
                    #result_rec.append(None)
                # Otherwise, convert field to its proper type before 
                # appending it to the result record.
                #else:
                result_rec.append(
                     self.convert_types_functions[i](fields[i]))

            # Add the result record to the result set.
            result_set.append(result_rec)

        # Close the table.
        self._closeTable(fptr)

        # If a sort field was specified...
        # I stole the following code from Steve Lucy.  I got it from the
        # ASPN Python Cookbook webpages.  Thanks Steve!
        if len(sortFields) > 0:
            reversedSortFields = list(sortFields)
            reversedSortFields.reverse()
            for sortField in reversedSortFields:
                i = filter.index(sortField)
                result_set.sort( lambda x,y:
                    cmp(*[(x[i], y[i]), (y[i], x[i])]
                     [sortField in sortDesc]))

        # If returnType is 'object', then convert each result record
        # to a Record object before returning the result list.
        if returnType == 'object':
            return [Record(filter, rec) for rec in result_set]
        # If returnType is 'dict', then convert each result record to
        # a dictionary with the keys being the field names before returning
        # the result list.
        elif returnType == 'dict':
            return [dict(zip(filter, rec)) for rec in result_set]
        # If returnType is 'report', then return a pretty print version of
        # the result set.
        elif returnType == 'report':
            # How many records before a formfeed.
            numRecsPerPage = rptSettings[0]
            # Put a line of dashes between each record?
            rowSeparator = rptSettings[1]
            delim = ' | '

            # columns of physical rows
            columns = apply(zip, [filter] + result_set)

            # get the maximum of each column by the string length of its 
            # items
            maxWidths = [max([len(str(item)) for item in column]) 
             for column in columns]
            # Create a string of dashes the width of the print out.
            rowDashes = '-' * (sum(maxWidths) + len(delim)*
             (len(maxWidths)-1))

            # select the appropriate justify method
            justifyDict = {str:str.ljust,int:str.rjust,float:str.rjust,
             bool:str.ljust,datetime.date:str.ljust,
             datetime.datetime:str.ljust}

            # Create a string that holds the header that will print.
            headerLine = delim.join([justifyDict[fieldType](item,width) 
             for item,width,fieldType in zip(filter,maxWidths,
            self.field_types)])

            # Create a StringIO to hold the print out.
            output=cStringIO.StringIO()

            # Variable to hold how many records have been printed on the
            # current page.
            recsOnPageCount = 0

            # For each row of the result set, print that row.
            for row in result_set:
                # If top of page, print the header and a dashed line.
                if recsOnPageCount == 0:
                    print >> output, headerLine
                    print >> output, rowDashes

                # Print a record.
                print >> output, delim.join([justifyDict[fieldType](
                 str(item),width) for item,width,fieldType in 
                 zip(row,maxWidths,self.field_types)])

                # If rowSeparator is True, print a dashed line.
                if rowSeparator: print >> output, rowDashes

                # Add one to the number of records printed so far on
                # the current page.
                recsOnPageCount += 1

                # If the user wants page breaks and you have printed 
                # enough records on this page, print a form feed and
                # reset records printed variable.
                if numRecsPerPage > 0 and (recsOnPageCount ==
                 numRecsPerPage):
                    print >> output, '\f',
                    recsOnPageCount = 0
            # Return the contents of the StringIO.
            return output.getvalue()
        # Otherwise, just return the list of lists.
        else:
            return result_set


    #----------------------------------------------------------------------
    # pack
    #----------------------------------------------------------------------
    def pack(self, name):
        """Remove blank records from table and return total removed.

        Keyword Arguments:
            name - physical file name, including path, that holds table.

        Returns number of blank lines removed from table.
        """

        # Open the table in read-only mode since we won't be updating it.
        fptr = self._openTable(name, 'r')

        # Read in all records.
        lines = fptr.readlines()

        # Close the table so we can re-build it.
        self._closeTable(fptr)

        # Reset number of deleted records to zero.
        header_rec = lines[0].split('|')
        header_rec[1] = "000000"

        # Set first line of re-built file to the header record.
        lines[0] = '|'.join(header_rec)

        # Open the table in write mode since we will be re-building it.
        fptr = self._openTable(name, 'w')

        # This is the counter we will use to report back how many blank
        # records were removed.
        lines_deleted = 0

        # Step through all records in table, only writing out non-blank
        # records.
        for line in lines:
            # By doing a rstrip instead of a strip, we can remove any
            # extra spaces at the end of line that were a result of
            # updating a record with a shorter one.
            line = line.rstrip()
            if line == "":
               lines_deleted += 1
               continue
            try:
                fptr.write(line + '\n')
            except:
                raise KBError('Could not write record in: ' + name)

        # Close the table.
        self._closeTable(fptr)

        # Return number of records removed from table.
        return lines_deleted

    #----------------------------------------------------------------------
    # validate
    #----------------------------------------------------------------------
    def validate(self, name):
        """Validate all records have field values of proper data type.

        Keyword Arguments:
            name - physical file name, including path, that holds table.

        Returns list of records that have invalid data.
        """

        # Open the table in read-only mode since we won't be updating it.
        fptr = self._openTable(name, 'r')

        # Update the instance variables holding table header info
        self._updateHeaderVars(fptr)

        # Create list to hold any invalid records that are found.
        invalid_list = []

        # Loop through all records in the table.
        for line in fptr:
            # Strip off newline character and any trailing spaces.
            line = line[:-1].strip()

            # If blank line, skip this record.
            if line == "": continue

            # Split the line up into fields.
            record = line.split("|")

            # Check the value of recno to see if the value is
            # greater than the last recno assigned.  If it is,
            # add this to the invalid record list.
            if self.last_recno < int(record[0]):
                invalid_list.append([record[0], 'recno', record[0]])

            # For each field in the record check to see if you
            # can convert it to the field type specified in the
            # header record by using the conversion function
            # specified in self.convert_types_functions. 
            # If you can't convert it, add the
            # record number, the field name, and the offending
            # field value to the list of invalid records.
            for i, item in enumerate(record):
                if item == '': continue
                try:
                    if self.convert_types_functions[i](item): pass
                except:
                    invalid_list.append([record[0], self.field_names[i], 
                     item])

        # Close the table.
        self._closeTable(fptr)

        # Return list of invalid records.
        return invalid_list

    #----------------------------------------------------------------------
    # drop
    #----------------------------------------------------------------------
    def drop(self, name):
        """Delete physical file containing table and return True.

        Arguments:
            name - physical filename, including path, that holds table.

        Returns True if no exceptions are raised.
        """

        # Delete physical file.
        os.remove(name)

        # Return success.
        return True

    #----------------------------------------------------------------------
    # getFieldNames
    #----------------------------------------------------------------------
    def getFieldNames(self, name):
        """Return list of field names for specified table name

        Arguments:
            name - physical file name, including path, that holds table.

        Returns list of field names for table.
        """

        # Open the table in read-only mode since we won't be updating it.
        fptr = self._openTable(name, 'r')

        # Update the instance variables holding table header info
        self._updateHeaderVars(fptr)

        # Close the table.
        self._closeTable(fptr)

        return self.field_names

    #----------------------------------------------------------------------
    # getFieldTypes
    #----------------------------------------------------------------------
    def getFieldTypes(self, name):
        """Return list of field types for specified table name

        Arguments:
            name - physical file name, including path, that holds table.

        Returns list of field types for table.
        """

        # Open the table in read-only mode since we won't be updating it.
        fptr = self._openTable(name, 'r')

        # Update the instance variables holding table header info
        self._updateHeaderVars(fptr)

        # Close the table.
        self._closeTable(fptr)

        return self.field_types


    #----------------------------------------------------------------------
    # len
    #----------------------------------------------------------------------
    def len(self, name):
        '''Return total number of non-deleted records in specified table

        Arguments:
            name - physical file name, including path, that holds table.

        Returns total number of records in table.
        '''

        # Initialize counter.
        rec_count = 0

        # Open the table in read-only mode since we won't be updating it.
        fptr = self._openTable(name, 'r')

        # Skip header record.
        line = fptr.readline()

        # Loop through entire table.
        line = fptr.readline()
        while line:
            # Strip off newline character.
            line = line[0:-1]

            # If not blank line, add 1 to record count.
            if line.strip() != "": rec_count += 1

            # Read next record.
            line = fptr.readline()

        # Close the table.
        self._closeTable(fptr)

        return rec_count

    #----------------------------------------------------------------------
    # PRIVATE METHODS
    #----------------------------------------------------------------------


    #----------------------------------------------------------------------
    # _strToBool
    #----------------------------------------------------------------------
    def _strToBool(self, boolString):
        if boolString == 'True': return True
        elif boolString == 'False': return False
        else: raise KBError('Invalid value for boolean: %s' % boolString)


    #----------------------------------------------------------------------
    # _strToDate
    #----------------------------------------------------------------------
    def _strToDate(self, dateString):
        # Split the date string up into pieces and create a
        # date object.
        return datetime.date(*map(int, dateString.split('-'))) 

    #----------------------------------------------------------------------
    # _strToDateTime
    #----------------------------------------------------------------------
    def _strToDateTime(self, dateTimeString):
        # Split datetime string into datetime portion microseconds portion.
        tempDateTime = dateTimeString.split('.')
        # Were there microseconds in the datetime string.
        if len(tempDateTime) > 1: microsec = int(tempDateTime[1])
        else: microsec = 0

        # Now, split the datetime portion into a date
        # and a time string.  Take all of the pieces and
        # create a datetime object.
        tempDate, tempTime = tempDateTime[0].split(' ')
        y, m, d = tempDate.split('-')
        h, min, sec = tempTime.split(':')
        return datetime.datetime(int(y),int(m),int(d),int(h),int(min),
         int(sec),microsec)

    #----------------------------------------------------------------------
    # _encodeString
    #----------------------------------------------------------------------
    def _encodeString(self, s):
        '''Encode a string.

        Translates problem characters like \n, \r, and \032 to benign
        character strings.

        Keyword Arguments:
            s - string to encode.

        Returns encoded string.
        '''
        if self.encodeRegExp.search(s):
            s = s.replace('\n', '&linefeed;')
            s = s.replace('\r', '&carriage_return;')
            s = s.replace('\032', '&substitute;')
            s = s.replace('|', '&pipe;')
        return s

    #----------------------------------------------------------------------
    # _unencodeString
    #----------------------------------------------------------------------
    def _unencodeString(self, s):
        '''Unencode a string.

        Translates encoded character strings back to special characters
        like \n, \r, \032.

        Keyword Arguments:
            s - string to unencode.

        Returns unencoded string.
        '''
        if self.unencodeRegExp.search(s):
            s = s.replace('&linefeed;', '\n')
            s = s.replace('&carriage_return;', '\r')
            s = s.replace('&substitute;', '\032')
            s = s.replace('&pipe;', '|')
        return s

    #----------------------------------------------------------------------
    # _updateHeaderVars
    #----------------------------------------------------------------------
    def _updateHeaderVars(self, fptr):
        # Go to the header record and read it in.
        fptr.seek(0)
        line = fptr.readline()

        # Chop off the newline character.
        line = line[0:-1]

        # Split the record into fields.
        header_rec = line.split('|')

        # Update Last Record Number and Deleted Records counters.
        self.last_recno = int(header_rec[0])
        self.del_counter = int(header_rec[1])

        # Skip the recno counter, and the delete counter.
        header_fields = header_rec[2:]

        # Create an instance variable holding the field names.
        self.field_names = [item.split(':')[0] for item in header_fields]
        # Create an instance variable holding the field types.
        self.field_types = [self.strToTypes[x.split(':')[1]] for x in
         header_fields]

        # the functions to use to convert values as strings into their type
        convTypes={ int:int, float:float ,bool:bool, #bool:self._strToBool,
            str:self._unencodeString,
            datetime.date:self._strToDate,
            datetime.datetime:self._strToDateTime }
        self.convert_types_functions = [convTypes[f] for f in 
         self.field_types]


    #----------------------------------------------------------------------
    # _validateMatchCriteria
    #----------------------------------------------------------------------
    def _validateMatchCriteria(self, fields, patterns):
        """Run various checks against list of fields and patterns to be
        used as search criteria.  This method is called from all public
        methods that search the database.
        """
        if len(fields) == 0:
            raise KBError('Length of fields list must be greater ' +
             'than zero.')
        if len(fields) != len(patterns):
            raise KBError('Length of fields list and patterns list ' +
             'not the same.')

        # If any of the list of fields to search on do not match a field
        # in the table, raise an error.
        for field, pattern in zip(fields, patterns):
            if field not in self.field_names:
                raise KBError('Invalid field name in fields list: %s' 
                    %field)

            # If the field is recno, make sure they are trying not to
            # search on more than one field.  Also, make sure they are
            # either trying to match all records or that it is an integer.
            if field == 'recno':
                if len(fields) > 1:
                    raise KBError('If selecting by recno, no other ' +
                     'selection criteria is allowed')
                if pattern != '*':
                    # check if all specified recnos are integers
                    if not isinstance(pattern,(tuple,list)):
                        pattern = [pattern]
                    for x in pattern:
                        if not isinstance(x,int):
                            raise KBError('Recno argument %s has type %s' 
                                ', expected an integer' %(x,type(x)))                        
                continue

            # If the field type is not a str or a bool, make sure the
            # pattern you are searching on has a proper comparion
            # operator (<,<=,>,>=,==,!=,or <>) in it.
            if (self.field_types[self.field_names.index(field)] in  
             [int, float, datetime.date, datetime.datetime]):
                r = re.search('[\s]*[\+-]?\d', pattern)
                if not self.cmpFuncs.has_key(pattern[:r.start()]):
                    raise KBError('Invalid comparison syntax: %s'
                     % pattern[:r.start()])


    #----------------------------------------------------------------------
    #_convertInput
    #----------------------------------------------------------------------
    def _convertInput(self, values):
        """If values is a dictionary or an object, we are going to convert 
        it into a list.  That way, we can use the same validation and 
        updating routines regardless of whether the user passed in a 
        dictionary, an object, or a list.
        """
        # If values is a list, make a copy of it.
        if isinstance(values, list): record = list(values)
        # If values is a dictionary, convert it's values into a list
        # corresponding to the table's field names.  If there is not
        # a key in the dictionary corresponding to a field name, place a
        # '' in the list for that field name's value.
        elif isinstance(values, dict):
            record = [values.get(k,'') for k in self.field_names[1:]]        
        # If values is a record object, then do the same thing for it as
        # you would do for a dictionary above.
        else:
            record = [getattr(values,a,'') for a in self.field_names[1:]]
        # Return the new list with all items == None replaced by ''.
        new_rec = []
        for r in record:
            if r == None:
                new_rec.append('')
            else:
                new_rec.append(r)
        return new_rec        


    #----------------------------------------------------------------------
    # _validateUpdateCriteria
    #----------------------------------------------------------------------
    def _validateUpdateCriteria(self, updates, filter):
        """Run various checks against list of updates and fields to be
        used as update criteria.  This method is called from all public
        methods that update the database.
        """
        if len(updates) == 0:
            raise KBError('Length of updates list must be greater ' +
             'than zero.')

        if len(updates) != len(filter):
            raise KBError('Length of updates list and filter list ' +
             'not the same.')
        # Since recno is the record's primary key and is system
        # generated, like an autoincrement field, do not allow user
        # to update it.
        if 'recno' in filter:
            raise KBError("Cannot update value of 'recno' field.")

        # Validate filter list.
        self._validateFilter(filter)

        # Make sure each update is of the proper type.
        for update, field_name in zip(updates, filter):
            if update in ['', None]: pass
            elif type(update) != self.field_types[
             self.field_names.index(field_name)]:
                raise KBError("Invalid update value for %s" % field_name)

    #----------------------------------------------------------------------
    # _validateFilter
    #----------------------------------------------------------------------
    def _validateFilter(self, filter):
        # Each field in the filter list must be a valid field in the table.
        for field in filter:
            if field not in self.field_names:
                raise KBError('Invalid field name: %s' % field)

    #----------------------------------------------------------------------
    # _getMatches
    #----------------------------------------------------------------------
    def _getMatches(self, fptr, fields, patterns, useRegExp):
        # Initialize a list to hold all records that match the search
        # criteria.
        match_list = []

        # If one of the fields to search on is 'recno', which is the
        # table's primary key, then search just on that field and return
        # at most one record.
        if 'recno' in fields:
            return self._getMatchByRecno(fptr,patterns)
        # Otherwise, search table, using all search fields and patterns
        # specified in arguments lists.
        else:
            new_patterns = [] 
            fieldNrs = [self.field_names.index(x) for x in fields]
            for fieldPos, pattern in zip(fieldNrs, patterns):
                if self.field_types[fieldPos] == str:
                    # If useRegExp is True, compile the pattern to a
                    # regular expression object and add it to the
                    # new_patterns list.  Otherwise,  just add it to
                    # the new_patterns list.  This will be used below 
                    # when matching table records against the patterns.
                    if useRegExp:
                        new_patterns.append(re.compile(pattern))
                        # the pattern can be a tuple with re flags like re.I
                    else:
                        new_patterns.append(pattern)
                elif self.field_types[fieldPos] == bool:
                    # If type is boolean, I am going to coerce it to be
                    # either True or False by applying bool to it.  This
                    # is because it could be '' or [].  Next, I am going
                    # to convert it to the string representation: either
                    # 'True' or 'False'.  The reason I do this is because
                    # that is how it is stored in each record of the table
                    # and it is a lot faster to change this one value from
                    # boolean to string than to change possibly thousands
                    # of table values from string to boolean.  And, if they
                    # both are either 'True' or 'False' I can still
                    # compare them using the equality test and get the same
                    # result as if they were both booleans.
                    new_patterns.append(str(bool(pattern)))
                else:
                    # If type is int, float, date, or datetime, this next
                    # bit of code will split the the comparison string
                    # into the string representing the comparison
                    # operator (i.e. ">=" and the actual value we are going
                    # to compare the table records against from the input
                    # pattern, (i.e. "5").  So, for example, ">5" would be
                    # split into ">" and "5".
                    r = re.search('[\s]*[\+-]?\d', pattern)
                    if self.field_types[fieldPos] == int:
                        patternValue = int(pattern[r.start():])
                    elif self.field_types[fieldPos] == float:
                        patternValue = float(pattern[r.start():])
                    else:
                        patternValue = pattern[r.start():]
                    new_patterns.append(
                     [self.cmpFuncs[pattern[:r.start()]], patternValue]
                    ) 

            fieldPos_new_patterns = zip(fieldNrs, new_patterns)
            maxfield = max(fieldNrs)+1

            # Record current position in table. Then read first detail
            # record.
            fpos = fptr.tell()
            line = fptr.readline()

            # Loop through entire table.
            while line:
                # Strip off newline character and any trailing spaces.
                line = line[:-1].strip()
                try:
                    # If blank line, skip this record.
                    if line == "": raise 'No Match'
                    # Split the line up into fields.
                    record = line.split("|", maxfield)

                    # Foreach correspond field and pattern, check to see
                    # if the table record's field matches successfully.
                    for fieldPos, pattern in fieldPos_new_patterns:
                        # If the field type is string, it
                        # must be an exact match or a regular expression,
                        # so we will compare the table record's field to it
                        # using either '==' or the regular expression 
                        # engine.  Since it is a string field, we will need
                        # to run it through the unencodeString function to
                        # change any special characters back to their 
                        # original values.
                        if self.field_types[fieldPos] == str:
                            try:
                                if useRegExp:
                                    if not pattern.search(
                                     self._unencodeString(record[fieldPos])
                                     ):
                                        raise 'No Match'
                                else:
                                    if record[fieldPos] != pattern:
                                        raise 'No Match'        
                            except Exception:
                                raise KBError(
                                 'Invalid match expression for %s'
                                 % self.field_names[fieldPos])
                        # If the field type is boolean, then I will simply
                        # do an equality comparison.  See comments above
                        # about why I am actually doing a string compare
                        # here rather than a boolean compare.
                        elif self.field_types[fieldPos] == bool:
                            if record[fieldPos] != pattern:
                                raise 'No Match'
                        # If it is not a string or a boolean, then it must 
                        # be a number or a date.
                        else:
                            # Convert the table's field value, which is a
                            # string, back into it's native type so that
                            # we can do the comparison.
                            if record[fieldPos] == '':
                                tableValue = None
                            elif self.field_types[fieldPos] == int:
                                tableValue = int(record[fieldPos])
                            elif self.field_types[fieldPos] == float:
                                tableValue = float(record[fieldPos])
                            # I don't convert datetime values from strings
                            # back into their native types because it is
                            # faster to just leave them as strings and 
                            # convert the comparison value that the user
                            # supplied into a string.  Comparing the two
                            # strings works out the same as comparing two
                            # datetime values anyway.    
                            elif self.field_types[fieldPos] in (
                             datetime.date, datetime.datetime):
                                tableValue = record[fieldPos]
                            else:
                                # If it falls through to here, then,
                                # somehow, a bad field type got put into
                                # the table and we show an error.
                                raise KBError('Invalid field type for %s'
                                 % self.field_names[fieldPos])
                            # Now we do the actual comparison.  I used to
                            # just do an eval against the pattern string
                            # here, but I found that eval's are VERY slow.
                            # So, now I determine what type of comparison
                            # they are trying to do and I do it directly.
                            # This sped up queries by 40%.     
                            if not pattern[0](tableValue, pattern[1]):
                                raise 'No Match' 
                # If a 'No Match' exception was raised, then go to the
                # next record, otherwise, add it to the list of matches.
                except 'No Match':
                    pass
                else:
                    match_list.append([line, fpos])
                # Save the file position BEFORE we read the next record,
                # because after a read it is pointing at the END of the
                # current record, which, of course, is also the BEGINNING
                # of the next record.  That's why we have to save the
                # position BEFORE we read the next record.
                fpos = fptr.tell()
                line = fptr.readline()

        # After searching, return the list of matched records.
        return match_list

    #----------------------------------------------------------------------
    # _getMatchByRecno
    #----------------------------------------------------------------------
    def _getMatchByRecno(self, fptr, recnos):
        """Search by recnos. recnos is a list, containing '*', an integer, or
        a list or tuple of integers"""

        # Initialize table location marker and read in first record
        # of table.
        fpos = fptr.tell()
        line = fptr.readline()

        if recnos == ['*']:
            # take all the non blank lines
            while line:
                line = line[:-1] # remove trailing \n (patch ver. 1.8.2)
                if line.strip():
                    yield [line,fpos]
                fpos = fptr.tell()
                line = fptr.readline()
        else:
            # select the records with record number in recnos
            if isinstance(recnos[0],(tuple,list)):
                # must make it a list, to be able to remove items
                recnos = list(recnos[0])
            while line:
                # Strip of newline character.
                line = line[0:-1]

                # If line is not blank, split it up into fields.
                if line.strip():
                    record = line.split("|")
                    # If record number for current record equals record number
                    # we are searching for, add it to match list
                    if int(record[0]) in recnos:
                        yield [line, fpos]
                        recnos.remove(int(record[0]))
                        # if no more recno to search, stop looping
                        if not recnos: break

                # update the table location marker
                # and read the next record.
                fpos = fptr.tell()
                line = fptr.readline()

        # Stop iteration
        return

    #----------------------------------------------------------------------
    # _incrRecnoCounter
    #----------------------------------------------------------------------
    def _incrRecnoCounter(self, fptr):
        # Save where we are in the table.
        last_pos = fptr.tell()

        # Go to header record and grab header fields.
        fptr.seek(0)
        line = fptr.readline()
        header_rec = line[0:-1].split('|')

        # Increment the recno counter.
        self.last_recno += 1
        header_rec[0] = "%06d" %(self.last_recno)

        # Write the header record back to the file.  Run each field through
        # encoder to handle special characters.
        self._writeRecord(fptr, 0, '|'.join(header_rec))

        # Go back to where you were in the table.
        fptr.seek(last_pos)
        # Return the newly incremented recno counter.
        return self.last_recno

    #----------------------------------------------------------------------
    # _incrDeleteCounter
    #----------------------------------------------------------------------
    def _incrDeleteCounter(self, fptr):
        # Save where we are in the table.
        last_pos = fptr.tell()

        # Go to header record and grab header fields.
        fptr.seek(0)
        line = fptr.readline()
        header_rec = line[0:-1].split('|')

        # Increment the delete counter.
        self.del_counter += 1
        header_rec[1] = "%06d" %(self.del_counter)

        # Write the header record back to the file.
        self._writeRecord(fptr, 0, '|'.join(header_rec))

        # Go back to where you were in the table.
        fptr.seek(last_pos)

    #----------------------------------------------------------------------
    # _deleteRecord
    #----------------------------------------------------------------------
    def _deleteRecord(self, fptr, pos, record):
        # Move to record position in table.
        fptr.seek(pos)

        # Overwrite record with all spaces.
        self._writeRecord(fptr, pos, " " * len(record))

    #----------------------------------------------------------------------
    # _writeRecord
    #----------------------------------------------------------------------
    def _writeRecord(self, fptr, pos, record):
        try:
            # If record is to be appended, go to end of table and write
            # record, adding newline character.
            if pos == 'end':
                fptr.seek(0, 2)
                fptr.write(record + '\n')
            else:
                # Otherwise, move to record position in table and write
                # record.
                fptr.seek(pos)
                fptr.write(record)
        except:
            raise KBError('Could not write record to: ' + fptr.name)

    #----------------------------------------------------------------------
    # _openTable
    #----------------------------------------------------------------------
    def _openTable(self, name, access):
        try:
            # Open physical file holding table.
            fptr = open(name, access)
        except:
            raise KBError('Could not open table: ' + name)
        # Return handle to physical file.
        return fptr

    #----------------------------------------------------------------------
    # _closeTable
    #----------------------------------------------------------------------
    def _closeTable(self, fptr):
        try:
            # Close the file containing the table.
            fptr.close()
        except:
            raise KBError('Could not close table: ' + fptr.name)

#--------------------------------------------------------------------------
# Generic class for records
#--------------------------------------------------------------------------
class Record(object):
    """Generic class for record objects.

    Public Methods:
        __init__ - Create an instance of Record.
    """
    #----------------------------------------------------------------------
    # init
    #----------------------------------------------------------------------
    def __init__(self,names,values):
        self.__dict__ = dict(zip(names, values))


#--------------------------------------------------------------------------
# KBError Class
#--------------------------------------------------------------------------
class KBError(Exception):
    """Exception class for Database Management System.

    Public Methods:
        __init__ - Create an instance of exception.
    """
    #----------------------------------------------------------------------
    # init
    #----------------------------------------------------------------------
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return `self.value`

    # I overrode repr so I could pass error objects from the server to the
    # client across the network.
    def __repr__(self):
        format = """KBError("%s")"""
        return format % (self.value)