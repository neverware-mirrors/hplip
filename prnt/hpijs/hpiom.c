/*****************************************************************************\

  hpiom.c - HP I/O message handler
 
  (c) 2003-2004 Copyright Hewlett-Packard Development Company, LP

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

\*****************************************************************************/

#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include "hpijs.h"
#include "hpiom.h"

static int hpiod_port_num = 50000;
static int hpiod_socket=-1;

static const int gnMaxDataSize = 2048;
static const int gnMaxCmdOptionSize = 4;

static const char gcFrameMarker                    = '$';
static const int  gnPadding                        = 255;
static const int  gnRequiredSize                   = 11;
static const int  gnMinCommandSize                 = 16;
static const int  gnMinDecodeSize                  = 10;   // needed six bytes to determine command number,
                                                    // command length and data length
 
static const int  gUV8FrameOffset                  = 0;
static const int  gUV16CommandLengthOffset         = 1;
static const int  gUV8UnitNumberOffset             = 3;
static const int  gE8PacketTypeOffset              = 4;
static const int  gUV8CommandNumberOffset          = 5;
static const int  gUV16ReferenceNumberOffset       = 6;
static const int  gUV16DataLengthOffset            = 8;
static const int  gUV8CommandOptionsOffset         = 10;

static const int  gUV8RespFrameOffset              = 0;
static const int  gUV16RespCommandLengthOffset     = 1;
static const int  gUV8RespUnitNumberOffset         = 3;
static const int  gE8RespPacketTypeOffset          = 4;
static const int  gUV8RespCommandNumberOffset      = 5;
static const int  gUV16RespReferenceNumberOffset   = 6;
static const int  gUV16RespDataLengthOffset        = 8;
static const int  gE8RespCompleteOffset            = 10;

// reserved reference number
//
static const int gnMinRefNum = 0xF000;
static const int gnMaxRefNum = 0xFFFD;

unsigned short gwSynchRefNum                  = 0xFFEC;
unsigned short gwSynchCompleteRefNum          = 0xFFEB;
unsigned short gwResetRefNum                  = 0xFFEA;
  
unsigned short gwPrinterVersionQueryRefNum      = 0xFFD0;
unsigned short gwPrinterStatusQueryRefNum       = 0xFFD1;
unsigned short gwPrinterAttributesQueryRefNum   = 0xFFD2;
unsigned short gwAlignmentQueryRefNum           = 0xFFD3;
unsigned short gwDeviceIdQueryRefNum            = 0xFFDD;
unsigned short gwHueCompensationQueryRefNum     = 0xFFDE;

// command options
//
// printer query command options
//
static const int  gnPrinterQueryOptionsSize = 4;

static unsigned char gpPrinterVersionQuery[]      = { 0x00, 0x00, 0x00, 0x00 };  //  0 - return UV32 version data
//static unsigned char gpPrinterStatusQuery[]       = { 0x01, 0x00, 0x00, 0x00 };  //  1 - return status string
//static unsigned char gpPrinterAttributesQuery[]   = { 0x02, 0x00, 0x00, 0x00 };  //  2 - return printer attributes
static unsigned char gpAlignmentQuery[]           = { 0x03, 0x00, 0x00, 0x00 };  //  3 - return primitive alignment value
//static unsigned char gpDeviceIdQuery[]            = { 0x0D, 0x00, 0x00, 0x00 };  // 13 - return device id
//static unsigned char gpHueCompensationQuery[]     = { 0x0E, 0x00, 0x00, 0x00 };  // 14 - return hue compensation
static unsigned char gpPenAlignmentQuery[]        = { 0x0F, 0x00, 0x00, 0x00 };  // 15 - return pen alignment value

int GetPair(char *buf, char *key, char *value, char **tail)
{
   int i=0, j;

   key[0] = 0;
   value[0] = 0;

   if (buf[i] == '#')
   {
      for (; buf[i] != '\n' && i < HEADER_SIZE; i++);  /* eat comment line */
      i++;
   }

   if (strncasecmp(&buf[i], "data:", 5) == 0)
   {
      strcpy(key, "data:");   /* "data:" key has no value */
      i+=5;
   }   
   else
   {
      j = 0;
      while ((buf[i] != '=') && (i < HEADER_SIZE) && (j < LINE_SIZE))
         key[j++] = buf[i++];
      for (j--; key[j] == ' ' && j > 0; j--);  /* eat white space before = */
      key[++j] = 0;

      for (i++; buf[i] == ' ' && i < HEADER_SIZE; i++);  /* eat white space after = */

      j = 0;
      while ((buf[i] != '\n') && (i < HEADER_SIZE) && (j < LINE_SIZE))
         value[j++] = buf[i++];
      for (j--; value[j] == ' ' && j > 0; j--);  /* eat white space before \n */
      value[++j] = 0;
   }

   i++;   /* bump past '\n' */

   if (tail != NULL)
      *tail = buf + i;  /* tail points to next line */

   return i;
}

