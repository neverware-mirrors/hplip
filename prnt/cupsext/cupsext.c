/*
cupsext - Python extension class for CUPS 1.1+
 
 (c) Copyright 2003-2004 Hewlett-Packard Development Company, L.P.

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA


Portions based on:
    "lpadmin" command for the Common UNIX Printing System (CUPS).
 
    Copyright 1997-2003 by Easy Software Products.
 
    These coded instructions, statements, and computer programs are the
    property of Easy Software Products and are protected by Federal
    copyright law.  Distribution and use rights are outlined in the file
    "LICENSE.txt" which should have been included with this file.  If this
    file is missing or damaged please contact Easy Software Products
    at:
 
        Attn: CUPS Licensing Information
        Easy Software Products
        44141 Airport View Drive, Suite 204
        Hollywood, Maryland 20636-3111 USA
 
        Voice: (301) 373-9603
        EMail: cups-info@cups.org
          WWW: http://www.cups.org
 
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
 notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
 notice, this list of conditions and the following disclaimer in the
 documentation and/or other materials provided with the distribution.
3. Neither the name of Hewlett-Packard nor the names of its
 contributors may be used to endorse or promote products derived
 from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN
NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PATENT INFRINGEMENT; PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Requires:
CUPS 1.1+
Python 2.2+

Author:
Don Welch

*/


#include <Python.h>
#include <structmember.h>
#include <cups/cups.h>
#include <cups/language.h>


/*
 * 'validate_name()' - Make sure the printer name only contains valid chars.
 */

static int                      /* O - 0 if name is no good, 1 if name is good */
validate_name(const char *name) /* I - Name to check */
{
  const char    *ptr;                /* Pointer into name */


 /*
  * Scan the whole name...
  */

  for (ptr = name; *ptr; ptr ++)
    if (*ptr == '@')
      break;
    else if ((*ptr >= 0 && *ptr <= ' ') || *ptr == 127 || *ptr == '/')
      return (0);

 /*
  * All the characters are good; validate the length, too...
  */

  return ((ptr - name) < 128);
}


staticforward PyTypeObject printer_Type;

#define printerObject_Check(v) ((v)->ob_type == &printer_Type)

typedef struct
{
    PyObject_HEAD
    PyObject * device_uri;
    PyObject * printer_uri;
    PyObject * name;
    PyObject * location;
    PyObject * makemodel;
    /*PyObject * ppd_name;*/
    int state;
} printer_Object;


static void printer_dealloc( printer_Object * self )
{
    
    Py_XDECREF(self->name);
    Py_XDECREF(self->device_uri);
    Py_XDECREF(self->printer_uri);
    Py_XDECREF(self->location);
    Py_XDECREF(self->makemodel);
    /*Py_XDECREF(self->ppd_name);*/
    PyObject_DEL( self );
}


static PyMemberDef printer_members[] = 
{
    { "device_uri", T_OBJECT_EX, offsetof( printer_Object, device_uri ), 0, "Device URI (device-uri)" },
    /*{ "ppd_name", T_OBJECT_EX, offsetof( printer_Object, ppd_name ), 0, "PPD Name (ppd-name)" },*/
    { "printer_uri", T_OBJECT_EX, offsetof( printer_Object, printer_uri ), 0, "Printer URI (printer-uri)" },
    { "name", T_OBJECT_EX, offsetof( printer_Object, name ), 0, "Name (printer-name)" },
    { "location", T_OBJECT_EX, offsetof( printer_Object, location ), 0, "Location (printer-location)" },
    { "makemodel", T_OBJECT_EX, offsetof( printer_Object, makemodel ), 0, "Make and model (printer-make-and-model)" },
    { "state", T_INT, offsetof( printer_Object, state ), 0, "State (printer-state)" },
    {0}
};

