/*****************************************************************************\

  ptest.c - HP MFP photo card file manager
 
  (c) 2004 Copyright Hewlett-Packard Development Company, LP

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

\*****************************************************************************/

#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <syslog.h>
#include <stdarg.h>
#include <signal.h>
#include <arpa/inet.h>
#include <errno.h>
#include <ctype.h>
#include "ptest.h"
#include "fat.h"

#if defined(__APPLE__) && defined(__MACH__)
    typedef unsigned long uint32_t;
#endif

#define HPIODFILE "/var/run/hpiod.port"
#define HPSSDFILE "/var/run/hpssd.port"
#define LINE_SIZE 256 /* Length of buffer reads */
#define BUFFER_SIZE 4096
#define HEADER_SIZE 4096   /* Rough estimate for message header */

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
   char uri[LINE_SIZE];
   char flow_ctl[32];
   int descriptor;       /* device descriptor (device-id) */
   int length;           /* length of data in bytes */
   int result;
   int channel;          /* channel descriptor (channel-id) */
   int writelen;           /* bytes-written */
   int readlen;   /* bytes-to-read */
   int sector;
   int nsector;
   int msglen;            /* message length */
   int ndevice;
   unsigned char *data;           /* pointer to data */
} MSG_ATTRIBUTES;

#define DEV_ACK 0x0100

#pragma pack(1)

typedef struct
{
   short cmd;
   unsigned short nsector;
} CMD_READ_REQUEST;

typedef struct{
   short cmd;
   unsigned short nsector;
   short cs;         /* check sum is not used */
} CMD_WRITE_REQUEST;

typedef struct
{
   short cmd;
   uint32_t nsector;
   short ver;
} RESPONSE_SECTOR;

#pragma pack()

static int hpiod_port_num = 50000;
static int hpiod_socket=-1;
static int hpssd_port_num = 50002;
static int hpssd_socket=-1;
static int hd=-1, channel=-1;

int verbose=0;
 
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

/* sysdump() originally came from http://sws.dett.de/mini/hexdump-c , steffen@dett.de . */
int sysdump(void *data, int size)
{
    /* Dump size bytes of *data. Looks like:
     * [0000] 75 6E 6B 6E 6F 77 6E 20 30 FF 00 00 00 00 39 00 unknown 0.....9.
     */

    unsigned char *p = (unsigned char *)data;
    unsigned char c;
    int n, total=0;
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
            total += fprintf(stderr, "[%4.4s]   %-50.50s  %s\n", addrstr, hexstr, charstr);
            hexstr[0] = 0;
            charstr[0] = 0;
        }
        p++; /* next byte */
    }

    if (strlen(hexstr) > 0) {
        /* print rest of buffer if not empty */
        total += fprintf(stderr, "[%4.4s]   %-50.50s  %s\n", addrstr, hexstr, charstr);
    }
    return total;
}

int last_slash(const char *path, int *number_found, int *path_size)
{
   int i, found=0, lasti=0;

   /* Find last '/'. */
   for (i=0; path[i] && i<LINE_SIZE; i++)
      if (path[i] == '/')
      {
         found++;
         lasti=i;
      }

   *number_found = found;
   *path_size = i;

   return lasti;
} 

int nth_slash(const char *path, int n)
{
   int i, found=0, lasti=0;

   /* Find nth '/'. */
   for (i=0; path[i] && i<LINE_SIZE; i++)
      if (path[i] == '/')
      {
         found++;
         lasti=i;
         if (found == n)
           break;
      }

   return lasti;
} 

char *basename(const char *path)
{
   int len, found=0, slash_index=0;

   slash_index = last_slash(path, &found, &len);
   return found ? (char *)path+slash_index+1 : (char *)path; 
}

int dirname(const char *path, char *dir)
{
   int len, found=0, slash_index=0;

   slash_index = last_slash(path, &found, &len);

   if (found == 0)
      strcpy(dir, ".");              /* no '/' */
   else if (path[slash_index+1]==0 && found==1)
      strcpy(dir, "/");              /* '/' only */
   else if (path[slash_index+1]==0 && found>1)
   {
      slash_index = nth_slash(path, found-1);   /* trailing '/', backup */
      strncpy(dir, path, slash_index);
      dir[slash_index]=0;
   }
   else
   {
      strncpy(dir, path, slash_index);      /* normal '/' */
      dir[slash_index]=0;
   }
   return slash_index;  /* return length of dir */
}

