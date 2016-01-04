/*****************************************************************************\

  system.cpp - class provides common system services 
 
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

#include "hpiod.h"

const char ERR_MSG[] = "msg=MessageError\nresult-code=%d\n";

System::System()
{
   struct sockaddr_in sin;
   int i, len, fd;
   int yes=1;
   char buf[128];

   /* Set some defaults. */
   HpiodPortNumber = 50000;
   DeviceCnt = 0;
   Reset = 0;

   ReadConfig();
   pthread_mutex_init(&mutex, NULL); /* create fast mutex */

   for (i=0; i<MAX_DEVICE; i++)
      pDevice[i] = NULL;

   /* Create permanent socket. */
   Permsd = socket(AF_INET, SOCK_STREAM, 0);
   if (Permsd == -1)
   {
      syslog(LOG_ERR, "unable to open permanent socket: %m\n");  
      exit(EXIT_FAILURE);
   }

   /* Get rid of "address already in use" error message. */
   if (setsockopt(Permsd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1)
   {
      syslog(LOG_ERR, "unable to setsockopt: %m\n");
      exit(EXIT_FAILURE);
   }

   bzero(&sin, sizeof(sin));
   sin.sin_family = AF_INET;
   sin.sin_addr.s_addr = INADDR_ANY;
   sin.sin_port = htons(GetHpiodPortNumber());

   if (bind(Permsd, (struct sockaddr *)&sin, sizeof(sin)) == -1) 
   {
      syslog(LOG_ERR, "unable to bind socket %d: %m\n", GetHpiodPortNumber());
      exit(EXIT_FAILURE);
   }

   /* Verify port assignment, could be dynamic (port=0). */
   len = sizeof(sin);
   getsockname(Permsd,(struct sockaddr *)&sin, (socklen_t *)&len);
   HpiodPortNumber = ntohs(sin.sin_port);

   if (listen(Permsd, 20) == -1) 
   {
      syslog(LOG_ERR, "unable to listen socket %d: %m\n", GetHpiodPortNumber());
      exit(EXIT_FAILURE);
   }

   if((fd = open("/var/run/hpiod.port", O_CREAT | O_TRUNC | O_WRONLY, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)) < 0)
   {
      syslog(LOG_ERR, "unable create /var/run/hpiod.port: %m\n");
      exit(EXIT_FAILURE);
   }

   len = sprintf(buf, "%d\n", GetHpiodPortNumber());
   write(fd, buf, len);
   close(fd);

   syslog(LOG_INFO, "%s accepting connections at %d...\n", VERSION, GetHpiodPortNumber()); 
}

System::~System()
{
   int i;

   for (i=0; i<MAX_DEVICE; i++)
   {
      if (pDevice[i] != NULL)
      {
         delete pDevice[i];
      }
   }

   pthread_mutex_destroy(&mutex);
   close(Permsd);
}

//System::ReadConfig
//! Read changeable system parameters.
/*!
******************************************************************************/
int System::ReadConfig()
{
   char rcbuf[LINE_SIZE]; /* Hold the value read */
   char section[32];
   FILE *inFile;
   char *tail;
        
   if((inFile = fopen(RCFILE, "r")) == NULL) 
   {
      syslog(LOG_ERR, "unable to open %s: %m\n", RCFILE);
      return 1;
   } 

   /* Read the config file */
   while ((fgets(rcbuf, sizeof(rcbuf), inFile) != NULL))
   {
      if (rcbuf[0] == '[')
         strncpy(section, rcbuf, sizeof(section)); /* found new section */
      else if ((strncasecmp(section, "[hpiod]", 7) == 0) && (strncasecmp(rcbuf, "port=", 5) == 0))
         HpiodPortNumber = strtol(rcbuf+5, &tail, 10);
   }
        
   fclose(inFile);
         
   return 0;
}