static PyTypeObject printer_Type = 
{
    PyObject_HEAD_INIT( &PyType_Type ) 
    0,                             /* ob_size */
    "cupsext.Printer",           /* tp_name */
    sizeof( printer_Object ),      /* tp_basicsize */    
    0,                             /* tp_itemsize */
    (destructor)printer_dealloc,   /* tp_dealloc */
    0,                             /* tp_print */
    0,                             /* tp_getattr */
    0,                             /* tp_setattr */
    0,                             /* tp_compare */
    0,                             /* tp_repr */
    0,                             /* tp_as_number */
    0,                             /* tp_as_sequence */
    0,                             /* tp_as_mapping */
    0,                             /* tp_hash */
    0,                             /* tp_call */
    0,                             /* tp_str */
    PyObject_GenericGetAttr,       /* tp_getattro */
    PyObject_GenericSetAttr,       /* tp_setattro */
    0,                             /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
    "CUPS Printer object",         /* tp_doc */
    0,                             /* tp_traverse */
    0,                             /* tp_clear */
    0,                             /* tp_richcompare */
    0,                             /* tp_weaklistoffset */
    0,                             /* tp_iter */
    0,                             /* tp_iternext */
    0, /*job_methods, */           /* tp_methods */
    printer_members,               /* tp_members */
    0,                             /* tp_getset */
    0,                             /* tp_base */
    0,                             /* tp_dict */
    0,                             /* tp_descr_get */
    0,                             /* tp_descr_set */
    0,                             /* tp_dictoffset */
    0,                             /* tp_init */
    0,                             /* tp_alloc */
    0,                             /* tp_new */
};
    



static PyObject * _newPrinter( char * device_uri, 
                                char * name,
                            char * printer_uri, 
                                                    char * location, 
                            char * makemodel, 
                            int    state
                            /*char * ppd_name*/ )
{
    printer_Object * self = PyObject_New( printer_Object, &printer_Type );
    if ( !self ) 
        return NULL;
    if ( device_uri != NULL )
        self->device_uri = Py_BuildValue( "s", device_uri );
    if ( printer_uri != NULL )
        self->printer_uri = Py_BuildValue( "s", printer_uri );
    if ( name != NULL )
        self->name = Py_BuildValue( "s", name );
    if ( location != NULL )
        self->location = Py_BuildValue( "s", location );
    if ( makemodel != NULL )
        self->makemodel = Py_BuildValue( "s", makemodel );
    /*if ( ppd_name != NULL )
        self->ppd_name = Py_BuildValue( "s", ppd_name );*/
    self->state = state;
    return (PyObject *)self;
}   

static PyObject * newPrinter( PyObject * self, PyObject * args, PyObject * kwargs )
{
    char * device_uri = "";
    char * name = "";
    char * location = "";
    char * makemodel = "";
    int state = 0;
    char * printer_uri = "";
    /*char * ppd_name = "";*/
        
    char * kwds[] = { "device_uri", "name", "printer_uri", "location", 
                      "makemodel", "state", /*"ppd_name",*/ NULL };
        
    if (!PyArg_ParseTupleAndKeywords( args, kwargs, "zz|zzzi", kwds, 
                                      &device_uri, &name, &printer_uri, 
                      &location, &makemodel, &state 
                      /*&ppd_name*/ ))
        return NULL;        
    
    return _newPrinter( device_uri, printer_uri, name, location, makemodel, state /*ppd_name*/ );
}   

