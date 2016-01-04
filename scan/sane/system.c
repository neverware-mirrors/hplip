/************************************************************************************\

  system.c - HP SANE backend for multi-function peripherals (libsane-hpaio)

  (c) 2001-2004 Copyright Hewlett-Packard Development Company, LP

  Permission is hereby granted, free of charge, to any person obtaining a copy 
  of this software and associated documentation files (the "Software"), to deal 
  in the Software without restriction, including without limitation the rights 
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
  of the Software, and to permit persons to whom the Software is furnished to do 
  so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
  FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
  IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
  WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

  Current Author: Don Welch
  Contributing Author: David Suffield 

\************************************************************************************/

#include "system.h"

#define HPIOD_PORT_FILE "/var/run/hpiod.port"
#define HPSSD_PORT_FILE "/var/run/hpssd.port"

static int hpiod_port_num = 0;
static int hpiod_socket = -1;

static int hpssd_port_num = 0;
static int hpssd_socket = -1;

static int inited = 0;

#if defined( HPAIO_DEBUG )
void DBG(int level, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
}
#else
void DBG(int level, const char *format, ...)
{
}
#endif
    
int bug(int level, const char *fmt, ...)
{
   char buf[256];
   va_list args;
   int n;

   va_start(args, fmt);
   if ((n = vsnprintf(buf, 256, fmt, args)) == -1)
      buf[255] = 0;     /* output was truncated */
   syslog(LOG_WARNING, buf);
   va_end(args);
   return n;
}

/*
 * sysdump() originally came from http://sws.dett.de/mini/hexdump-c , steffen@dett.de .  
 */
void DBG_DUMP(void *data, int size)
{
    /* dumps size bytes of *data to syslog. Looks like:
     * [0000] 75 6E 6B 6E 6F 77 6E 20
     *                  30 FF 00 00 00 00 39 00 unknown 0.....9.
     * (in a single line of course)
     */

    unsigned char *p = (unsigned char *)data;
    unsigned char c;
    int n;
    char bytestr[4] = {0};
    char addrstr[10] = {0};
    char hexstr[16*3 + 5] = {0};
    char charstr[16*1 + 5] = {0};
    for(n=1;n<=size;n++) {
        if (n%16 == 1) {
            /* store address for this line */
            snprintf(addrstr, sizeof(addrstr), "%.4x",
               (p-(unsigned char *)data) );
        }
            
        c = *p;
        if (isprint(c) == 0) {
            c = '.';
        }

        /* store hex str (for left side) */
        snprintf(bytestr, sizeof(bytestr), "%02X ", *p);
        strncat(hexstr, bytestr, sizeof(hexstr)-strlen(hexstr)-1);

        /* store char str (for right side) */
        snprintf(bytestr, sizeof(bytestr), "%c", c);
        strncat(charstr, bytestr, sizeof(charstr)-strlen(charstr)-1);

        if(n%16 == 0) { 
            /* line completed */
            //syslog(LOG_INFO, "[%4.4s]   %-50.50s  %s\n", addrstr, hexstr, charstr);
            DBG( 0, "[%4.4s]   %-50.50s  %s\n", addrstr, hexstr, charstr);
            hexstr[0] = 0;
            charstr[0] = 0;
        }
        p++; /* next byte */
    }

    if (strlen(hexstr) > 0) {
        /* print rest of buffer if not empty */
        //syslog(LOG_INFO, "[%4.4s]   %-50.50s  %s\n", addrstr, hexstr, charstr);
        DBG( 0, "[%4.4s]   %-50.50s  %s\n", addrstr, hexstr, charstr);
    }
}



unsigned long DivideAndShift( int line,
                              unsigned long numerator1,
                              unsigned long numerator2,
                              unsigned long denominator,
                              int shift )
{
    unsigned long remainder, shiftLoss = 0;
    unsigned long long result = numerator1;
    result *= numerator2;
    if( shift > 0 )
    {
        result <<= shift;
    }
    remainder = result % denominator;
    result /= denominator;
    if( shift < 0 )
    {
        shiftLoss = result & ( ( 1 << ( -shift ) ) - 1 );
        result >>= ( -shift );
    }
    return result;
}