//System::Write
//!  Kernel write with timeout. File descriptor must be opened with O_NONBLOCK.
/*!
******************************************************************************/
int System::Write(int fd, const void *buf, int size)
{
   struct timeval tmo;
   fd_set master;
   fd_set writefd;
   int maxfd, ret, len=0;

   if (fd<0)
   {
      syslog(LOG_ERR, "invalid System::Write: %d\n", fd);  /* extra sanity check */
      len = -2;
      goto bugout;
   }

   FD_ZERO(&master);
   FD_SET(fd, &master);
   maxfd = fd;
   tmo.tv_sec = EXCEPTION_TIMEOUT;
   tmo.tv_usec = 0;

   while(1)
   {
      writefd = master;
      if ((ret = select(maxfd+1, NULL, &writefd, NULL, &tmo)) == 0)
      {
         len = -1;
         break;   /* timeout */
      }
      len = write(fd, buf, size);
      if (len < 0)
         if (errno == EAGAIN)
            continue;
      break;
   }

bugout:
   return len;
}

//System::Read
//!  Kernel read with timeout. File descriptor must be opened with O_NONBLOCK.
/*!
******************************************************************************/
int System::Read(int fd, void *buf, int size, int sec, int usec)
{
   struct timeval tmo;
   fd_set master;
   fd_set readfd;
   int maxfd, ret, len=0;

   if (fd<0)
   {
      syslog(LOG_ERR, "invalid System::Read: %d\n", fd);  /* extra sanity check */
      len = -2;
      goto bugout;
   }

   FD_ZERO(&master);
   FD_SET(fd, &master);
   maxfd = fd;
   tmo.tv_sec = sec;
   tmo.tv_usec = usec;

   while(1)
   {
      readfd = master;
      if ((ret = select(maxfd+1, &readfd, NULL, NULL, &tmo)) == 0)
      {
         len = -1;
         break;   /* timeout */
      }
      len = read(fd, buf, size);
      if (len == 0)
      {
         // Zero reads wasts cpu resources, but this appears to be normal. 
         //         syslog(LOG_ERR, "zero read\n");   
         continue;
      }
      if (len < 0)
         if (errno == EAGAIN)
            continue;
      break;
   }

bugout:
   return len;
}

//System::GetPair
//!  Get key value pair from buffer. Assumes one key value pair per line.
//!  Note, end-of-line '/n' is stripped out. Both key/value pairs are zero
//!  terminated.
/*!
******************************************************************************/
int System::GetPair(char *buf, char *key, char *value, char **tail)
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

//System::IsHP
//! Given the IEEE 1284 device id string, determine if this is a HP product.
/*!
******************************************************************************/
int System::IsHP(char *id)
{
   char *pMf;

   if ((pMf = strstr(id, "MFG:")) != NULL)
      pMf+=4;
   else if ((pMf = strstr(id, "MANUFACTURER:")) != NULL)
      pMf+=13;
   else
      return 0;

   if ((strncasecmp(pMf, "HEWLETT-PACKARD", 15) == 0) ||
      (strncasecmp(pMf, "APOLLO", 6) == 0) || (strncasecmp(pMf, "HP", 2) == 0))
   {
      return 1;  /* found HP product */
   }
   return 0;   
}

//System::GetModel
//! Parse the model from the IEEE 1284 device id string.
/*!
******************************************************************************/
int System::GetModel(char *id, char *buf, int bufSize)
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

//System::GetSerialNum
//! Parse the serial number from the IEEE 1284 device id string.
/*!
******************************************************************************/
int System::GetSerialNum(char *id, char *buf, int bufSize)
{
   char *pSN;
   int i;

   buf[0] = 0;

   if ((pSN = strstr(id, "SERN:")) != NULL)
      pSN+=5;
   else if ((pSN = strstr(id, "SN:")) != NULL)
      pSN+=3;
   else
      return 0;

   for (i=0; (pSN[i] != ';') && (i < bufSize); i++)
      buf[i] = pSN[i];
   buf[i] = 0;

   return i;
}

//System::GetUriDataLink
//! Parse the data link from a uri string.
/*!
******************************************************************************/
int System::GetURIDataLink(char *uri, char *buf, int bufSize)
{
   char *p;
   int i;

   buf[0] = 0;

   if (strcasestr(uri, "usb/") != NULL)
   {
      if ((p = strcasestr(uri, "device=")) != NULL)
         p+=7;
      else
         return 0;
   }
   else
   {
      if ((p = strcasestr(uri, "ip=")) != NULL)
         p+=3;
      else
         return 0;
   }

   for (i=0; (p[i] != 0) && (p[i] != '&') && (i < bufSize); i++)
      buf[i] = p[i];

   buf[i] = 0;

   return i;
}