PyObject * getPrinters( PyObject * self, PyObject * args ) 
{
    char buf[1024];
    http_t *http=NULL;     /* HTTP object */
    ipp_t *request=NULL;  /* IPP request object */
    ipp_t *response=NULL; /* IPP response object */
    ipp_attribute_t *attr;     /* Current IPP attribute */
    PyObject * printer_list;
    cups_lang_t * language;
    static const char * attrs[] = /* Requested attributes */
        {
            "printer-info",
            "printer-location",
            "printer-make-and-model",
            "printer-state",
            "printer-name",
            "device-uri",
            "printer-uri-supported",
            /*"ppd-name"*/
        };

    /* Connect to the HTTP server */
    if ( ( http = httpConnectEncrypt( cupsServer(), ippPort(), cupsEncryption() ) ) == NULL )
    {
        goto abort;
    }

    /* Assemble the IPP request */
    request = ippNew();
    language = cupsLangDefault();
    
    request->request.op.operation_id = CUPS_GET_PRINTERS;
    request->request.any.request_id  = 1;

    ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_CHARSET,
        "attributes-charset", NULL,  cupsLangEncoding( language ) );

    ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_LANGUAGE,
        "attributes-natural-language", NULL, language->language );

    ippAddStrings(request, IPP_TAG_OPERATION, IPP_TAG_KEYWORD,
        "requested-attributes", sizeof(attrs) / sizeof(attrs[0]),
        NULL, attrs);

    /* Send the request and get a response. */
    if ((response = cupsDoRequest(http, request, "/")) == NULL)
    {
        goto abort;
    }

    int max_count = 0;

    for ( attr = ippFindAttribute(response, "printer-name", IPP_TAG_NAME),
            max_count = 0; 
        attr != NULL;
        attr = ippFindNextAttribute(response, "printer-name", IPP_TAG_NAME), 
            max_count ++);


    printer_list = PyList_New( max_count );

    char * device_uri;
    char * printer_uri;
    char * info;
    char * location;
    char * make_model;
    char * name;
    /*char * ppd_name;*/
    cups_ptype_t type;
    ipp_pstate_t state;
    int i = 0;

    for (attr = response->attrs; attr != NULL; attr = attr->next)
    {
        while (attr != NULL && attr->group_tag != IPP_TAG_PRINTER)
            attr = attr->next;

        if (attr == NULL)
            break;

        device_uri = "";
        name       = "";
        info       = "";
        location   = "";
        make_model = "";
        printer_uri = "";
        /*ppd_name = "";*/
        type       = CUPS_PRINTER_REMOTE;
        state      = IPP_PRINTER_IDLE;

        while (attr != NULL && attr->group_tag == IPP_TAG_PRINTER)
        {
            /*if ( ( attr->value_tag == IPP_TAG_NAME ) || (attr->value_tag == IPP_TAG_URI ))
            {
                sprintf( buf, "print '%s=%s'", attr->name, attr->values[0].string.text );
                PyRun_SimpleString( buf );
            }*/
            
            if (strcmp(attr->name, "printer-name") == 0 &&
                attr->value_tag == IPP_TAG_NAME)
                name = attr->values[0].string.text;

            else if (strcmp(attr->name, "device-uri") == 0 &&
                attr->value_tag == IPP_TAG_URI)
                device_uri = attr->values[0].string.text;

            else if (strcmp(attr->name, "printer-uri-supported") == 0 &&
                attr->value_tag == IPP_TAG_URI)
                printer_uri = attr->values[0].string.text;
            
            else if (strcmp(attr->name, "printer-info") == 0 &&
                attr->value_tag == IPP_TAG_TEXT)
                info = attr->values[0].string.text;

            else if (strcmp(attr->name, "printer-location") == 0 &&
                attr->value_tag == IPP_TAG_TEXT)
                location = attr->values[0].string.text;

            else if (strcmp(attr->name, "printer-make-and-model") == 0 &&
                attr->value_tag == IPP_TAG_TEXT)
                make_model = attr->values[0].string.text;

            else if (strcmp(attr->name, "printer-state") == 0 &&
                attr->value_tag == IPP_TAG_ENUM)
                state = (ipp_pstate_t)attr->values[0].integer;
                
            /*else if (strcmp(attr->name, "ppd-name") == 0 &&
                attr->value_tag == IPP_TAG_NAME)
                ppd_name = attr->values[0].string.text;*/
                

            attr = attr->next;
        }

        if (device_uri == NULL)
        {
            if (attr == NULL)
                break;
            else
                continue;
        }  

        printer_Object * printer;
        printer = (printer_Object *)_newPrinter( device_uri, name, printer_uri, location, make_model,
        state/*, ppd_name*/ ); 
        PyList_SET_ITEM( printer_list, i, (PyObject *)printer );

        i++;

        if (attr == NULL)
            break;  
    }

    return printer_list;