static int GetPair( char * buf, char * key, char * value, char ** tail )
{
    int i = 0, j;

    key[0] = 0;
    value[0] = 0;

    if( buf[i] == '#' )
    {
        for( ; buf[i] != '\n' && i < BUFFER_SIZE; i++ )
            ;  /* eat comment line */
        i++;
    }

    if( strncasecmp( &buf[i], "data:", 5 ) == 0 )
    {
        strcpy( key, "data:" );   /* "data:" key has no value */
        i += 5;
    }
    else
    {
        j = 0;
        while( ( buf[i] != '=' ) && ( i < BUFFER_SIZE ) && ( j < LINE_SIZE ) )
        {
            key[j++] = buf[i++];
        }
        for( j--; key[j] == ' ' && j > 0; j-- )
            ;  /* eat white space before = */
        key[++j] = 0;

        for( i++; buf[i] == ' ' && i < BUFFER_SIZE; i++ )
            ;  /* eat white space after = */

        j = 0;
        while( ( buf[i] != '\n' ) && ( i < BUFFER_SIZE ) && ( j < LINE_SIZE ) )
        {
            value[j++] = buf[i++];
        }
        for( j--; value[j] == ' ' && j > 0; j-- )
            ;  /* eat white space before \n */
        value[++j] = 0;
    }

    i++;   /* bump past '\n' */

    if( tail != NULL )
    {
        *tail = buf + i;
    }  /* tail points to next line */

    return i;
}


static int ParseMsg( char * buf, int len, MsgAttributes * ma )
{
    char key[LINE_SIZE];
    char value[LINE_SIZE];
    char * tail, * tail2;
    int i, ret = R_AOK;

    ma->cmd[0] = 0;
    ma->flow_ctl[0] = 0;
    ma->length = 0;
    ma->data = NULL;
    ma->resultcode = -1;
    ma->deviceid = -1;
    ma->channelid = -1;
    ma->byteswritten = 0;
    ma->numdevices = 0;
    ma->scantype = 0;

    i = GetPair( buf, key, value, &tail );
    
    if( strcasecmp( key, "msg" ) != 0 )
    {
        DBG( 1, "invalid message:%s\n", key);
        return R_INVALID_MESSAGE;
    }
    
    strncpy( ma->cmd, value, sizeof( ma->cmd ) );

    while( i < len )
    {
        i += GetPair( tail, key, value, &tail );

        if( strcasecmp( key, "device-id" ) == 0 )
        {
            ma->deviceid = strtol( value, &tail2, 10 );
        }
        else if( strcasecmp( key, "channel-id" ) == 0 )
        {
            ma->channelid = strtol( value, &tail2, 10 );
        }
        else if( strcasecmp( key, "bytes-written" ) == 0 )
        {
            ma->byteswritten = strtol( value, &tail2, 10 );
        }
        else if( strcasecmp( key, "num-devices" ) == 0 )
        {
            ma->numdevices = strtol( value, &tail2, 10 );
        }
        else if( strcasecmp( key, "scan-type" ) == 0 )
        {
            ma->scantype = strtol( value, &tail2, 10 );
        }
        else if( strcasecmp( key, "length" ) == 0 )
        {
            ma->length = strtol( value, &tail2, 10 );
            if( ma->length > BUFFER_SIZE )
            {
                ret = R_INVALID_LENGTH;
            }
        }
        else if( strcasecmp( key, "data:" ) == 0 )
        {
            ma->data = ( unsigned char * ) tail;
            break;  /* done parsing */
        }
        else if( strcasecmp( key, "result-code" ) == 0 )
        {
            ma->resultcode = strtol( value, &tail2, 10 );
        }
        else if (strcasecmp(key, "io-control") == 0)
        {
            strncpy(ma->flow_ctl, value, sizeof(ma->flow_ctl));
        }
        else
        {
            /* Unknown keys are ignored (R_AOK). */
        }
    }  // end while (i < len)

    return ret;
}