int ReadConfig()
{
   char rcbuf[255];
   FILE *inFile;
   char *tail;
        
   if((inFile = fopen(HPIODFILE, "r")) == NULL) 
   {
      bug("unable to open %s: %m\n", HPIODFILE);
      return 1;
   } 
   if (fgets(rcbuf, sizeof(rcbuf), inFile) != NULL)
      hpiod_port_num = strtol(rcbuf, &tail, 10);
   fclose(inFile);
         
   return 0;
}

//System::ParseMsg
//!  Parse and convert all key value pairs in message. Do sanity check on values.
/*!
******************************************************************************/
int ParseMsg(char *buf, int len, MsgAttributes *ma)
{
   char key[LINE_SIZE];
   char value[LINE_SIZE];
   char *tail, *tail2;
   int i, ret=R_AOK;

   ma->cmd[0] = 0;
   ma->descriptor = -1;
   ma->length = 0;
   ma->channel = -1;
   ma->data = NULL;
   ma->result = -1;
   ma->writelen = 0;
   ma->readlen = 0;
   ma->status = 0;

   i = GetPair(buf, key, value, &tail);
   if (strcasecmp(key, "msg") != 0)
   {
      bug("invalid message:%s\n", key);
      return R_INVALID_MESSAGE;
   }
   strncpy(ma->cmd, value, sizeof(ma->cmd));

   while (i < len)
   {
      i += GetPair(tail, key, value, &tail);

      if (strcasecmp(key, "device-id") == 0)
      {
         ma->descriptor = strtol(value, &tail2, 10);
         if (ma->descriptor < 0)
         {
            bug("invalid device descriptor:%d\n", ma->descriptor);
            ret = R_INVALID_DESCRIPTOR;
            break;
         }
      }
      else if (strcasecmp(key, "channel-id") == 0)
      {
         ma->channel = strtol(value, &tail2, 10);
         if (ma->channel < 0)
         {
            bug("invalid channel descriptor:%d\n", ma->channel);
            ret = R_INVALID_CHANNEL_ID;
            break;
         }
      }
      else if (strcasecmp(key, "length") == 0)
      {
         ma->length = strtol(value, &tail2, 10);
         if (ma->length > BUFFER_SIZE)
         {
            bug("invalid data length:%d\n", ma->length);
            ret = R_INVALID_LENGTH;
         }
      }
      else if (strcasecmp(key, "data:") == 0)
      {
         ma->data = (unsigned char *)tail;
         break;  /* done parsing */
      }
      else if (strcasecmp(key, "result-code") == 0)
      {
         ma->result = strtol(value, &tail2, 10);
      }
      else if (strcasecmp(key, "bytes-written") == 0)
      {
         ma->writelen = strtol(value, &tail2, 10);
      }
      else if (strcasecmp(key, "bytes-to-read") == 0)
      {
         ma->readlen = strtol(value, &tail2, 10);
         if (ma->readlen > BUFFER_SIZE)
         {
            bug("invalid read length:%d\n", ma->readlen);
            ret = R_INVALID_LENGTH;
         }
      }
      else if (strcasecmp(key, "status-code") == 0)
      {
         ma->status = strtol(value, &tail2, 10);
      }
      else if (strcasecmp(key, "status-name") == 0)
      {
         continue; /* ignor */
      }
      else if (strcasecmp(key, "encoding") == 0)
      {
         continue; /* ignor */
      }
      else
      {
         /* Unknown keys are ignored (R_AOK). */
//         bug("invalid key:%s\n", key);
      }
   }  // end while (i < len)

   return ret;
}