abort:
    if (response != NULL)
        ippDelete(response);
        
    if (http != NULL)
        httpClose(http);
    
    printer_list = PyList_New( 0 );
    return printer_list;
}


PyObject *  addPrinter( PyObject * self, PyObject * args ) 
{
    //char buf[1024];
    ipp_status_t status;
    http_t *http=NULL;     /* HTTP object */
    ipp_t *request=NULL;  /* IPP request object */
    ipp_t *response=NULL; /* IPP response object */
    ipp_attribute_t *attr;     /* Current IPP attribute */
    cups_lang_t * language;
    int r;
    char printer_uri[HTTP_MAX_URI];  
    char * name, * device_uri, *location, *ppd_file, * info;
    const char * status_str = "successful-ok";


    if ( !PyArg_ParseTuple( args, "zzzzz", 
                            &name, // name of printer
                            &device_uri, // DeviceURI (e.g., hp:/usb/PSC_2200_Series?serial=0000000010)
                            &location, // location of printer
                            &ppd_file, // path to PPD file (uncompressed, must exist)
                            &info // info/description
                            ) )
    {
        r = 0;
        status_str = "Invalid arguments";
        goto abort;
    }

    if ( !validate_name( name ) )
    {
        r = 0;
        status_str = "Invalid printer name";
        goto abort;
    }

    
    sprintf( printer_uri, "ipp://localhost/printers/%s", name );
    
    if (info == NULL )
        strcpy( info, name );
    
     /* Connect to the HTTP server */
    if ((http = httpConnectEncrypt(cupsServer(), ippPort(), cupsEncryption())) == NULL)
    {
        r = 0;
        status_str = "Unable to connect to CUPS server";
        goto abort;
    }

    /* Assemble the IPP request */
    request = ippNew();
    language = cupsLangDefault();
    
    request->request.op.operation_id = CUPS_ADD_PRINTER;
    request->request.any.request_id  = 1;

    ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_CHARSET,
        "attributes-charset", NULL, cupsLangEncoding( language ) );

    ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_LANGUAGE,
        "attributes-natural-language", NULL, language->language );
    
    ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_URI,
        "printer-uri", NULL, printer_uri );

    ippAddInteger(request, IPP_TAG_PRINTER, IPP_TAG_ENUM,
        "printer-state", IPP_PRINTER_IDLE );
        
    ippAddBoolean( request, IPP_TAG_PRINTER, "printer-is-accepting-jobs", 1 );
    
    ippAddString(request, IPP_TAG_PRINTER, IPP_TAG_URI, "device-uri", NULL,
                 device_uri );  
         
        ippAddString(request, IPP_TAG_PRINTER, IPP_TAG_TEXT, "printer-info", NULL,
               info );
           
        ippAddString(request, IPP_TAG_PRINTER, IPP_TAG_TEXT, "printer-location", NULL,
               location );
    
    /* Send the request and get a response. */
    if ((response = cupsDoFileRequest(http, request, "/admin/", ppd_file )) == NULL)
    {
        status = cupsLastError();
        r = 0;
    }
    else    
    {
        status = response->request.status.status_code;
        ippDelete( response );
        r = 1;
    }

    status_str = ippErrorString( status );

abort:
        
    if (http != NULL)
        httpClose(http);

    return Py_BuildValue( "is", r, status_str );

}

/*
 * 'delPrinter()' - Delete a printer from the system...
 */