static int XmitAndParseMessage( char * message, int len, int maxlen, MsgAttributes * ma )
{
    if( !inited )
    {
        bug( 0, "XmitAndParseMessage(): not inited, call sane_init() first\n" );
        goto abort;
    }

    if ( send( hpiod_socket, message, len, 0 ) == -1 ) 
    {  
       bug( 0, "XmitAndParseMessage(): unable to send message: %m\n" );  
       goto abort;  
    }  
    
    memset( message, '\0', maxlen );

    if ( ( len = recv( hpiod_socket, message, maxlen, 0 ) ) == -1 ) 
    {  
       bug( 0, "XmitAndParseMessage(): unable to receive result message: %m\n" );  
       goto abort;
    }  

    ParseMsg( message, len, ma );
    
    return len;
    
abort:
    return 0;
}


static int ReadConfig()
{
    DBG( 0, "Reading port files...\n"  );
    char rcbuf[255];
    char section[32];
    FILE * inFile;
    char * tail;

    
    if( ( inFile = fopen(HPIOD_PORT_FILE, "r") ) == NULL ) 
    {
        bug( 0, "unable to open %s: %m\n", HPIOD_PORT_FILE );
        goto bugout;
    } 

    if (fgets(rcbuf, sizeof(rcbuf), inFile) != NULL)
    {
        hpiod_port_num = strtol(rcbuf, &tail, 10);
    }

    fclose(inFile);
    
    if( ( inFile = fopen(HPSSD_PORT_FILE, "r") ) == NULL ) 
    {
        bug( 0, "unable to open %s: %m\n", HPSSD_PORT_FILE );
        goto bugout;
    } 
    if ( fgets(rcbuf, sizeof(rcbuf), inFile) != NULL )
    {
        hpssd_port_num = strtol(rcbuf, &tail, 10);    
    }
    
bugout:
    return 0;
}

#if 0
static int GetLine( char * start, char ** next )
{
    char * p = start;
    int i = 0;
    while( *p != '\0' )
    {
        if( *p == '\n' )
        {
            *p = '\0';
            p++;
            i++;
            break;
        }
        p++;
        i++;
    }
    *next = p;
    return i;
}
#endif

void NumListClear( int * list )
{
    memset( list, 0, sizeof( int ) * MAX_LIST_SIZE );
}

int NumListIsInList( int * list, int n )
{
    int i;
    for( i = 1; i < MAX_LIST_SIZE; i++ )
    {
        if( list[i] == n )
        {
            return 1;
        }
    }
    return 0;
}

int NumListAdd( int * list, int n )
{
    if( NumListIsInList( list, n ) )
    {
        return 1;
    }
    if( list[0] >= ( MAX_LIST_SIZE - 1 ) )
    {
        return 0;
    }
    list[0]++;
    list[list[0]] = n;
    return 1;
}

int NumListGetCount( int * list )
{
    return list[0];
}

int NumListGetFirst( int * list )
{
    int n = list[0];
    if( n > 0 )
    {
        n = list[1];
    }
    return n;
}

void StrListClear( const char ** list )
{
    memset( list, 0, sizeof( char * ) * MAX_LIST_SIZE );
}

int StrListIsInList( const char ** list, char * s )
{
    while( *list )
    {
        if( !strcasecmp( *list, s ) )
        {
            return 1;
        }
        list++;
    }
    return 0;
}

int StrListAdd( const char ** list, char * s )
{
    int i;
    for( i = 0; i < MAX_LIST_SIZE - 1; i++ )
    {
        if( !list[i] )
        {
            list[i] = s;
            return 1;
        }
        if( !strcasecmp( list[i], s ) )
        {
            return 1;
        }
    }
    return 0;
}