//System::GetURIModel
//! Parse the model from a uri string.
/*!
******************************************************************************/
int System::GetURIModel(char *uri, char *buf, int bufSize)
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

//System::GetURISerial
//! Parse the serial number from a uri string.
/*!
******************************************************************************/
int System::GetURISerial(char *uri, char *buf, int bufSize)
{
   char *p;
   int i;

   buf[0] = 0;

   if ((p = strcasestr(uri, "serial=")) != NULL)
      p+=7;
   else
      return 0;

   for (i=0; (p[i] != 0) && (p[i] != '+') && (i < bufSize); i++)
      buf[i] = p[i];

   buf[i] = 0;

   return i;
}

//System::GeneralizeURI
//! Convert any serial number URI to non-serial number URI.
//!
//! Serial number URI example:
//!    hp:/usb/DESKJET_990C?serial=C1234X
//! 
//! Non-serial number URI example:
//!    hp:/usb/DESKJET_990C?device=/dev/usb/lp0
//!    hp:/net/DESKJET_990C?ip=15.252.63.142 (jetdirect)
//!
//! Both URI types may point to the same physical device (data link).
//!
//! For a serial number based uri, each physical device is searched for
//! the same model and serial number specified in the uri. 
//! If a match is found the m_uri is modified. 
//!
//! This will take care of peripherals that have moved (ie: lp0 to lp1)
//! after different power-up sequences.
//!
//! Return value: 0=OK, 1=Invalid URI 
/*!
******************************************************************************/
int System::GeneralizeURI(MsgAttributes *ma)
{
   char dev[255];
   char model[128];
   char serial[128];
   char uriModel[128];
   char uriSerial[128];
   char sendBuf[1024];
   char *id;
   int i, len, found=0, result;
   Device *pD;

   if (strcasestr(ma->uri, "usb/") == NULL && strcasestr(ma->uri, "net/") == NULL)
      return 1;  /* invalid uri */

   if (strcasestr(ma->uri, "device=") != NULL)
      return 0;  /* uri is all ready generalized */

   if (strcasestr(ma->uri, "ip=") != NULL)
      return 0;  /* uri is all ready generalized */

   if (GetURIModel(ma->uri, uriModel, sizeof(uriModel)) == 0)
      return 1; /* invalid uri */ 

   if (GetURISerial(ma->uri, uriSerial, sizeof(uriSerial)) == 0)
      return 1;  /* invalid uri */
      
   for (i = 0; i < 16 && !found; i ++)
   {
      sprintf(dev, "hp:/usb/ANY?device=/dev/usb/lp%d", i);

      pD = NewDevice(dev);
      len = pD->Open(sendBuf, &result);
      if (result == R_AOK)
      {
         len = pD->GetDeviceID(sendBuf, sizeof(sendBuf), &result);
         if (result == R_AOK)
         {
            id = pD->GetID(); /* use cached copy */

            if (id[0] != 0 && IsHP(id))
            {
               GetModel(id, model, sizeof(model));
               GetSerialNum(id, serial, sizeof(serial));
               if ((strcmp(model, uriModel)==0) && (strcmp(serial, uriSerial)==0))
               {
                  sprintf(ma->uri, "hp:/usb/%s?device=/dev/usb/lp%d", model, i);
                  found = 1;
               }
            }
         }
      }

      pD->Close(sendBuf, &result);
      DelDevice(pD->GetIndex());
   }

   if (found)
      return 0;
   else
      return 1;
}

//System::UsbDiscovery
//! Walk the usb ports looking for HP products. 
/*!
******************************************************************************/
int System::UsbDiscovery(char *lst, int *cnt)
{
   char dev[255];
   char model[128];
   char serial[128];
   char sendBuf[2048];
   char *id;
   int i, len, size=0, result;
   Device *pD;

   for (*cnt=0, i=0; i < 16; i++)
   {
      sprintf(dev, "hp:/usb/ANY?device=/dev/usb/lp%d", i);

      pD = NewDevice(dev);
      len = pD->Open(sendBuf, &result);
      if (result == R_AOK)
      {
         id = pD->GetID(); /* use cached copy */

         if (id[0] != 0 && IsHP(id))
         {
            GetModel(id, model, sizeof(model));
            GetSerialNum(id, serial, sizeof(serial));
            if (strcmp(serial, "")==0)
               sprintf(dev, "hp:/usb/%s?device=/dev/usb/lp%d", model, i);
            else
               sprintf(dev, "hp:/usb/%s?serial=%s", model, serial);
            size += sprintf(lst+size,"direct %s \"HP %s\" \"%s\"\n", dev, model, dev);
            *cnt+=1;
         }
      }

      pD->Close(sendBuf, &result);
      DelDevice(pD->GetIndex());
   }

   return size;
}

