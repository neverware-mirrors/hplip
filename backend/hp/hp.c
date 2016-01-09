/*****************************************************************************\

  hp.c - hp cups backend 
 
  (c) 2004 Copyright Hewlett-Packard Development Company, LP

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
#include <stdarg.h>
#include <syslog.h>

#define RCFILE "/etc/hp/hplip.conf" /* The config file */
#define HPIODFILE "/var/run/hpiod.port"
#define HPSSDFILE "/var/run/hpssd.port"

#define LINE_SIZE 256 /* Length of buffer reads */
#define BUFFER_SIZE 4096
//#define HEADER_SIZE 256   /* Rough estimate for message header */
#define HEADER_SIZE 4096   /* Rough estimate for message header */
#define RETRY_TIMEOUT 30  /* seconds */

#define NFAULT_BIT  0x08
#define PERROR_BIT  0x20

#define OOP             (NFAULT_BIT | PERROR_BIT)
#define JAMMED          (PERROR_BIT)
#define ERROR_TRAP      (0)

#define STATUS_MASK (NFAULT_BIT | PERROR_BIT)

#define DEVICE_IS_OOP(reg)  ((reg & STATUS_MASK) == OOP)
#define DEVICE_PAPER_JAMMED(reg)  ((reg & STATUS_MASK) == JAMMED)
#define DEVICE_IO_TRAP(reg)       ((reg & STATUS_MASK) == ERROR_TRAP)

#define HEX2INT(x, i) if (x >= '0' && x <= '9')      i |= x - '0'; \
                       else if (x >= 'A' && x <= 'F') i |= 0xA + x - 'A'; \
                       else if (x >= 'a' && x <= 'f') i |= 0xA + x - 'a'

/* Actual vstatus codes are mapped to 1000+vstatus for DeviceError messages. */ 
typedef enum
{
   VSTATUS_IDLE = 1000,
   VSTATUS_BUSY,
   VSTATUS_PRNT,      /* io printing */
   VSTATUS_OFFF,      /* turning off */
   VSTATUS_RPRT,      /* report printing */
   VSTATUS_CNCL,      /* canceling */
   VSTATUS_IOST,      /* io stall */
   VSTATUS_DRYW,      /* dry time wait */
   VSTATUS_PENC,      /* pen change */
   VSTATUS_OOPA,      /* out of paper */
   VSTATUS_BNEJ,      /* banner eject needed */
   VSTATUS_BNMZ,      /* banner mismatch */
   VSTATUS_PHMZ,      /* photo mismatch */
   VSTATUS_DPMZ,      /* duplex mismatch */
   VSTATUS_PAJM,      /* media jam */
   VSTATUS_CARS,      /* carriage stall */
   VSTATUS_PAPS,      /* paper stall */
   VSTATUS_PENF,      /* pen failure */
   VSTATUS_ERRO,      /* hard error */
   VSTATUS_PWDN,      /* power down */
   VSTATUS_FPTS,      /* front panel test */
   VSTATUS_CLNO       /* clean out tray missing */
} VSTATUS;


#define EVENT_START_JOB 500
#define EVENT_END_JOB 501

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

enum SESSION_STATE
{
   SESSION_NORMAL = 0,
   SESSION_START,
   SESSION_END
};

typedef struct
{
   char cmd[LINE_SIZE];
   char io_mode[32];
   char flow_ctl[32];
   int descriptor;       /* device descriptor (device-id) */
   int length;           /* length of data in bytes */
   int result;
   int channel;          /* channel descriptor (channel-id) */
   int writelen;           /* bytes-written */
   int readlen;   /* bytes-to-read */
   unsigned char status;   /* 8-bit device status */
   unsigned char *data;           /* pointer to data */
} MsgAttributes;

static int hpiod_port_num = 50000;
static int hpssd_port_num = 50002;
static int hpiod_socket=-1;
static int hpssd_socket=-1;
static int jdprobe=0;

int bug(const char *fmt, ...)
{
   char buf[256];
   va_list args;
   int n;

   va_start(args, fmt);

   if ((n = vsnprintf(buf, 256, fmt, args)) == -1)
      buf[255] = 0;     /* output was truncated */

   fprintf(stderr, buf);
   syslog(LOG_WARNING, buf);

   fflush(stderr);
   va_end(args);
   return n;
}

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
   ma->io_mode[0] = 0;
   ma->flow_ctl[0] = 0;
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
      else if (strcasecmp(key, "io-mode") == 0)
      {
         strncpy(ma->io_mode, value, sizeof(ma->io_mode));
      }
      else if (strcasecmp(key, "io-control") == 0)
      {
         strncpy(ma->flow_ctl, value, sizeof(ma->flow_ctl));
      }
      else
      {
         /* Unknown keys are ignored (R_AOK). */
//         bug("invalid key:%s\n", key);
      }
   }  // end while (i < len)

   return ret;
}