int Init( void )
{
    DBG( 0, "Init()\n" );
    
    struct sockaddr_in pin;  
    struct hostent *server_host_name;
    
    ReadConfig();

    server_host_name = gethostbyname( "localhost" );
    bzero( &pin, sizeof(pin) );  
    pin.sin_family = AF_INET;  
    pin.sin_addr.s_addr = ( (struct in_addr *)(server_host_name->h_addr) )->s_addr;  
    pin.sin_port = htons( hpiod_port_num );  
    
    if ( ( hpiod_socket = socket( AF_INET, SOCK_STREAM, 0 ) ) == -1 ) 
    {  
      bug( 0, "Init(): Unable to create hpiod socket.\n" );
      goto abort;  
    }  
    
    if ( connect( hpiod_socket, (void *)&pin, sizeof(pin) ) == -1)  
    {  
      bug( 0, "Init(): Unable to connect hpiod socket.\n" );
      goto abort;  
    }  

    bzero( &pin, sizeof(pin) );  
    pin.sin_family = AF_INET;  
    pin.sin_addr.s_addr = ( (struct in_addr *)(server_host_name->h_addr) )->s_addr;  
    pin.sin_port = htons( hpssd_port_num );  
    
    if ( ( hpssd_socket = socket( AF_INET, SOCK_STREAM, 0 ) ) == -1 ) 
    {  
      bug( 0, "Init(): Unable to create hpssd socket.\n" );
      goto abort;  
    }  

    if ( connect( hpssd_socket, (void *)&pin, sizeof(pin) ) == -1)  
    {  
      bug( 0, "Init(): Unable to connect hpssd socket.\n" );
      goto abort;  
    }  

    inited = 1;
    
    return 1;

abort:
    return 0;
}

int OpenDevice( char * devicename )
{
    DBG( 0, "OpenDevice(%s)\n", devicename );
    char message[ MINSIZE ];
    int len = sprintf(message, "msg=DeviceOpen\ndevice-uri=%s\n", devicename );;
    DBG( 0, "\n>>>\n%s\n", message ); 
    
    MsgAttributes ma;
    
    if( XmitAndParseMessage( message, len, sizeof( message ), &ma ) == 0 )
    {
        goto abort;
    }
   
    DBG( 0, "\n<<<\n%s\n", message ); 

    if (ma.resultcode == R_AOK)
    {
        return ma.deviceid;
    }
    else
    {
abort:
        return -1;
    }
    
}

int GetDeviceID( int deviceid,  char * deviceIDString, int maxlen )
{
    char message[ MAXSIZE ];
    int len = sprintf( message, "msg=DeviceID\ndevice-id=%d\n", deviceid );
    DBG( 0, "\n>>>\n%s\n", message ); 
    
    MsgAttributes ma;
    
    if( XmitAndParseMessage( message, len, sizeof( message ), &ma ) == 0 )
    {
        goto abort;
    }
    
    DBG( 0, "\n<<<\n%s\n", message ); 
    
    if( ma.resultcode == R_AOK )
    {
        strncpy( deviceIDString, ma.data, ma.length ); 
    }
    else
    {
        deviceIDString[0]='\0';
    }
    return ma.length;
abort:
    return ERROR;
}

int GetModel(char *id, char *buf, int bufSize)
{
   char *pMd;
   int i;

   buf[0] = 0;

   if ((pMd = strstr(id, "MDL:")) != NULL)
      pMd+=4;
   else if ((pMd = strstr(id, "MODEL:")) != NULL)
      pMd+=6;
   else
      return 0;

   for (i=0; (pMd[i] != ';') && (i < bufSize); i++)
   {
      if (pMd[i]==' ' || pMd[i]=='/')
         buf[i] = '_';   /* convert space to "_" */
      else
         buf[i] = pMd[i];
   }
   buf[i] = 0;

   return i;
}