//System::ProbeDevices
//!  Perform hp device discovery. Works simultaneously with other open clients.
/*!
******************************************************************************/
int System::ProbeDevices(char *sendBuf)
{
   char lst[LINE_SIZE*MAX_DEVICE];
   int len, lstLen, cnt;

   lst[0] = 0;
   lstLen = UsbDiscovery(lst, &cnt);

   len = sprintf(sendBuf, "msg=ProbeDevicesResult\nresult-code=%d\nnum-devices=%d\nlength=%d\ndata:\n%s", R_AOK, cnt, lstLen, lst); 

   return len;
}

//System::ParseMsg
//!  Parse and convert all key value pairs in message. Do sanity check on values.
/*!
******************************************************************************/
int System::ParseMsg(char *buf, int len, MsgAttributes *ma)
{
   char key[LINE_SIZE];
   char value[LINE_SIZE];
   char *tail, *tail2;
   int i, ret=R_AOK;

   ma->cmd[0] = 0;
   ma->uri[0] = 0;
   ma->service[0] = 0;
   ma->io_mode[0] = 0;
   ma->flow_ctl[0] = 0;
   ma->descriptor = -1;
   ma->length = 0;
   ma->channel = -1;
   ma->readlen = 0;
   ma->data = NULL;
   ma->result = -1;
   ma->timeout = EXCEPTION_TIMEOUT;

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
         if (!((strncasecmp(ma->uri, "hp:", 3) == 0) &&
               (strstr(ma->uri, "?") != NULL) &&
                  (GeneralizeURI(ma) == 0)))
         {
            syslog(LOG_ERR, "invalid uri:%s\n", ma->uri);
            ret = R_INVALID_URI;
            break;
         }
      }
      else if (strcasecmp(key, "device-id") == 0)
      {
         ma->descriptor = strtol(value, &tail2, 10);
         if (ma->descriptor <= 0 || ma->descriptor >= MAX_DEVICE || pDevice[ma->descriptor] == NULL)
         {
            syslog(LOG_ERR, "invalid device descriptor:%d\n", ma->descriptor);
            ret = R_INVALID_DESCRIPTOR;
            break;
         }
      }
      else if (strcasecmp(key, "channel-id") == 0)
      {
         ma->channel = strtol(value, &tail2, 10);
         if (ma->channel <= 0 || ma->channel >= MAX_CHANNEL)
         {
            syslog(LOG_ERR, "invalid channel descriptor:%d\n", ma->channel);
            ret = R_INVALID_CHANNEL_ID;
            break;
         }
      }
      else if (strcasecmp(key, "job-id") == 0)
      {
         ma->jobid = strtol(value, &tail2, 10);
      }
      else if (strcasecmp(key, "timeout") == 0)
      {
         ma->timeout = strtol(value, &tail2, 10);
      }
      else if (strcasecmp(key, "length") == 0)
      {
         ma->length = strtol(value, &tail2, 10);
         if (ma->length > BUFFER_SIZE)
         {
            syslog(LOG_ERR, "invalid data length:%d\n", ma->length);
            ret = R_INVALID_LENGTH;
            break;
         }
      }
      else if (strcasecmp(key, "service-name") == 0)
      {
         strncpy(ma->service, value, sizeof(ma->service));
      }
      else if (strcasecmp(key, "bytes-to-read") == 0)
      {
         ma->readlen = strtol(value, &tail2, 10);
         if (ma->readlen > BUFFER_SIZE)
         {
            syslog(LOG_ERR, "invalid read length:%d\n", ma->readlen);
            ret = R_INVALID_LENGTH;
            break;
         }
      }
      else if (strcasecmp(key, "data:") == 0)
      {
         ma->data = (unsigned char *)tail;
         break;  /* done parsing */
      }
      else if (strcasecmp(key, "io-mode") == 0)
      {
         strncpy(ma->io_mode, value, sizeof(ma->io_mode));      /* raw | mlc */
      }
      else if (strcasecmp(key, "result-code") == 0)
      {
         ma->result = strtol(value, &tail2, 10);
      }
      else if (strcasecmp(key, "io-control") == 0)
      {
         strncpy(ma->flow_ctl, value, sizeof(ma->flow_ctl));    /* gusher | miser */
      }
      else
      {
         /* Unknown keys are ignored (R_AOK). */
//         syslog(LOG_ERR, "invalid key:%s\n", key);
      }
   }  // end while (i < len)

   return ret;
}