int ReadConfig()
{
   char rcbuf[255];
   char section[32];
   FILE *inFile = NULL;
   char *tail;
   int stat=1;
        
   if((inFile = fopen(RCFILE, "r")) == NULL) 
   {
      bug("unable to open %s: %m\n", RCFILE);
      goto bugout;
   } 

   section[0] = 0;

   /* Read the config file */
   while ((fgets(rcbuf, sizeof(rcbuf), inFile) != NULL))
   {
      if (rcbuf[0] == '[')
         strncpy(section, rcbuf, sizeof(section)); /* found new section */
      else if ((strncasecmp(section, "[hplip]", 7) == 0) && (strncasecmp(rcbuf, "jdprobe=", 8) == 0))
         jdprobe = strtol(rcbuf+8, &tail, 10);
   }
        
   fclose(inFile);

   if((inFile = fopen(HPIODFILE, "r")) == NULL) 
   {
      bug("unable to open %s: %m\n", HPIODFILE);
      goto bugout;
   } 
   if (fgets(rcbuf, sizeof(rcbuf), inFile) != NULL)
      hpiod_port_num = strtol(rcbuf, &tail, 10);
   fclose(inFile);

   if((inFile = fopen(HPSSDFILE, "r")) == NULL) 
   {
      bug("unable to open %s: %m\n", HPSSDFILE);
      goto bugout;
   } 
   if (fgets(rcbuf, sizeof(rcbuf), inFile) != NULL)
      hpssd_port_num = strtol(rcbuf, &tail, 10);

   stat = 0;

bugout:        
   if (inFile != NULL)
      fclose(inFile);
         
   return stat;
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
int ModelQuery(char *uri, MsgAttributes *ma)
{
   char message[HEADER_SIZE];  
   char model[128];
   int len=0,stat=1;

   if (hpssd_socket < 0)
      goto bugout;  

   len = GetURIModel(uri, model, sizeof(model));

   len = sprintf(message, "msg=ModelQuery\nmodel=%s\n", model);

   if (send(hpssd_socket, message, len, 0) == -1) 
   {  
      bug("unable to send ModelQuery: %m\n");  
      goto bugout;  
   }  

   if ((len = recv(hpssd_socket, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive ModelQueryResult: %m\n");  
      goto bugout;
   }  

   message[len] = 0;

   ParseMsg(message, len, ma);
   stat=0;

bugout:

   return stat;
}

int OpenHP(char *dev)
{
   char message[512];  
   struct sockaddr_in pin;  
   int len=0, fd=-1;
   MsgAttributes ma;
 
   bzero(&pin, sizeof(pin));  
   pin.sin_family = AF_INET;  
   pin.sin_addr.s_addr =  htonl(INADDR_LOOPBACK);
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

int OpenChannel(int hd, char *sn, char *uri, char *io_mode, char *flow_ctl)
{
   char message[512];  
   int len=0, channel=-1;
   MsgAttributes ma;

   if (strcasecmp(io_mode, "mlc") == 0)
   {
      if (flow_ctl[0] == 0)
         len = sprintf(message, "msg=ChannelOpen\ndevice-id=%d\nservice-name=%s\nio-mode=%s\n", hd, sn, io_mode);
      else
         len = sprintf(message, "msg=ChannelOpen\ndevice-id=%d\nservice-name=%s\nio-mode=%s\nio-control=%s\n", hd, sn, io_mode, flow_ctl);
   }
   else
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
int GetID(int hd, char *buf, int bufSize)
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
 
int GetStatus(int hd, char *buf, int size)
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

const char *GetVStatusMessage(VSTATUS status)
{
   char *p;

   /* Map VStatus to text message. TODO: text needs to be localized. */
   switch(status)
   {
      case(VSTATUS_IDLE):
         p = "ready to print";
         break;
      case(VSTATUS_BUSY):
         p = "busy";
         break;
      case(VSTATUS_PRNT):
         p = "i/o printing";
         break;
      case(VSTATUS_OFFF):
         p = "turning off";
         break;
      case(VSTATUS_RPRT):
         p = "report printing";
         break;
      case(VSTATUS_CNCL):
         p = "canceling";
         break;
      case(VSTATUS_IOST):
         p = "incomplete job";
         break;
      case(VSTATUS_DRYW):
         p = "dry time wait";
         break;
      case(VSTATUS_PENC):
         p = "pen change";
         break;
      case(VSTATUS_OOPA):
         p = "out of paper";
         break;
      case(VSTATUS_BNEJ):
         p = "banner eject needed";
         break;
      case(VSTATUS_BNMZ):
         p = "banner mismatch";
         break;
      case(VSTATUS_DPMZ):
         p = "duplex mismatch";
         break;
      case(VSTATUS_PAJM):
         p = "media jam";
         break;
      case(VSTATUS_CARS):
         p = "carriage stall";
         break;
      case(VSTATUS_PAPS):
         p = "paper stall";
         break;
      case(VSTATUS_PENF):
         p = "pen failure";
         break;
      case(VSTATUS_ERRO):
         p = "hard error";
         break;
      case(VSTATUS_PWDN):
         p = "power down";
         break;
      case(VSTATUS_FPTS):
         p = "front panel test";
         break;
      case(VSTATUS_CLNO):
         p = "clean out tray missing";
         break;
      case(5000+R_IO_ERROR):
         p = "check device";
         break;
      default:
         p = "unknown state";
         bug("INFO: printer state=%d\n", status);
         break;
   }
   return p;
}

int GetVStatus(int hd)
{
   char id[1024];
   char *pSf;
   int vstatus=VSTATUS_IDLE, ver;

   if (GetID(hd, id, sizeof(id)) == 0)
   {
      vstatus = 5000+R_IO_ERROR;      /* no deviceid, return some error */
      goto bugout;
   }
   
   /* Check for valid S-field in device id string. */
   if ((pSf = strstr(id, ";S:")) == NULL)
   {
      /* No S-field, use status register instead of device id. */ 
      unsigned char status;
      GetStatus(hd, &status, 1);      
      if (DEVICE_IS_OOP(status))
         vstatus = VSTATUS_OOPA;
      else if (DEVICE_PAPER_JAMMED(status))
         vstatus = VSTATUS_PAJM;
      else if (DEVICE_IO_TRAP(status))
         vstatus = VSTATUS_CARS;
      else
         vstatus = 5000+R_IO_ERROR;      /* nothing in status, return some error */
   }
   else
   {
      /* Valid S-field, get version number. */
      pSf+=3;
      ver = 0; 
      HEX2INT(*pSf, ver);
      pSf++;
      ver = ver << 4;
      HEX2INT(*pSf, ver);
      pSf++;

      /* Position pointer to printer state subfield. */
      switch (ver)
      {
         case 0:
         case 1:
         case 2:
            pSf+=12;
            break;
         case 3:
            pSf+=14;
            break;
         case 4:
            pSf+=18;
            break;
         default:
            bug("WARNING: unknown S-field version=%d\n", ver);
            pSf+=12;
            break;            
      }

      /* Extract VStatus.*/
      vstatus = 0; 
      HEX2INT(*pSf, vstatus);
      pSf++;
      vstatus = vstatus << 4;
      HEX2INT(*pSf, vstatus);
      vstatus += 1000;
   }

bugout:
   return vstatus;
}

int DevDiscovery()
{
   char message[LINE_SIZE*64];  
   int hpiod_sd=-1, hpssd_sd=-1;
   struct sockaddr_in pin;  
   int len=0, len2=0;  
   MsgAttributes ma;
 
   message[0] = 0;

   bzero(&pin, sizeof(pin));  
   pin.sin_family = AF_INET;  
   pin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
   pin.sin_port = htons(hpiod_port_num);  
 
   if ((hpiod_sd = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
   {  
      bug("unable to open socket: %m\n");  
      goto mordor;  
   }  
 
   if (connect(hpiod_sd, (void *)&pin, sizeof(pin)) == -1) 
   {  
      bug("unable to connect to socket: %m\n");  
      goto mordor;  
   }  

   len = sprintf(message, "msg=ProbeDevices\n");
 
   if (send(hpiod_sd, message, len, 0) == -1) 
   {  
      bug("unable to send ProbeDevices: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_sd, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive ProbeDevicesResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

   ParseMsg(message, len, &ma);

   len = 0;
   if (ma.result == R_AOK && ma.length)
   {
      len = ma.length;
      fprintf(stdout, "%s", ma.data);
   }

   if (jdprobe)
   {
      message[0] = 0;
   
      bzero(&pin, sizeof(pin));  
      pin.sin_family = AF_INET;  
      pin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
      pin.sin_port = htons(hpssd_port_num);  
 
      if ((hpssd_sd = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
      {  
         bug("unable to open socket: %m\n");  
         goto mordor;  
      }  
 
      if (connect(hpssd_sd, (void *)&pin, sizeof(pin)) == -1) 
      {  
         bug("unable to connect to socket: %m\n");  
         goto mordor;  
      }  

      len2 = sprintf(message, "msg=ProbeDevicesFiltered\nbus=net\n");
 
      if (send(hpssd_sd, message, len2, 0) == -1) 
      {  
         bug("unable to send ProbeDevices: %m\n");  
         goto mordor;  
      }  

      if ((len2 = recv(hpssd_sd, message, sizeof(message), 0)) == -1) 
      {  
         bug("unable to receive ProbeDevicesResult: %m\n");  
         goto mordor;
      }  

      message[len2] = 0;
 
      ParseMsg(message, len2, &ma);

      len2 = 0;
      if (ma.result == R_AOK && ma.length)
      {
         len2 = ma.length;
         fprintf(stdout, "%s", ma.data);
      }
   }  /* end if (jdprobe) */

   if (len+len2 == 0)
      fprintf(stdout, "direct hp:/no_device_found \"Unknown\" \"hp no_device_found\"\n");

mordor:
   if (hpiod_sd >= 0)
      close(hpiod_sd);
   if (hpssd_sd >= 0)
      close(hpssd_sd);  

   return len+len2;
}

int DeviceEvent(char *dev, char *jobid, int code, char *type, int timeout, int sstate)
{
   char message[512];  
   struct sockaddr_in pin;  
   int len=0;
 
   if (sstate == SESSION_START)
   {
      bzero(&pin, sizeof(pin));  
      pin.sin_family = AF_INET;  
      pin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
      pin.sin_port = htons(hpssd_port_num);   /* hpssd */  

      if ((hpssd_socket = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
      {  
         bug("unable to open socket %d: %m\n", hpssd_port_num);  
         hpssd_socket = -1;  
         goto mordor;  
      }  
 
      if (connect(hpssd_socket, (void *)&pin, sizeof(pin)) == -1) 
      {  
         bug("unable to connect to socket %d: %m\n", hpssd_port_num);  
         hpssd_socket = -1;  
         goto mordor;  
      }  
   }
   
   if (hpssd_socket < 0)
      goto mordor;  

   if (timeout == 0)
      len = sprintf(message, "msg=Event\ndevice-uri=%s\njob-id=%s\nevent-code=%d\nevent-type=%s\n", dev, jobid, code, type);
   else
      len = sprintf(message, "msg=Event\ndevice-uri=%s\njob-id=%s\nevent-code=%d\nevent-type=%s\nretry-timeout=%d\n", 
                     dev, jobid, code, type, timeout);
 
   /* Send message with no response. */
   if (send(hpssd_socket, message, len, 0) == -1) 
   {  
      bug("unable to send Event %s %s %d: %m\n", dev, jobid, code);
      hpssd_socket = -1;  
   }  

mordor:

   if (sstate == SESSION_END && hpssd_socket >= 0)
   {
      close(hpssd_socket);
      hpssd_socket = -1;  
   }
   return 0;
}

int main(int argc, char *argv[])
{
   int fd;
   int copies;
   int len, vstatus, cnt;
   char buf[BUFFER_SIZE+HEADER_SIZE];
   MsgAttributes ma;

   if (argc > 1)
   {
      const char *arg = argv[1];
      if ((arg[0] == '-') && (arg[1] == 'h'))
      {
         fprintf(stdout, "HP Linux Imaging and Printing System\nCUPS Backend %s\n", VERSION);
         fprintf(stdout, "(c) 2003-2004 Copyright Hewlett-Packard Development Company, LP\n");
         exit(0);
      }
   }

   ReadConfig();

   if (argc == 1)
   {
      DevDiscovery();
      exit (0);
   }

   if (argc < 6 || argc > 7)
   {
      bug("ERROR: invalid usage: device_uri job-id user title copies options [file]\n");
      exit (1);
   }

   if (argc == 6)
   {
      fd = 0;         /* use stdin. */
      copies = 1;
   }
   else
   {
      if ((fd = open(argv[6], O_RDONLY)) < 0)  /* use specified file */ 
      {
         bug("ERROR: unable to open print file %s: %m\n", argv[6]);
         exit (1);
      }
      copies = atoi(argv[4]);
   }

   DeviceEvent(argv[0], argv[1], EVENT_START_JOB, "event", 0, SESSION_START);

   int hd=-1, channel=-1, n, total, retry=0, size;

   /* Open hp device. */
   do
   {
      if ((hd = OpenHP(argv[0])) < 0)
      {
         /* Display user error. */
         DeviceEvent(argv[0], argv[1], 5000+R_IO_ERROR, "error", RETRY_TIMEOUT, 0);

         bug("INFO: open device failed; will retry in %d seconds...\n", RETRY_TIMEOUT);
         sleep(RETRY_TIMEOUT);
         retry = 1;
      }
   }
   while (hd < 0);

   if (retry)
   {
      /* Clear user error. */
      DeviceEvent(argv[0], argv[1], VSTATUS_PRNT, "event", 0, 0);
      retry=0;
   }

   /* Get any parameters needed for OpenChannel. */ 
   ModelQuery(argv[0], &ma);  

   /* Write print file. */
   while (copies > 0)
   {
      copies--;

      if (fd != 0)
      {
         fputs("PAGE: 1 1\n", stderr);
         lseek(fd, 0, SEEK_SET);
      }

      while ((len = read(fd, buf, BUFFER_SIZE)) > 0)
      {
         size=len;
         total=0;

         while (size > 0)
         {
            /* Got some data now open the print channel. This will handle any HPIJS print channel contention. */
            if (channel < 0)
            {
               do
               {
                  if ((channel = OpenChannel(hd, "PRINT", argv[0], ma.io_mode, ma.flow_ctl)) < 0)
                  {
                     DeviceEvent(argv[0], argv[1], 5000+R_CHANNEL_BUSY, "error", RETRY_TIMEOUT, 0);
                     bug("INFO: open print channel failed; will retry in %d seconds...\n", RETRY_TIMEOUT);
                     sleep(RETRY_TIMEOUT);
                     retry = 1;
                  }
               }
               while (channel < 0);

               if (retry)
               {
                  /* Clear user error. */
                  DeviceEvent(argv[0], argv[1], VSTATUS_PRNT, "event", 0, 0);
                  retry=0;
               }
            }

            n = WriteHP(hd, channel, buf+total, size);

            if (n != size)
            {
               /* IO error, get printer status. */
               vstatus = GetVStatus(hd);

               /* Display user error. */
               DeviceEvent(argv[0], argv[1], vstatus, "error", RETRY_TIMEOUT, 0);

               bug("INFO: %s; will retry in %d seconds...\n", GetVStatusMessage(vstatus), RETRY_TIMEOUT);
               sleep(RETRY_TIMEOUT);
               retry = 1;

            }
            total+=n;
            size-=n;
         }

         if (retry)
         {
            /* Clear user error. */
            DeviceEvent(argv[0], argv[1], VSTATUS_PRNT, "event", 0, 0);
            retry=0;
         }
      }
   } /* while (copies > 0) */

   /* Wait arbitrary time before reading deviceid. LJ1010/1012/1015 will hang with in-bound deviceid query. */ 
   sleep(1);

   /*
    * Since hpiod uses non-blocking i/o we must make sure the printer has received all data
    * before closing the print channel. Otherwise data will be lost.
    */
   vstatus = GetVStatus(hd);
   if (vstatus < 5000)
   {
      /* Got valid status, wait for idle. */
     cnt=0;
     while ((vstatus != VSTATUS_IDLE) && (vstatus < 5000) && (cnt < 5))
     {
        sleep(2);
        vstatus = GetVStatus(hd);
        cnt++;
     }
   }
   else
   {
      /* No valid status, use fixed delay. */
      sleep(10);
   }
   
   DeviceEvent(argv[0], argv[1], EVENT_END_JOB, "event", 0, SESSION_END);
   fprintf(stderr, "INFO: %s\n", GetVStatusMessage(VSTATUS_IDLE));

   if (channel >= 0)
      CloseChannel(hd, channel);
   if (hd >= 0)
      CloseHP(hd);   
   if (fd != 0)
      close(fd);

   exit (0);
}