int OpenHP(char *dev)
{
   char message[512];  
   struct sockaddr_in pin;  
   int len=0, fd=-1;
   MsgAttributes ma;

   ReadConfig();
 
   bzero(&pin, sizeof(pin));  
   pin.sin_family = AF_INET;  
   pin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
   pin.sin_port = htons(hpiod_port_num);  
 
   if ((hpiod_socket = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
   {  
      bug("unable to open socket %d: %m\n", hpiod_port_num);  
      goto mordor;  
   }  
 
   if (connect(hpiod_socket, (void *)&pin, sizeof(pin)) == -1) 
   {  
      bug("unable to connect to socket %d: %m\n", hpiod_port_num);  
      goto mordor;  
   }  

   len = sprintf(message, "msg=DeviceOpen\ndevice-uri=%s\n", dev);
 
   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      bug("unable to send DeviceOpen: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive DeviceOpenResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

   ParseMsg(message, len, &ma);
   if (ma.result == R_AOK)
      fd = ma.descriptor;

mordor:

   return fd;
}

int CloseHP(int hd)
{
   char message[512];  
   int len=0;
 
   len = sprintf(message, "msg=DeviceClose\ndevice-id=%d\n", hd);
 
   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      bug("unable to send DeviceClose: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive DeviceCloseResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

mordor:
   close(hpiod_socket);
   hpiod_socket = -1;  

   return 0;
}

/* Get device id string. Assume binary length value at begining of string has been removed. */
int ReadHPDeviceID(int hd, char *buf, int bufSize)
{
   char message[512];  
   int len=0;  
   MsgAttributes ma;
 
   buf[0] = 0;

   len = sprintf(message, "msg=DeviceID\ndevice-id=%d\n", hd);
 
   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      bug("unable to send DeviceID: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, buf, bufSize, 0)) == -1) 
   {  
      bug("unable to receive DeviceIDResult: %m\n");  
      goto mordor;
   }  

   buf[len] = 0;

   ParseMsg(buf, len, &ma);
   if (ma.result == R_AOK)
   {
      len = ma.length;
      memcpy(buf, ma.data, len);
   }
   else
      len = 0;   /* error */

mordor:

   return len;
}  
 
int ReadHPStatus(int hd, char *buf, int size)
{
   char message[512];  
   int len=0;  
   MsgAttributes ma;
 
   buf[0] = 0;

   len = sprintf(message, "msg=DeviceStatus\ndevice-id=%d\n", hd);
 
   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      bug("unable to send DeviceStatus: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive DeviceStatusResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

   ParseMsg(message, len, &ma);
   if (ma.result == R_AOK)
   {
      len = 1;
      buf[0] = ma.status;
   }
   else
      len = 0;   /* error */

mordor:

   return len;
}  

int WriteHP(int hd, int channel, char *buf, int size)
{
   char message[BUFFER_SIZE+HEADER_SIZE];  
   int len=0, slen=0;
   MsgAttributes ma;
 
   len = sprintf(message, "msg=ChannelDataOut\ndevice-id=%d\nchannel-id=%d\nlength=%d\ndata:\n", hd, channel, size);
   if (size+len > sizeof(message))
   {  
      bug("unable to fill data buffer: size=%d\n", size);  
      goto mordor;  
   }  

   memcpy(message+len, buf, size);
  
   if (send(hpiod_socket, message, size+len, 0) == -1) 
   {  
      bug("unable to send ChannelDataOut: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive ChannelDataOutResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;
   ParseMsg(message, len, &ma);

   slen = ma.writelen;

mordor:

   return slen;
}

int ReadHP(int hd, int channel, char *buf, int size)
{
   char message[BUFFER_SIZE+HEADER_SIZE];  
   int len=0, rlen=0;
   MsgAttributes ma;
 
   len = sprintf(message, "msg=ChannelDataIn\ndevice-id=%d\nchannel-id=%d\nbytes-to-read=%d\n", hd, channel, size);
   if (size+len > sizeof(message))
   {  
      fprintf(stderr, "Error data size=%d\n", size);  
      goto mordor;  
   }  

   if (send(hpiod_socket, message, size+len, 0) == -1) 
   {  
      bug("unable to send ChannelDataIn: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive ChannelDataInResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

   ParseMsg(message, len, &ma);

   if (ma.result == 0)
   {  
      rlen = ma.length;
      memcpy(buf, ma.data, rlen);
   }

mordor:

   return rlen;
}

int OpenChannel(int hd, char *sn)
{
   char message[512];  
   int len=0, channel=-1;
   MsgAttributes ma;

   len = sprintf(message, "msg=ChannelOpen\ndevice-id=%d\nservice-name=%s\n", hd, sn);

   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      bug("unable to send ChannelOpen: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive ChannelOpenResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

   ParseMsg(message, len, &ma);
   if (ma.result == R_AOK)
      channel = ma.channel;

mordor:

   return channel;
}

int CloseChannel(int hd, int channel)
{
   char message[512];  
   int len=0;

   len = sprintf(message, "msg=ChannelClose\ndevice-id=%d\nchannel-id=%d\n", hd, channel);
 
   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      bug("unable to send ChannelClose: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive ChannelCloseResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

mordor:

   return 0;
}

/*
 * Lidil commands.
 */

int EncodeCommand
(
   unsigned char *lpBuffer,
   unsigned short wBufferSize,
   unsigned char unUnitNumber,
   int ePacketType,
   int eCommandNumber,
   char *lpData,
   unsigned short wDataLength,
   unsigned char *lpCommandOptions,
   unsigned short wCommandOptionsSize,
   int *dPacketSize,
   unsigned short wRefNum
)
{
   int x;
   int lNumPaddingNeeded = 0;
   unsigned char *lpTemp = NULL;

   memset( lpBuffer, 0, wBufferSize );
   lpBuffer [ gUV8FrameOffset ]         = gcFrameMarker;
   lpBuffer [ gUV8UnitNumberOffset ]    = unUnitNumber;
   lpBuffer [ gE8PacketTypeOffset ]     = ePacketType;
   lpBuffer [ gUV8CommandNumberOffset ] = eCommandNumber;
   *(short *)(lpBuffer + gUV16DataLengthOffset) = htons(wDataLength);

   if ( wCommandOptionsSize > 0 )
   {   
      if ( lpCommandOptions )
      {
         // copy command options to the buffer
         memcpy(( lpBuffer + gUV8CommandOptionsOffset ), lpCommandOptions, wCommandOptionsSize);
      }
      else
      {
         // command option is null, fill the buffer with zeros
         memset(( lpBuffer + gUV8CommandOptionsOffset ), 0, wCommandOptionsSize );
      }
   }

   // calculate command length and padding if needed
   *dPacketSize = gnRequiredSize + wCommandOptionsSize;
   lNumPaddingNeeded = gnMinCommandSize - *dPacketSize;

   if ( lNumPaddingNeeded > 0 )
   {
      // move the pointer to the beginning of the padding
      lpTemp = lpBuffer + gUV8CommandOptionsOffset + wCommandOptionsSize;

      for (x = 0; x < lNumPaddingNeeded; x++, lpTemp++ )
      {
         *lpTemp = gnPadding;
      }
            
      *dPacketSize = gnMinCommandSize;
   }

   *(short *)(lpBuffer + gUV16CommandLengthOffset) = htons(*dPacketSize);
   *(short *)(lpBuffer + gUV16ReferenceNumberOffset) = htons(wRefNum ? wRefNum : 1);

   // add the trailing frame marker
   lpBuffer[ *dPacketSize - 1 ] = gcFrameMarker;

   if ( wDataLength )
   {            
      if ((*dPacketSize + wDataLength) > wBufferSize)
      {
          bug("unable to fill data buffer EncodeCommand size=%d\n", wDataLength);
          return 1;
      }   

      if ( lpData )
      {
          // copy the data to the end of the command
          memcpy( lpBuffer + *dPacketSize, lpData, wDataLength );
      }
      else
      {
          // NULL data pointer, fill the buffer with zeros
          memset( lpBuffer + *dPacketSize, 0, wDataLength );
      }

      *dPacketSize += wDataLength;
   }

   return 0;
}

int Synch(int hd, int chan)
{
    int bRet = 0;
    int dPacketSize = 0;
    unsigned char buf[4096];

    // create the Synch command, send it to the device, 
    // and retrieve absolute credit data from the device.
    EncodeCommand(buf, sizeof(buf)
                     , 0            
                     , eSynch
                     , eCommandUnknown
                     , NULL
                     , gnMaxDataSize
                     , NULL
                     , gnMaxCmdOptionSize
                     , &dPacketSize
                     , gwSynchRefNum
                     );

    bRet = WriteHP(hd, chan, (char *)buf, dPacketSize );

    return( bRet );
}

int SynchComplete(int hd, int chan)
{
    int bRet = 0;
    int dPacketSize = 0;
    unsigned char buf[32];

        // create the SynchComplete command, send it to the device, 
        // and retrieve absolute credit data from the device.
        EncodeCommand(buf, sizeof(buf)
                     , 0            
                     , eSynchComplete
                     , eCommandUnknown
                     , NULL
                     , 0
                     , NULL
                     , 0
                     , &dPacketSize
                     , gwSynchCompleteRefNum
                     );

    bRet = WriteHP(hd, chan, (char *)buf, dPacketSize );

    return( bRet );
}

int Reset(int hd, int chan)
{
    int bRet = 0;
    int dPacketSize = 0;
    unsigned char buf[32];

        // create the Reset command, send it to the device, 
        // and retrieve absolute credit data from the device.
        //
        EncodeCommand(buf, sizeof(buf)
                     , 0            
                     , eResetLidil
                     , eCommandUnknown
                     , NULL
                     , 0
                     , NULL
                     , 0
                     , &dPacketSize
                     , gwResetRefNum
                     );

        bRet = WriteHP(hd, chan, (char *)buf, dPacketSize );

    return( bRet );
}

int RetrieveAlignmentValues038(int hd, int chan, LDLGenAlign *pG)
{
   int n;
   int dPacketSize = 0;
   unsigned char buf[256];
   LDLResponseAlign038 *pA;

   /* Enable responses. */
   EncodeCommand(buf, sizeof(buf)
                     , 0
                     , eEnableResponses
                     , eCommandUnknown
                     , NULL
                     , 0
                     , NULL
                     , 0
                     , &dPacketSize
                     , 0
                     );
   n = WriteHP(hd, chan, (char *)buf, dPacketSize );

   /* Write alignment query. */
   EncodeCommand(buf, sizeof(buf)
                     , 0             // device 0
                     , eCommand
                     , eQuery
                     , NULL
                     , 0
                     , gpAlignmentQuery
                     , gnPrinterQueryOptionsSize  
                     , &dPacketSize
                     , gwAlignmentQueryRefNum
                     );
   n = WriteHP(hd, chan, (char *)buf, dPacketSize );

   /* Disable responses. */
   EncodeCommand(buf, sizeof(buf)
                     , 0
                     , eDiableResponses
                     , eCommandUnknown
                     , NULL
                     , 0
                     , NULL
                     , 0
                     , &dPacketSize
                     , 0
                     );
   n = WriteHP(hd, chan, (char *)buf, dPacketSize );
 
   /* Read query response. */
   n = ReadHP(hd, chan, (char *)buf, sizeof(buf));
   pA = (LDLResponseAlign038 *)buf;
   memset(pG, 0, sizeof(LDLGenAlign));
   if (pA->h.packet_type == 16)
   {
      pG->nPens = 2;
      /* Except for bi, convert values from relative to black pen to relative to color. */
      pG->pen[0].color = 0;
      pG->pen[0].vert = -pA->c[0];
      pG->pen[0].horz = -pA->c[1];
      pG->pen[0].bi = pA->k[2];
      pG->pen[1].color = 1;
      pG->pen[1].vert = pA->k[0];
      pG->pen[1].horz = pA->k[1];
      pG->pen[1].bi = pA->c[2];
   }

   return 0;
}

int RetrieveAlignmentValues043(int hd, int chan, LDLGenAlign *pG)
{
   int n=0;
   int dPacketSize = 0;
   unsigned char buf[256];
   LDLResponseAlign043 *pA;

   /* Enable responses. */
   EncodeCommand(buf, sizeof(buf)
                     , 0
                     , eEnableResponses
                     , eCommandUnknown
                     , NULL
                     , 0
                     , NULL
                     , 0
                     , &dPacketSize
                     , 0
                     );
   n = WriteHP(hd, chan, (char *)buf, dPacketSize );

   /* Write alignment query. */
   EncodeCommand(buf, sizeof(buf)
                     , 0             // device 0
                     , eCommand
                     , eQuery
                     , NULL
                     , 0
                     , gpPenAlignmentQuery 
                     , gnPrinterQueryOptionsSize  
                     , &dPacketSize
                     , gwAlignmentQueryRefNum
                     );
   n = WriteHP(hd, chan, (char *)buf, dPacketSize );

   /* Disable responses. */
   EncodeCommand(buf, sizeof(buf)
                     , 0
                     , eDiableResponses
                     , eCommandUnknown
                     , NULL
                     , 0
                     , NULL
                     , 0
                     , &dPacketSize
                     , 0
                     );
   n = WriteHP(hd, chan, (char *)buf, dPacketSize );

   n = ReadHP(hd, chan, (char *)buf, sizeof(buf));
   pA = (LDLResponseAlign043 *)buf;
   memset(pG, 0, sizeof(LDLGenAlign));
   if (pA->h.packet_type == 16)
   {
      memcpy(pG, &pA->g, sizeof(LDLGenAlign));
   }

   return 0;
}

uint32_t RetrieveVersion(int hd, int chan)
{
   int n, version=0;
   int dPacketSize = 0;
   unsigned char buf[256];
   LDLResponseVersion *pV;

   /* Enable responses. */
   EncodeCommand(buf, sizeof(buf)
                     , 0
                     , eEnableResponses
                     , eCommandUnknown
                     , NULL
                     , 0
                     , NULL
                     , 0
                     , &dPacketSize
                     , 0
                     );
   n = WriteHP(hd, chan, (char *)buf, dPacketSize );

   /* Write lidil version query. */
   EncodeCommand(buf, sizeof(buf)
                     , 0             // device 0
                     , eCommand
                     , eQuery
                     , NULL
                     , 0
                     , gpPrinterVersionQuery
                     , gnPrinterQueryOptionsSize  
                     , &dPacketSize
                     , gwAlignmentQueryRefNum
                     );
   n = WriteHP(hd, chan,(char *)buf, dPacketSize );

   /* Disable responses. */
   EncodeCommand(buf, sizeof(buf)
                     , 0
                     , eDiableResponses
                     , eCommandUnknown
                     , NULL
                     , 0
                     , NULL
                     , 0
                     , &dPacketSize
                     , 0
                     );
   n = WriteHP(hd, chan, (char *)buf, dPacketSize );

        n = ReadHP(hd, chan, (char *)buf, sizeof(buf));
        pV = (LDLResponseVersion *)buf;
        if (pV->h.packet_type == 16)
        {
           version = ntohl(pV->ldlversion);
           fprintf(stdout, "lidil version = %x\n", version);
        }

    return(version);
}

/*
 * Return value = (black | photo) to color vertical alignment offset, error = -1.
 *
 * All alignment values may be zero if pen(s) were never aligned. Valid values
 * may range from -30 to +30.
 */
int ReadHPVertAlign(int hd)
{
   int channel, n, i, x2colorVert=-1;
   uint32_t ver;
   LDLGenAlign ga;

   if ((channel = OpenChannel(hd, "PRINT")) < 0)
   {
      bug("unable to open print channel ReadHPVertAlign\n");
      goto bugout;
   }

   if (Synch(hd, channel)==0)
   {  
      bug("unable to write sync ReadHPVertAlign\n");  
      goto bugout;  
   }  

   if (SynchComplete(hd, channel)==0)
   {  
      bug("unable to write sync complete ReadHPVertAlign\n");  
      goto bugout;  
   }  

   if (Reset(hd, channel)==0)
   {  
      bug("unable to write reset ReadHPVertAlign\n");  
      goto bugout;  
   }  

   if ((ver = RetrieveVersion(hd, channel))==0)
   {  
      bug("unable to read version ReadHPVertAlign\n");  
      goto bugout;  
   }  

   if (ver > 0x308)
      RetrieveAlignmentValues043(hd, channel, &ga);
   else 
      RetrieveAlignmentValues038(hd, channel, &ga);

   if (!(n = ga.nPens))
      goto bugout;

   for (i=0; i<n; i++)
   {
      if (ga.pen[i].color == 0 || ga.pen[i].color == 2)
      {
         x2colorVert = ga.pen[i].vert;  /* (black | photo) to color offset */
         bug("%s alignment: vert=%d horz=%d bi=%d x2c=%d\n", (ga.pen[i].color==0) ? "black" : "photo", ga.pen[i].vert, ga.pen[i].horz, ga.pen[i].bi, x2colorVert);
      }
   }

   Reset(hd, channel);

bugout: 
   if (channel >= 0)
      CloseChannel(hd, channel);

   return x2colorVert;
}