PyObject * delPrinter( PyObject * self, PyObject * args ) 
{
  ipp_t         *request = NULL,                /* IPP Request */
                *response = NULL;                /* IPP Response */
  cups_lang_t   *language;                /* Default language */
  char          uri[HTTP_MAX_URI];        /* URI for printer/class */
  char * name;
  http_t *http = NULL;     /* HTTP object */
  int r = 0;
 
  if ( !PyArg_ParseTuple( args, "z", 
                          &name ) ) // name of printer
  {
      goto abort;
  }

  if ( !validate_name( name ) )
  {
      goto abort;
  }

  /* Connect to the HTTP server */
  if ((http = httpConnectEncrypt(cupsServer(), ippPort(), cupsEncryption())) == NULL)
  {
      goto abort;
  }
  snprintf(uri, sizeof(uri), "ipp://localhost/printers/%s", name );

  /*
      * Build a CUPS_DELETE_PRINTER request, which requires the following
      * attributes:
      *
      *    attributes-charset
      *    attributes-natural-language
      *    printer-uri
     */
  request = ippNew();

  request->request.op.operation_id = CUPS_DELETE_PRINTER;
  request->request.op.request_id   = 1;

  language = cupsLangDefault();

  ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_CHARSET,
               "attributes-charset", NULL, cupsLangEncoding(language));

  ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_LANGUAGE,
               "attributes-natural-language", NULL, language->language);

  ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_URI,
               "printer-uri", NULL, uri);

 /*
  * Do the request and get back a response...
  */
  response = cupsDoRequest(http, request, "/admin/");
  
  if ( (response != NULL) && (response->request.status.status_code <= IPP_OK_CONFLICT) )
  {
    r = 1;
  }
abort:
    if (http!=NULL)
        httpClose(http);
    if (response!=NULL)
        ippDelete(response);
    return Py_BuildValue( "i", r );

}

/*
 * 'setDefaultPrinter()' - Set the default printing destination.
 */

PyObject * setDefaultPrinter( PyObject * self, PyObject * args ) 

{
  char          uri[HTTP_MAX_URI];        /* URI for printer/class */
  ipp_t         *request = NULL,                /* IPP Request */
                *response = NULL;                /* IPP Response */
  cups_lang_t   *language;                /* Default language */
  char * name;
  http_t *http = NULL;     /* HTTP object */
  int r = 0;
 
  if ( !PyArg_ParseTuple( args, "z", 
                          &name ) ) // name of printer
   {
       goto abort;
   }

  if ( !validate_name( name ) )
  {
      goto abort;
  }
  /* Connect to the HTTP server */
  if ((http = httpConnectEncrypt(cupsServer(), ippPort(), cupsEncryption())) == NULL)
  {
      goto abort;
  }

/*
  * Build a CUPS_SET_DEFAULT request, which requires the following
  * attributes:
  *
  *    attributes-charset
  *    attributes-natural-language
  *    printer-uri
  */

  snprintf(uri, sizeof(uri), "ipp://localhost/printers/%s", name);

  request = ippNew();

  request->request.op.operation_id = CUPS_SET_DEFAULT;
  request->request.op.request_id   = 1;

  language = cupsLangDefault();

  ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_CHARSET,
               "attributes-charset", NULL, cupsLangEncoding(language));

  ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_LANGUAGE,
               "attributes-natural-language", NULL, language->language);

  ippAddString(request, IPP_TAG_OPERATION, IPP_TAG_URI,
               "printer-uri", NULL, uri);

 /*
  * Do the request and get back a response...
  */

  response = cupsDoRequest(http, request, "/admin/");
  
  if ((response != NULL) && (response->request.status.status_code <= IPP_OK_CONFLICT ) )
  {
    r = 1;
  }

abort:
    
    if (http!=NULL)
        httpClose(http);
    if (response!=NULL)
        ippDelete(response);
    return Py_BuildValue( "i", r );
   

}