//System::DeviceCleanUp
//!  Client was aborted pre-maturely, close the device.
/*!
******************************************************************************/
int System::DeviceCleanUp(int index)
{
   char dummyBuf[255];
   int dummy;

   syslog(LOG_INFO, "device cleanup id=%d\n", index);
   pDevice[index]->Close(dummyBuf, &dummy);
   DelDevice(index);

   return 0;
}

//System::NewDevice
//!  Create or re-use device object given the URI.
/*!
******************************************************************************/
Device *System::NewDevice(char *uri)
{
   char newDL[255];
   char oldDL[255];
   Device *pD=NULL;
   int i, n;

   if (uri[0] == 0)
      return pD;

   if (pthread_mutex_lock(&mutex) != 0)
   {
      syslog(LOG_ERR, "unable to lock NewDevice: %m\n");
      return pD;
   }

   /* Check for existing device object based on uri. */
   for (i=1, n=0; i<MAX_DEVICE && n<DeviceCnt; i++)
   {
      if (pDevice[i] != NULL)
      {
         n++;
         GetURIDataLink(uri, newDL, sizeof(newDL));
         GetURIDataLink(pDevice[i]->GetURI(), oldDL, sizeof(oldDL));
         if (strcmp(newDL, oldDL) == 0)
         {
            pD = pDevice[i];   /* same data link */
            pD->SetClientCnt(pD->GetClientCnt()+1);
            goto bugout;
         }
      }
   }

   if (DeviceCnt >= MAX_DEVICE)
      goto bugout;

   /* Look for unused slot in device array. Note, slot 0 is unused. */
   for (i=1; i<MAX_DEVICE; i++)
   {
      if (pDevice[i] == NULL)
      {
         if (strcasestr(uri, "usb/") != NULL)
            pD = new UsbDevice(this);
         else
            pD = new JetDirectDevice(this);
         pD->SetIndex(i);
         pD->SetURI(uri);
         pDevice[i] = pD;
         DeviceCnt++;
         break;
      }
   }     

bugout:
   pthread_mutex_unlock(&mutex);

   return pD;
}

//System::DelDevice
//!  Remove device object given the device decriptor.
/*!
******************************************************************************/
int System::DelDevice(int index)
{
   Device *pD = pDevice[index];

   if (pthread_mutex_lock(&mutex) != 0)
      syslog(LOG_ERR, "unable to lock DelDevice: %m\n");

   pD->SetClientCnt(pD->GetClientCnt()-1);

   if (pD->GetClientCnt() <= 0)
   {
      delete pD;
      pDevice[index] = NULL;
      DeviceCnt--;
   }

   pthread_mutex_unlock(&mutex);

   return 0;
}