int ResetDevices( SANE_Device *** devices )
{
    DBG( 0, "ResetDevices()\n" );
    
    if( *devices != NULL )
    {
        int d = 0;
        
        while( (*devices)[d] != NULL )
        {
            if( ((*devices)[d])->name != NULL )
                free( (void *)((*devices)[d])->name );
            
            if( ((*devices)[d])->model != NULL )
                free( (void *)((*devices)[d])->model );
            
            free( (*devices)[d] );
            
            d++;
        }
        
        free( *devices );
        *devices = NULL;
    }
    
    return OK;
}

int SendScanEvent( char * device_uri, int event, char * type )
{
    char message[ MAXSIZE ];
    MsgAttributes ma;
    memset( message, '\0', MAXSIZE );
    int len = sprintf( message, "msg=Event\ndevice-uri=%s\nevent-code=%d\nevent-type=%s\n", device_uri, event, type );
    DBG( 0, "\n>>>\n%s\n", message ); 

    if ( send( hpssd_socket, message, len, 0 ) == -1 ) 
    {
       bug( 0, "SendScanEvent(): unable to send message: %m\n" );  
    }

    return 0;    
}

int ProbeDevices( SANE_Device *** devices )
{
    char message[ MAXSIZE ];
    MsgAttributes ma;
    memset( message, '\0', MAXSIZE );
    int len = sprintf( message, "msg=ProbeDevicesFiltered\nbus=%s\nfilter=scan\nformat=default\n", "usb" );
    DBG( 0, "\n>>>\n%s\n", message ); 

    if ( send( hpssd_socket, message, len, 0 ) == -1 ) 
    {
       bug( 0, "ProbeDevices(): unable to send message: %m\n" );  
       goto abort;  
    }

    if ( ( len = recv( hpssd_socket, message, MAXSIZE, 0 ) ) == -1 ) 
    {
       bug( 0, "ProbeDevices(): unable to receive result message: %m\n" );  
       goto abort;
    }

    DBG( 0, "\n<<<\n%s\n", message ); 
    
    ParseMsg( message, len, &ma );

    int d = 0;
    char * uri = NULL;
    char * mdl = NULL;
    
    if( ma.numdevices > 0 )
    {
        *devices = malloc( sizeof( SANE_Device * ) * ( ma.numdevices + 1 ) );

        int remaining = ma.length;
        char * p = ma.data;

        int state = 0;

        while( remaining > 0 && *p != '\0' && d < ma.numdevices )
        {
            //DBG( 0, "\n>>>\n%d,%c\n", state, *p );
            
            switch( state )
            {
                case 0:
                {
                    if( *p == ':' )
                    {
                        p++; remaining--;
                        uri = p;
                        state = 1;
                    }        
                    break;
                }

                case 1: 
                {
                    if( *p == ',' )
                    {
                        *p = '\0';
                        state = 2;
                        p++; remaining--;
                        mdl = p;
                    }
                    break;
                }

                case 2:
                {
                    if( *p == '\n' )
                    {
                        *p = '\0';
                        (*devices)[d] = malloc( sizeof( SANE_Device ) );
                        ((*devices)[d])->name = strdup( uri ); // URI w/o hp: 
                        ((*devices)[d])->vendor = "hp";
                        ((*devices)[d])->model = strdup( mdl );
                        ((*devices)[d])->type = "multi-function peripheral";
                        DBG( 0, "\n%s\n", uri );    
                        d++;
                        state = 0;
                        break;
                    }
                }
            } // switch

            p++;
            remaining--;

        } // while
        
        (*devices)[d] = NULL;
        return d;
    }
    else  
    {
        *devices = malloc( sizeof( SANE_Device * ) );
        (*devices)[0] = NULL;
    }

abort:
    return 0;

}