staticforward PyTypeObject job_Type;

typedef struct
{
    PyObject_HEAD
    int id;
    PyObject * dest;
    PyObject * title;
    PyObject * user;
    int state;
    int size;
} job_Object;



static void job_dealloc( job_Object * self )
{
    
    Py_XDECREF(self->dest);
    Py_XDECREF(self->title);
    Py_XDECREF(self->user);
    PyObject_DEL( self );
}

static PyMemberDef job_members[] = 
{
    { "id", T_INT, offsetof( job_Object, id ), 0, "Id" },
    { "dest", T_OBJECT_EX, offsetof( job_Object, dest ), 0, "Destination" },
    { "state", T_INT, offsetof( job_Object, state ), 0, "State" },
    { "title", T_OBJECT_EX, offsetof( job_Object, title ), 0, "Title" },
    { "user", T_OBJECT_EX, offsetof( job_Object, user ), 0, "User" },
    { "size", T_INT, offsetof( job_Object, size ), 0, "Size" },
    {0}
};



static PyTypeObject job_Type = 
{
    PyObject_HEAD_INIT( &PyType_Type ) 
    0,                             /* ob_size */
    "Job",                         /* tp_name */
    sizeof( job_Object ),          /* tp_basicsize */    
    0,                             /* tp_itemsize */
    (destructor)job_dealloc,       /* tp_dealloc */
    0,                             /* tp_print */
    0,                             /* tp_getattr */
    0,                             /* tp_setattr */
    0,                             /* tp_compare */
    0,                             /* tp_repr */
    0,                             /* tp_as_number */
    0,                             /* tp_as_sequence */
    0,                             /* tp_as_mapping */
    0,                             /* tp_hash */
    0,                             /* tp_call */
    0,                             /* tp_str */
    PyObject_GenericGetAttr,       /* tp_getattro */
    PyObject_GenericSetAttr,       /* tp_setattro */
    0,                             /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,            /* tp_flags */
    "CUPS Job object",             /* tp_doc */
    0,                             /* tp_traverse */
    0,                             /* tp_clear */
    0,                             /* tp_richcompare */
    0,                             /* tp_weaklistoffset */
    0,                             /* tp_iter */
    0,                             /* tp_iternext */
    0, /*job_methods, */                  /* tp_methods */
    job_members,                   /* tp_members */
    0,                             /* tp_getset */
    0,                             /* tp_base */
    0,                             /* tp_dict */
    0,                             /* tp_descr_get */
    0,                             /* tp_descr_set */
    0,                             /* tp_dictoffset */
    0,                             /* tp_init */
    0,//(initproc)job_init,            /* tp_init */
    0,                             /* tp_alloc */
    //PyType_GenericAlloc,  
    0, //job_new,                       /* tp_new */    
    //PyType_GenericNew,
};
    

static /*job_Object **/ PyObject * _newJob( int id, int state, char * dest, char * title, char * user, int size )
{
    job_Object * jo;
    jo = PyObject_New( job_Object, &job_Type );
    if ( jo==NULL ) 
        return NULL;
    jo->id = id;
    jo->size = size;
    jo->state = state;
    if (dest != NULL )
        jo->dest = PyString_FromString( dest );
    else
        jo->dest = Py_BuildValue( "" );
        
    if (title != NULL)
        jo->title = PyString_FromString( title );
    else
        jo->title = Py_BuildValue( "" );
    
    if (user != NULL)
        jo->user = PyString_FromString( user );
    else
        jo->user = Py_BuildValue( "" );
    
    return (PyObject *)jo;
    
}