//System::ExecuteMsg
//!  Process client request. ExecuteMsg is called by different threads.
//!  Two mutexes are used for thread synchronization. There is a System mutex
//!  and Device mutex. Thread access to these objects may cause the thread to
//!  suspend until the object is unlocked. See the following table.
//!
//! <commands>      <possible thread lock suspend>
//!                 <System mutex>  <Device mutex>
//! DeviceOpen        yes              no
//! DeviceClose       yes              no
//! DeviceID          no               no
//! DeviceStatus      no               yes
//! ChannelOpen       no               yes
//! ChannelClose      no               yes
//! ChannelDataOut    no               yes
//! ChannelDataIn     no               yes
//! ProbeDevices      yes              no
//! DeviceFile        yes              no
//!
//! System suspends are fast and deterministic. Device suspends by nature are not
//! deterministic, but are hardware dependent.
/*!
******************************************************************************/
int System::ExecuteMsg(SessionAttributes *psa, char *recvBuf, int rlen, char *sendBuf, int slen)
{
   int len, ret;
   MsgAttributes ma;
   Device *pD;

   if ((ret = ParseMsg(recvBuf, rlen, &ma)) != R_AOK)
      return (sprintf(sendBuf, ERR_MSG, ret));

#ifdef HPIOD_DEBUG
   if (ma.length == 0)
   {
      recvBuf[rlen]=0;
      syslog(LOG_INFO, "tid:%x %s\n", (int)psa->tid, recvBuf);
   }
   else
   {
      syslog(LOG_INFO, "tid:%x %s di=%d ci=%d size=%d\n", psa->tid, ma.cmd, ma.descriptor, ma.channel, ma.length);
   }
#endif

   if (strcasecmp(ma.cmd, "DeviceID") == 0) 
   {
      len = pDevice[ma.descriptor]->GetDeviceID(sendBuf, slen, &ret);
   }
   else if (strcasecmp(ma.cmd, "DeviceStatus") == 0)
   {
      len = pDevice[ma.descriptor]->GetDeviceStatus(sendBuf, &ret);       
   }
   else if (strcasecmp(ma.cmd, "ChannelDataOut") == 0)
   {
      pD = pDevice[ma.descriptor];
      len = pD->WriteData(ma.data, ma.length, ma.channel, sendBuf, &ret);               
   }
   else if (strcasecmp(ma.cmd, "ChannelDataIn") == 0)
   {
      pD = pDevice[ma.descriptor];
      len = pD->ReadData(ma.readlen, ma.channel, ma.timeout, sendBuf, slen, &ret);       
   }
   else if (strcasecmp(ma.cmd, "DeviceOpen") == 0)
   {
      if (psa->descriptor != -1)
         len = sprintf(sendBuf, ERR_MSG, R_INVALID_DEVICE_OPEN); /* allow only one DeviceOpen per session */
      else if ((pD = NewDevice(ma.uri)) == NULL)
         len = sprintf(sendBuf, ERR_MSG, R_INVALID_URI);
      else
      {
         len = pD->Open(sendBuf, &ret);
         if (ret == R_AOK)
            psa->descriptor = pD->GetIndex();  /* track device descriptor for session clean up */     
         else
         {
            /* Open failed perform device cleanup. */
            char dummyBuf[255];               
            int dummy, index = pD->GetIndex();
            pDevice[index]->Close(dummyBuf, &dummy);
            DelDevice(index);
         }
      }
   }
   else if (strcasecmp(ma.cmd, "DeviceClose") == 0)
   {
      pD = pDevice[ma.descriptor];
      len = pD->Close(sendBuf, &ret);
      DelDevice(ma.descriptor);
      psa->descriptor = -1;  /* mark session as clean */     
   }
   else if (strcasecmp(ma.cmd, "ChannelOpen") == 0)
   {
      pD = pDevice[ma.descriptor];
      len = pD->ChannelOpen(ma.service, ma.io_mode, ma.flow_ctl, sendBuf, &ret);
   }
   else if (strcasecmp(ma.cmd, "ChannelClose") == 0)
   {
      pD = pDevice[ma.descriptor];
      len = pD->ChannelClose(ma.channel, sendBuf, &ret);
   }
   else if (strcasecmp(ma.cmd, "ProbeDevices") == 0)
   {
      len = ProbeDevices(sendBuf);       
   }
   else if (strcasecmp(ma.cmd, "DeviceFile") == 0)
   {
      len = sprintf(sendBuf, "msg=DeviceFileResult\nresult-code=%d\ndevice-file=%s\n", R_AOK, ma.uri);
   }
   else
   {
      /* Unknown message. */
      syslog(LOG_ERR, "invalid message:%s\n", ma.cmd);
      len = sprintf(sendBuf, ERR_MSG, R_INVALID_MESSAGE);
   }

#ifdef HPIOD_DEBUG
   ParseMsg(sendBuf, len, &ma);
   if (ma.length == 0)
   {
      syslog(LOG_INFO, "-tid:%x %s\n", (int)psa->tid, sendBuf);
   }
   else
   {
      syslog(LOG_INFO, "-tid:%x %s di=%d ci=%d size=%d\n", psa->tid, ma.cmd, ma.descriptor, ma.channel, ma.length);
   }
#endif

   return len;
}