int GetScannerType( SANE_String model )
{
    char message[ MINSIZE ];
    MsgAttributes ma;
    memset( message, '\0', MINSIZE );
    int len = sprintf( message, "msg=ModelQuery\nmodel=%s\n", model );
    DBG( 0, "\n>>>\n%s\n", message ); 

    if ( send( hpssd_socket, message, len, 0 ) == -1 ) 
    {
       bug( 0, "GetScannerType(): unable to send message: %m\n" );  
       goto abort;  
    }

    if ( ( len = recv( hpssd_socket, message, MINSIZE, 0 ) ) == -1 ) 
    {
       bug( 0, "GetScannerType(): unable to receive result message: %m\n" );  
       goto abort;
    }
    
    DBG( 0, "\n<<<\n%s\n", message ); 
    
    ParseMsg( message, len, &ma );

    return ma.scantype;

abort:
    return 0;
}

//GetURIModel
//! Parse the model from a uri string.
/*!
******************************************************************************/
int GetURIModel(char *uri, char *buf, int bufSize)
{
   char *p;
   int i;

   buf[0] = 0;

   if ((p = strstr(uri, "/")) == NULL)
      return 0;
   if ((p = strstr(p+1, "/")) == NULL)
      return 0;
   p++;

   for (i=0; (p[i] != '?') && (i < bufSize); i++)
      buf[i] = p[i];

   buf[i] = 0;

   return i;
}