static /*job_Object **/ PyObject * newJob( PyObject * self, PyObject * args, PyObject * kwargs )
{
    char * dest = "";
    int id = 0;
    int state = 0;
    char * title = "";
    char * user = "";
    int size = 0;
            
    char * kwds[] = { "id", "state", "dest", "title", "user", "size", NULL };
        
    if (!PyArg_ParseTupleAndKeywords( args, kwargs, "i|izzzi", kwds, 
                                      &id, &state, &dest, &title, &user, &size))
        return NULL;        

    return _newJob( id, state, dest, title, user, size );
    
}   




PyObject * getDefault( PyObject * self, PyObject * args )
{
    const char * defdest;
    defdest = cupsGetDefault();
    if (defdest == NULL )
        return Py_BuildValue( "" ); // None
    else
        return Py_BuildValue( "s", defdest );

}


PyObject * cancelJob( PyObject * self, PyObject * args ) // cancelJob( dest, jobid )
{
    int status;
    int jobid;
    char * dest;
    
    if ( !PyArg_ParseTuple( args, "si", &dest, &jobid ) )
    {
        return Py_BuildValue( "i", 0 );
    }
    
    status = cupsCancelJob( dest, jobid );
    
    return Py_BuildValue( "i", status );
}

PyObject * getJobs( PyObject * self, PyObject * args )
{
    cups_job_t * jobs;
    int i;
    int num_jobs;
    PyObject * job_list;
    PyObject * newjob;
    int my_job;
    int completed;
    
    if ( !PyArg_ParseTuple( args, "ii", &my_job, &completed ) )
    {
        return PyList_New( 0 );
    }
    
    num_jobs = cupsGetJobs( &jobs, NULL, my_job, completed );
    
    if ( num_jobs > 0 )
    {
        job_list = PyList_New( num_jobs );
        
        for ( i=0; i < num_jobs; i++ )
        {
            job_Object * newjob;
            newjob = (job_Object *)_newJob(  jobs[i].id, 
                            jobs[i].state,
                            jobs[i].dest, 
                            jobs[i].title, 
                            jobs[i].user, 
                            jobs[i].size );
                            
            PyList_SetItem( job_list, i, (PyObject *)newjob );

        }
        cupsFreeJobs( num_jobs, jobs );
    }
    else
    {
        job_list = PyList_New( 0 );
    }
    return job_list;
}




PyObject *  getVersion( PyObject * self, PyObject * args ) 
{
    //return Py_BuildValue( "iii", CUPS_VERSION_MAJOR, CUPS_VERSION_MINOR, CUPS_VERSION_PATCH );
    return Py_BuildValue( "f", CUPS_VERSION );
}

PyObject *  getServer( PyObject * self, PyObject * args ) 
{
    return Py_BuildValue( "s", cupsServer() );
}


static PyMethodDef cupsext_methods[] = 
{
    { "getPrinters", (PyCFunction)getPrinters, METH_VARARGS },
    { "addPrinter",  (PyCFunction)addPrinter,  METH_VARARGS },
    { "delPrinter",  (PyCFunction)delPrinter,  METH_VARARGS },
    { "getDefault",  (PyCFunction)getDefault,  METH_VARARGS },
    { "getVersion",  (PyCFunction)getVersion,  METH_VARARGS },
    { "cancelJob",   (PyCFunction)cancelJob,   METH_VARARGS },
    { "getJobs",     (PyCFunction)getJobs,     METH_VARARGS },
    { "getServer",   (PyCFunction)getServer,   METH_VARARGS },
    { "Job",         (PyCFunction)newJob,      METH_VARARGS | METH_KEYWORDS },
    { "Printer",     (PyCFunction)newPrinter,  METH_VARARGS | METH_KEYWORDS },
    { NULL, NULL }
};  


static char cupsext_documentation[] = "Python extension for CUPS 1.x";

void initcupsext( void )
{
    
    PyObject * mod = Py_InitModule4( "cupsext", cupsext_methods, 
                                     cupsext_documentation, (PyObject*)NULL, 
                     PYTHON_API_VERSION );
                     
    if ( mod == NULL )
        return;                  
                     
                     
}