int GetDir(char *path, char *dir, char **tail)
{
   int i=0;

   dir[0] = 0;

   if (path[0] == 0)
   {
      strcpy(dir, ".");   /* end of path */
      i = 0;
   }
   else if ((path[0] == '/') && (*tail != path))
   {
      strcpy(dir, "/");          /* found root '/' at beginning of path */
      i=1;
   }                 
   else
   {
      for (i=0; path[i] && (path[i] != '/') && (i<LINE_SIZE); i++)   /* copy directory entry */
         dir[i] = path[i];
      if (i==0)
         strcpy(dir, ".");   /* end of path */
      else
         dir[i] = 0;
      if (path[i] == '/')
         i++;  /* bump past '/' */
   }

   if (tail != NULL)
      *tail = path + i;  /* tail points to next directory or 0 */

   return i;
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

   if (buf[i] == '\n')
   {
      /* do nothing, empty line */
   }
   else if (strncasecmp(&buf[i], "data:", 5) == 0)
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
int ParseMsg(char *buf, int len, MSG_ATTRIBUTES *ma)
{
   char key[LINE_SIZE];
   char value[LINE_SIZE];
   char *tail, *tail2;
   int i, ret=R_AOK;

   ma->cmd[0] = 0;
   ma->uri[0] = 0;
   ma->flow_ctl[0] = 0;
   ma->descriptor = -1;
   ma->length = 0;
   ma->channel = -1;
   ma->data = NULL;
   ma->result = -1;
   ma->writelen = 0;
   ma->readlen = 0;
   ma->sector = 0;
   ma->nsector = 0;
   ma->ndevice = 0;
   ma->msglen = 0;

   i = GetPair(buf, key, value, &tail);
   if (strcasecmp(key, "msg") != 0)
   {
      syslog(LOG_ERR, "invalid message:%s\n", key);
      return R_INVALID_MESSAGE;
   }
   strncpy(ma->cmd, value, sizeof(ma->cmd));

   while (i < len)
   {
      i += GetPair(tail, key, value, &tail);

      if (strcasecmp(key, "device-uri") == 0)
      {
         strncpy(ma->uri, value, sizeof(ma->uri));
      }
      else if (strcasecmp(key, "device-id") == 0)
      {
         ma->descriptor = strtol(value, &tail2, 10);
         if (ma->descriptor < 0)
         {
            syslog(LOG_ERR, "invalid device descriptor:%d\n", ma->descriptor);
            ret = R_INVALID_DESCRIPTOR;
            break;
         }
      }
      else if (strcasecmp(key, "channel-id") == 0)
      {
         ma->channel = strtol(value, &tail2, 10);
         if (ma->channel < 0)
         {
            syslog(LOG_ERR, "invalid channel descriptor:%d\n", ma->channel);
            ret = R_INVALID_CHANNEL_ID;
            break;
         }
      }
      else if (strcasecmp(key, "length") == 0)
      {
         ma->length = strtol(value, &tail2, 10);
         if (ma->length > BUFFER_SIZE)
         {
            syslog(LOG_ERR, "invalid data length:%d\n", ma->length);
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
            syslog(LOG_ERR, "invalid read length:%d\n", ma->readlen);
            ret = R_INVALID_LENGTH;
         }
      }
      else if (strcasecmp(key, "sector") == 0)
      {
         ma->sector = strtol(value, &tail2, 10);
      }
      else if (strcasecmp(key, "nsector") == 0)
      {
         ma->nsector = strtol(value, &tail2, 10);
      }
      else if (strcasecmp(key, "num-devices") == 0)
      {
         ma->ndevice = strtol(value, &tail2, 10);
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

   ma->msglen = i;

   return ret;
}

int ReadConfig()
{
   char rcbuf[255];
   FILE *inFile=NULL;
   char *tail;
        
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

bugout:
   if (inFile != NULL)
     fclose(inFile);
         
   return 0;
}

int OpenHP(char *dev)
{
   char message[512];  
   struct sockaddr_in pin;  
   int len=0, fd=-1;
   MSG_ATTRIBUTES ma;
 
   bzero(&pin, sizeof(pin));  
   pin.sin_family = AF_INET;  
   pin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
   pin.sin_port = htons(hpiod_port_num);  
 
   if ((hpiod_socket = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
   {  
      syslog(LOG_ERR, "unable to open socket %d: %m\n", hpiod_port_num);  
      goto mordor;  
   }  
 
   if (connect(hpiod_socket, (void *)&pin, sizeof(pin)) == -1) 
   {  
      syslog(LOG_ERR, "unable to connect to socket %d: %m\n", hpiod_port_num);  
      goto mordor;  
   }  

   len = sprintf(message, "msg=DeviceOpen\ndevice-uri=%s\n", dev);
 
   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      syslog(LOG_ERR, "unable to send DeviceOpen: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      syslog(LOG_ERR, "unable to receive DeviceOpenResult: %m\n");  
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
   MSG_ATTRIBUTES ma;
 
   len = sprintf(message, "msg=ChannelDataOut\ndevice-id=%d\nchannel-id=%d\nlength=%d\ndata:\n", hd, channel, size);
   if (size+len > sizeof(message))
   {  
      syslog(LOG_ERR, "unable to fill data buffer: size=%d\n", size);  
      goto mordor;  
   }  

   memcpy(message+len, buf, size);
  
   if (send(hpiod_socket, message, size+len, 0) == -1) 
   {  
      syslog(LOG_ERR, "unable to send ChannelDataOut: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      syslog(LOG_ERR, "unable to receive ChannelDataOutResult: %m\n");  
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
   MSG_ATTRIBUTES ma;
 
   len = sprintf(message, "msg=ChannelDataIn\ndevice-id=%d\nchannel-id=%d\nbytes-to-read=%d\n", hd, channel, size);
   if (size+len > sizeof(message))
   {  
      fprintf(stderr, "Error data size=%d\n", size);  
      goto mordor;  
   }  

   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      syslog(LOG_ERR, "unable to send ChannelDataIn: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      syslog(LOG_ERR, "unable to receive ChannelDataInResult: %m\n");  
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
int ModelQuery(char *uri, MSG_ATTRIBUTES *ma)
{
   char message[HEADER_SIZE];  
   char model[128];
   struct sockaddr_in pin;  
   int len=0,stat=1;

   bzero(&pin, sizeof(pin));  
   pin.sin_family = AF_INET;  
   pin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
   pin.sin_port = htons(hpssd_port_num);   /* hpssd */  

   if ((hpssd_socket = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
   {  
      bug("unable to open socket %d: %m\n", hpssd_port_num);  
      hpssd_socket = -1;  
      goto bugout;  
   }  
 
   if (connect(hpssd_socket, (void *)&pin, sizeof(pin)) == -1) 
   {  
      bug("unable to connect to socket %d: %m\n", hpssd_port_num);  
      hpssd_socket = -1;  
      goto bugout;  
   }  

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
   if (hpssd_socket >= 0)
   {
      close(hpssd_socket);
      hpssd_socket = -1;  
   }

   return stat;
}

int OpenChannel(int hd, char *sn, char *uri)
{
   char message[512];  
   int len=0, channel=-1;
   MSG_ATTRIBUTES ma;

   ModelQuery(uri, &ma);

   if (ma.flow_ctl[0] == 0)
      len = sprintf(message, "msg=ChannelOpen\ndevice-id=%d\nservice-name=%s\n", hd, sn);
   else
      len = sprintf(message, "msg=ChannelOpen\ndevice-id=%d\nservice-name=%s\nio-control=%s\n", hd, sn, ma.flow_ctl);

   if (send(hpiod_socket, message, len, 0) == -1) 
   {  
      syslog(LOG_ERR, "unable to send ChannelOpen: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      syslog(LOG_ERR, "unable to receive ChannelOpenResult: %m\n");  
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
      syslog(LOG_ERR, "unable to send ChannelClose: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      syslog(LOG_ERR, "unable to receive ChannelCloseResult: %m\n");  
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
      syslog(LOG_ERR, "unable to send DeviceClose: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(hpiod_socket, message, sizeof(message), 0)) == -1) 
   {  
      syslog(LOG_ERR, "unable to receive DeviceCloseResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

mordor:
   close(hpiod_socket);
   hpiod_socket = -1;  

   return 0;
}

int DevDiscovery(char *uri, int urisize)
{
   char message[LINE_SIZE*64];  
   int socket_descriptor;  
   struct sockaddr_in pin;  
   int i, len=0;  
   MSG_ATTRIBUTES ma;
   char *pBeg;
 
   message[0] = 0;
   uri[0] = 0;

   bzero(&pin, sizeof(pin));  
   pin.sin_family = AF_INET;  
   pin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
   pin.sin_port = htons(hpiod_port_num);  
 
   if ((socket_descriptor = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
   {  
      bug("unable to open socket: %m\n");  
      goto mordor;  
   }  
 
   if (connect(socket_descriptor, (void *)&pin, sizeof(pin)) == -1) 
   {  
      bug("unable to connect to socket: %m\n");  
      goto mordor;  
   }  

   len = sprintf(message, "msg=ProbeDevices\n");
 
   if (send(socket_descriptor, message, len, 0) == -1) 
   {  
      bug("unable to send ProbeDevices: %m\n");  
      goto mordor;  
   }  

   if ((len = recv(socket_descriptor, message, sizeof(message), 0)) == -1) 
   {  
      bug("unable to receive ProbeDevicesResult: %m\n");  
      goto mordor;
   }  

   message[len] = 0;

   ParseMsg(message, len, &ma);
   if (ma.result == R_AOK && ma.length)
   {
      if (verbose > 0)
      {
         len = ma.length;
         fprintf(stderr, "%s", ma.data);
      }

      if (ma.ndevice == 1)
      {
         /* Only one device connected make this the default uri. */
         for (i=0; (strncmp(&ma.data[i], "hp:", 3) != 0) && (i < LINE_SIZE); i++)  /* find start of uri */
            ;
         pBeg = ma.data + i;
         for (i=0; *pBeg != ' ' && (i < urisize); i++, pBeg++)  /* copy uri */
            uri[i] = *pBeg;
         uri[i] = 0;      /* zero terminate */
      }
   }

mordor:
   close(socket_descriptor);  

   return len;
}

int ReadSector(int sector, int nsector, void *buf, int size)
{
   char message[HEADER_SIZE];
   int i, len, rlen, stat=1, total=0;
   CMD_READ_REQUEST *pC;
   RESPONSE_SECTOR *pR;
   uint32_t *pSect;
   short cmd=0x0010;  /* read request */
   
   if (nsector <= 0 || (nsector*FAT_HARDSECT) > size)
   {
      bug("ReadSector invalid sector count=%d\n", nsector);
      goto bugout;
   }
      
   /* Write photo card command to device. */
   pC = (CMD_READ_REQUEST *)message;
   pC->cmd = htons(cmd);
   pC->nsector = htons(nsector);
   pSect = (uint32_t *)(message + sizeof(CMD_READ_REQUEST));
   for (i=0; i<nsector; i++)
     *pSect++ = htonl(sector+i);
   len = sizeof(CMD_READ_REQUEST)+(4*nsector);
   WriteHP(hd, channel, message, len);

   /* Read photo card response header from device. */
   memset(message, 0, sizeof(RESPONSE_SECTOR));
   rlen = sizeof(RESPONSE_SECTOR);
   len = ReadHP(hd, channel, message, rlen); 
   pR = (RESPONSE_SECTOR *)message;
   if (ntohs(pR->cmd) != (cmd | DEV_ACK))
   {
      bug("ReadSector invalid response header cmd=%x expected=%x\n", ntohs(pR->cmd), cmd | DEV_ACK);
      goto bugout;
   }      

   if (verbose > 0)
   {
      static int cnt=0;
      if (cnt++ < 1)
         fprintf(stderr, "photo card firmware version=%x\n", ntohs(pR->ver));   
   }

   /* Read photo card sector data from device. */
   rlen = nsector*FAT_HARDSECT;
   while (total < rlen)
   { 
      if ((len = ReadHP(hd, channel, buf+total, rlen)) == 0)
         break;  /* timeout */
      total+=len;
   }

   if (total != rlen)
   {
      bug("ReadSector invalid response data len=%d expected=%d\n", total, rlen);
      goto bugout;
   }      

   stat = 0;

bugout:
   return stat;    
}

int WriteSector(int sector, int nsector, void *buf, int size)
{
   char message[HEADER_SIZE];
   int i, len, stat=1;
   CMD_WRITE_REQUEST *pC;
   uint32_t *pSect;
   short response=0, cmd=0x0020;  /* write request */

   if (nsector <= 0 || (nsector*FAT_HARDSECT) > size)
   {
      bug("WriteSector invalid sector count=%d\n", nsector);
      goto bugout;
   }
      
   /* Write photo card command header to device. */
   pC = (CMD_WRITE_REQUEST *)message;
   pC->cmd = htons(cmd);
   pC->nsector = htons(nsector);
   pC->cs = 0;
   pSect = (uint32_t *)(message + sizeof(CMD_WRITE_REQUEST));
   for (i=0; i<nsector; i++)
     *pSect++ = htonl(sector+i);
   len = sizeof(CMD_WRITE_REQUEST)+(4*nsector);
   WriteHP(hd, channel, message, len);

   /* Write photo card sector data to device. */
   WriteHP(hd, channel, buf, size);

   /* Read response. */
   len = ReadHP(hd, channel, (char *)&response, sizeof(response)); 
   if (ntohs(response) != DEV_ACK)
   {
      bug("WriteSector invalid response cmd=%x expected=%x\n", ntohs(response), DEV_ACK);
      goto bugout;
   }      
   stat = 0;

bugout:
   return stat;    
}

void usage()
{
   fprintf(stdout, "HP MFP Photo Card File Manager %s\n", VERSION);
   fprintf(stdout, "(c) 2004 Copyright Hewlett-Packard Development Company, LP\n");
   fprintf(stdout, "usage: ptest [-v] [-u uri] -c ls [-p path]  (list directory)\n");
   fprintf(stdout, "       ptest [-v] [-u uri] -c read -p path  (read file to stdout)\n");
   fprintf(stdout, "       ptest [-v] [-u uri] -c rm -p path    (delete file)\n");
   //   fprintf(stdout, "       ptest [-v] -u uri -c write -p path   (write stdin to file)\n");
}

int main(int argc, char *argv[])
{
   char cmd[16] = "", path[LINE_SIZE]="", uri[LINE_SIZE]="", dir[LINE_SIZE]="", spath[LINE_SIZE]="";
   extern char *optarg;
   char *tail;
   int i, stat=-1;
   PHOTO_CARD_ATTRIBUTES pa;

   while ((i = getopt(argc, argv, "vhu:c:p:")) != -1)
   {
      switch (i)
      {
      case 'c':
         strncpy(cmd, optarg, sizeof(cmd));
         break;
      case 'p':
         strncpy(path, optarg, sizeof(path));
         break;
      case 'u':
         strncpy(uri, optarg, sizeof(uri));
         break;
      case 'v':
         verbose++;
         break;
      case 'h':
         usage();
         exit(0);
      case '?':
         usage();
         fprintf(stderr, "unknown argument: %s\n", argv[1]);
         exit(-1);
      default:
         break;
      }
   }

   ReadConfig();

   if (uri[0] == 0)
      DevDiscovery(uri, sizeof(uri));
   if (uri[0] == 0)
   {
      bug("invalid uri %s or more than one device connected\n", uri);
      goto bugout;
   }   

   if ((hd = OpenHP(uri)) < 0)
   {
      bug("unable to open device %s\n", uri);
      goto bugout;
   }   
   if ((channel = OpenChannel(hd, "hp-card-access", uri)) < 0)
   {
      bug("unable to open hp-card-access channel %s\n", uri);
      goto bugout;
   }

   if (FatInit() != 0)
   {
      bug("unable to read photo card %s\n", uri);
      goto bugout;
   }

   FatDiskAttributes(&pa);

   /* If disk is write protected reopen channel to clear write error. */
   if (pa.WriteProtect)
   {
      CloseChannel(hd, channel);
      if ((channel = OpenChannel(hd, "hp-card-access", uri)) < 0)
      {
         bug("unable to open hp-card-access channel %s\n", uri);
         goto bugout;
      }
   }

   if (strcasecmp(cmd, "ls") == 0)
   {
      /* Walk the path for each directory entry. */
      GetDir(path, dir, &tail);
      FatSetCWD(dir);
      while (tail[0] != 0)
      {
         GetDir(tail, dir, &tail);
         FatSetCWD(dir);
      }
      FatListDir();
   }
   else if (strcasecmp(cmd, "read") == 0)
   {
      dirname(path, spath);       /* extract directory */
      GetDir(spath, dir, &tail);
      FatSetCWD(dir);
      while (tail[0] != 0)
      {
         GetDir(tail, dir, &tail);
         FatSetCWD(dir);
      }    
      if ((FatReadFile(basename(path), STDOUT_FILENO)) <= 0)
      {
         bug("unable to locate file %s\n", path);
         goto bugout;
      }
   }
   else if (strcasecmp(cmd, "rm") == 0)
   {
      dirname(path, spath);       /* extract directory */
      GetDir(spath, dir, &tail);
      FatSetCWD(dir);
      while (tail[0] != 0)
      {
         GetDir(tail, dir, &tail);
         FatSetCWD(dir);
      }    
      if (FatDeleteFile(basename(path)) != 0)
      {
         bug("unable to locate file %s\n", path);
         goto bugout;
      }
   }
   else
   {
      usage();  /* invalid command */
      goto bugout;
   }   

   stat = 0;

bugout:
   if (channel >= 0)
      CloseChannel(hd, channel);
   if (hd >= 0)
      CloseHP(hd);   
  
   exit (stat);
}