//ModelQuery
//!  Request ModelQuery from hpssd.
/*!
******************************************************************************/
int ModelQuery(char *devicename, MsgAttributes *ma)
{
   char message[4096];  
   char model[128];
   int len=0,stat=1;

   if (hpssd_socket < 0)
      goto bugout;  

   len = GetURIModel(devicename, model, sizeof(model));

   len = sprintf(message, "msg=ModelQuery\nmodel=%s\n", model);

   if (send(hpssd_socket, message, len, 0) == -1) 
   {  
      bug(0, "unable to send ModelQuery: %m\n");  
      goto bugout;  
   }  

   if ((len = recv(hpssd_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug(0, "unable to receive ModelQueryResult: %m\n");  
      goto bugout;
   }  

   message[len] = 0;

   ParseMsg(message, len, ma);
   stat=0;

bugout:

   return stat;
}

int OpenChannel( int deviceid, char * channelname, char *flow_ctl )
{
    char message[ MINSIZE ];
    int len=0, channel=-1;
    MsgAttributes ma;

   if (flow_ctl[0] == 0)
      len = sprintf(message, "msg=ChannelOpen\ndevice-id=%d\nservice-name=%s\n", deviceid, channelname);
   else
      len = sprintf(message, "msg=ChannelOpen\ndevice-id=%d\nservice-name=%s\nio-control=%s\n", deviceid, channelname, flow_ctl);

    if( XmitAndParseMessage( message, len, sizeof( message ), &ma ) == 0 )
        goto bugout;
    
    if (ma.resultcode == R_AOK)
        channel = ma.channelid;

bugout:

    return channel;    
}


int CloseChannel( int deviceid, int channelid )
{
    char message[ MINSIZE ];
    memset( message, '\0', MINSIZE );
    int len = sprintf( message, "msg=ChannelClose\ndevice-id=%d\nchannel-id=%d\n", deviceid, channelid );
    DBG( 0, "\n>>>\n%s\n", message ); 
    
    MsgAttributes ma;

    if( XmitAndParseMessage( message, len, sizeof( message ), &ma ) == 0 )
    {
        goto abort;
    }
    
    DBG( 0, "\n<<<\n%s\n", message ); 

    if (ma.resultcode == R_AOK)
    {
        return 1;
    }
    else
    {
abort:
        return 0;
    }
}


int ReadChannel( int deviceid, int channelid, unsigned char * buffer, int maxlen, int timeout )
{
    if( timeout == -1 )
        timeout = DEFAULT_CHANNEL_READ_TIMEOUT;
    
    char message[ MAXSIZE ];

    int len = sprintf( message, "msg=ChannelDataIn\ndevice-id=%d\nchannel-id=%d\nbytes-to-read=%d\ntimeout=%d\n", 
                       deviceid, channelid, maxlen, timeout );
    DBG( 0, "\n>>>\n%s\n", message ); 
    
    MsgAttributes ma;

    DBG( 0, "Reading data from channel %d...\n", channelid );

    if( XmitAndParseMessage( message, len, sizeof( message ), &ma ) == 0 )
    {
        goto abort;
    }

    DBG( 0, "\n<<<\nChannelDataInResult\nlength=%d\nresult-code=%d\n", ma.length, ma.resultcode  ); 
    DBG_DUMP( ma.data, ma.length );
    
    if (ma.resultcode == R_AOK)
    {
        if( ma.length > maxlen )
        {
            return -1; 
        }
        
        memcpy( buffer, ma.data, ma.length );
        
        return ma.length;
    }
    else
    {
abort:
        DBG( 0, "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX READ ERROR %d XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n", ma.resultcode );
        return -1;
    }

}

/* Read full requested data length in BUFFER_SIZE chunks. Return number of bytes read. */
int ReadChannelEx(int deviceid, int channelid, unsigned char * buffer, int length, int timeout)
{
   int n, len, size, total=0;

   size = length;

   while(size > 0)
   {
      len = size > BUFFER_SIZE ? BUFFER_SIZE : size;
        
      n = ReadChannel(deviceid, channelid, buffer+total, len, timeout);
      if (n <= 0)
      {
         break;    /* error or timeout */
      }
      size-=n;
      total+=n;
   }
        
   return total;
}

int WriteChannel( int deviceid, int channelid, unsigned char * buffer, int numbytes )
{
    char message[ MAXSIZE ] ;
    int len = sprintf( message, "msg=ChannelDataOut\ndevice-id=%d\nchannel-id=%d\nlength=%d\ndata:\n", deviceid, channelid, numbytes );
    DBG( 0, "\n>>>\n%s\n", message ); 
    DBG_DUMP( buffer, numbytes );

    MsgAttributes ma;
    
    DBG( 0, "Writing data to channel %d...\n", channelid );

    if( numbytes + len > MAXSIZE )
    {
        return 0;
    }
    
    memcpy( message + len, buffer, numbytes );

    if( XmitAndParseMessage( message, len + numbytes, sizeof( message ), &ma ) == 0 )
    {
        goto abort;
    }
    
    DBG( 0, "\n<<<\n%s\n", message ); 
    
    if (ma.resultcode == R_AOK)
    {
        if( ma.byteswritten == numbytes )
        {
            return ma.byteswritten;
        }
        else
        {
            return 0;
        }
    }
    else if( ma.resultcode == R_INVALID_CHANNEL_ID )
    {
        DBG( 0, "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX WRITE ERROR %d XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n", ma.resultcode );
        return -1;
    }
    
    else
    {
abort:
        return 0;
    }

}

int CloseDevice( int deviceid )
{
    char message[ MINSIZE ];
    int len = sprintf(message, "msg=DeviceClose\ndevice-id=%d\n", deviceid );
    DBG( 0, "\n>>>\n%s\n", message ); 
    
    MsgAttributes ma;

    if( XmitAndParseMessage( message, len, sizeof( message ), &ma ) == 0 )
    {
        goto abort;
    }

    DBG( 0, "\n<<<\n%s\n", message ); 
    
    if( !inited )
    {
        bug( 0, "CloseDevice(): not inited, call sane_init() first\n" );
        return SANE_STATUS_INVAL;
    }
    
    if (ma.resultcode == R_AOK)
    {
        return 1;
    }
    else
    {
abort:
        return 0;
    }
    

}

int Exit( void )
{
    inited = 0; 
    
    close( hpiod_socket );
    hpiod_socket = -1;  

    close( hpssd_socket );
    hpssd_socket = -1;
    
    return SANE_STATUS_GOOD;

}

/************************************************************************************/
