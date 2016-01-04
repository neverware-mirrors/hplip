/************************************************************************************\

  system.h - HP SANE backend for multi-function peripherals (libsane-hpaio)

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

#if !defined( __SYSTEM_H__ )
#define __SYSTEM_H__

#include <stdio.h>
#include <stdarg.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <syslog.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <linux/lp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <ctype.h>

#include "sane.h"

// Uncomment the following line to get verbose debugging output
//#define HPAIO_DEBUG

#define BREAKPOINT __asm( "int3" )

#define MAXSIZE 16384
#define MINSIZE 512
#define ERROR 0
#define OK 1
#define LINE_SIZE 256
#define BUFFER_SIZE 8192
#define MAX_LIST_SIZE 32
#define RCFILE "/etc/hp/hplip.conf"
#define DEFAULT_CHANNEL_READ_TIMEOUT 60


typedef struct
{
   char cmd[LINE_SIZE];
   char flow_ctl[32];
   int deviceid; 
   int channelid; 
   int length;
   int resultcode;
   int byteswritten;
   int numdevices;
   int scantype;
   unsigned char *data;
} MsgAttributes;

enum RESULT_CODE
{
   R_AOK = 0,
   R_INVALID_DESCRIPTOR = 3,
   R_INVALID_URI = 4,
   R_INVALID_MESSAGE = 5,
   R_INVALID_LENGTH = 8,
   R_IO_ERROR = 12,
   R_INVALID_CHANNEL_ID = 30,
   R_CHANNEL_BUSY = 31,
};

#define BEND_GET_SHORT(s) (((s)[0]<<8)|((s)[1]))
#define BEND_GET_LONG(s) (((s)[0]<<24)|((s)[1]<<16)|((s)[2]<<8)|((s)[3]))
#define BEND_SET_SHORT(s,x) ((s)[0]=((x)>>8)&0xFF,(s)[1]=(x)&0xFF)
#define BEND_SET_LONG(s,x) ((s)[0]=((x)>>24)&0xFF,(s)[1]=((x)>>16)&0xFF,(s)[2]=((x)>>8)&0xFF,(s)[3]=(x)&0xFF)
#define LEND_GET_SHORT(s) (((s)[1]<<8)|((s)[0]))
#define LEND_GET_LONG(s) (((s)[3]<<24)|((s)[2]<<16)|((s)[1]<<8)|((s)[0]))
#define LEND_SET_SHORT(s,x) ((s)[1]=((x)>>8)&0xFF,(s)[0]=(x)&0xFF)
#define LEND_SET_LONG(s,x) ((s)[3]=((x)>>24)&0xFF,(s)[2]=((x)>>16)&0xFF,(s)[1]=((x)>>8)&0xFF,(s)[0]=(x)&0xFF)

void DBG(int level, const char *format, ...);
void DBG_DUMP( void *data, int size );
int bug(int level, const char *fmt, ...);

unsigned long DivideAndShift( int line,
                              unsigned long numerator1,
                              unsigned long numerator2,
                              unsigned long denominator,
                              int shift );

void NumListClear( int * list );

int NumListIsInList( int * list, int n );

int NumListAdd( int * list, int n );

int NumListGetCount( int * list );

int NumListGetFirst( int * list );

void StrListClear( const char ** list );

int StrListIsInList( const char ** list, char * s );

int StrListAdd( const char ** list, char * s );

int Init( void );

int ResetDevices( SANE_Device *** devices );

int SendScanEvent( char * device_uri, int event, char * type );

int ProbeDevices( SANE_Device *** devices );

int GetScannerType( SANE_String model );

int OpenDevice( char * devicename );

int GetDeviceID( int deviceid,  char * deviceIDString, int maxlen );

int GetModel(char *id, char *buf, int bufSize);

int OpenChannel( int deviceid, char * channelname, char * flow_ctl ); 

int CloseChannel( int deviceid, int channelid );

int ReadChannel( int deviceid, int channelid, unsigned char * buffer, int maxlen, int timeout );

int ReadChannelEx( int deviceid, int channelid, unsigned char * buffer, int countdown, int timeout );

int WriteChannel( int deviceid, int channelid, unsigned char * buffer, int numbytes );

int CloseDevice( int deviceid );

int Exit( void );


#endif


