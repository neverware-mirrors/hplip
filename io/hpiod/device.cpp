/*****************************************************************************\

  device.cpp - base class for devices 
 
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
  Client/Server generic message format (see messaging-protocol.doc):

\*****************************************************************************/

#include "hpiod.h"

const unsigned char Venice_Power_On[] = {0x1b, '%','P','u','i','f','p','.',
        'p','o','w','e','r',' ','1',';',
        'u','d','w','.','q','u','i','t',';',0x1b,'%','-','1','2','3','4','5','X' };

/* Constructor should be called from System::NewDevice which is thread safe. */
Device::Device(System *pS) : pSys(pS)
{
   int i;

   URI[0] = 0;
   ID[0] = 0;
   OpenFD = -1;
   ClientCnt = 1;
   pthread_mutex_init(&mutex, NULL); /* create fast mutex */

   for (i=0; i<MAX_CHANNEL; i++)
      pChannel[i] = NULL;
   ChannelCnt = 0;
   ChannelMode = -1; 
   MlcUp = 0;
   CurrentProtocol = USB_PROTOCOL_712;
   NewProtocol = 0;
   memset(CA, 0, sizeof(CA));
}

/* Destructor should be called from System::DelDevice which is thread safe. */
Device::~Device()
{
   int i;

   if (OpenFD >= 0)
      close(OpenFD);
   for (i=0; i<MAX_CHANNEL; i++)
      if (pChannel[i] != NULL)
         delete pChannel[i];
   pthread_mutex_destroy(&mutex);
}

//Device::Write
//!  Kernel write with timeout. File descriptor must be opened with O_NONBLOCK.
/*!
******************************************************************************/
int Device::Write(int fd, const void *buf, int size)
{
   struct timeval tmo;
   fd_set master;
   fd_set writefd;
   int maxfd, ret, len=0;

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

   return len;
}

//Device::Read
//!  Kernel read with timeout. File descriptor must be opened with O_NONBLOCK.
/*!
******************************************************************************/
int Device::Read(int fd, void *buf, int size, int sec, int usec)
{
   struct timeval tmo;
   fd_set master;
   fd_set readfd;
   int maxfd, ret, len=0;

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

   return len;
}

int Device::DeviceID(char *buffer, int size)
{
   int len=0, maxSize;

   maxSize = (size > 1024) ? 1024 : size;   /* RH8 has a size limit for device id */

   if (ioctl(OpenFD, LPIOC_GET_DEVICE_ID(maxSize), (void*)(buffer)) < 0)
   {
     //      if (errno == ENODEV)
     //         len = -1;
      syslog(LOG_ERR, "unable to read uri:%s Device::DeviceID: %m\n", URI);
      goto bugout;
   }

   len = ((unsigned char)buffer[0] << 8) + (unsigned char)buffer[1];
   if (len > (size-1))
      len = size-1;   /* leave byte for zero termination */
   if (len > 2)
      len -= 2;
   memcpy(buffer, buffer+2, len);    /* remove length */
   buffer[len]=0;

bugout:
   return len; /* length does not include zero termination */
}

/* Get VStatus from S-field. */
int Device::SFieldPrinterState(char *id)
{
   char *pSf;
   int vstatus=0, ver;

   if ((pSf = strstr(id, ";S:")) == NULL)
   {
      syslog(LOG_ERR, "invalid S-field\n");
      return vstatus;
   }

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
         syslog(LOG_ERR, "unknown S-field version=%d\n", ver);
         pSf+=12;
         break;            
   }

   /* Extract VStatus.*/
   vstatus = 0; 
   HEX2INT(*pSf, vstatus);
   pSf++;
   vstatus = vstatus << 4;
   HEX2INT(*pSf, vstatus);

   return vstatus;
}

/* Power up printer if necessary. */
int Device::PowerUp()
{
   char *pSf;

   if ((pSf = strstr(ID, "CMD:LDL")) != NULL)
     return 0;   /* crossbow don't do power-up */

   if ((pSf = strstr(ID, ";S:")) != NULL)
   {
      if (SFieldPrinterState(ID) != 3)
         return 0;     /* already powered up */
   }
   else if ((pSf = strstr(ID, "VSTATUS:")) != NULL)
   {
      if ((pSf = strstr(pSf+8, "OFFF")) == NULL)
         return 0;   /* already powered up */
   }
   else
      return 0;  /* must be laserjet, don't do power-up */

   Write(OpenFD, Venice_Power_On, sizeof(Venice_Power_On));  
   sleep(2);

   return 0;
}

int Device::Open(char *sendBuf, int *result)
{
   char dev[255];
   char uriModel[128];
   char model[128];
   int len=0;

   *result = R_AOK;

   if (pthread_mutex_trylock(&mutex) != 0)
      goto bugout;   /* device is already open. */ 

   pSys->GetURIModel(URI, uriModel, sizeof(uriModel));

   //   if (ClientCnt==1)
   if (ID[0] == 0)
   {
      /* First DeviceOpen, open actual kernal device. */
      pSys->GetURIDataLink(URI, dev, sizeof(dev));
      if ((OpenFD = open(dev, O_RDWR | O_NONBLOCK | O_EXCL)) < 0) 
      {
         *result = R_IO_ERROR;
         if (strcmp(uriModel, "ANY") != 0)
            syslog(LOG_ERR, "unable to Device::Open %s: %m\n", URI);
         goto blackout;
      }

      len = DeviceID(ID, sizeof(ID));  /* get new copy and cache it  */ 

      if (len == 0)
      {
         *result = R_IO_ERROR;
         goto blackout;
      }

      if (pSys->IsHP(ID) && strcmp(uriModel, "ANY") != 0)
      {
         PowerUp();
      }
   }
   else
   {
      len = DeviceID(ID, sizeof(ID));  /* refresh */
      if (len == 0)
      {
         *result = R_IO_ERROR;
         goto blackout;
      }        
   }

   /* Make sure uri model matches device id model. Ignor test if uri model equals "ANY" (probe). */
   if (strcmp(uriModel, "ANY") != 0)
   {
      pSys->GetModel(ID, model, sizeof(model));
      if (strcmp(uriModel, model) != 0)
      {
         *result = R_INVALID_DEVICE_NODE;  /* probably a laserjet, or different device plugged in */  
         syslog(LOG_ERR, "invalid model %s != %s Device::Open\n", uriModel, model);
         goto blackout;
      }
   }

blackout:
   pthread_mutex_unlock(&mutex);

bugout:
   if (*result == R_AOK)
      len = sprintf(sendBuf, "msg=DeviceOpenResult\nresult-code=%d\ndevice-id=%d\n", *result, Index);  
   else
      len = sprintf(sendBuf, "msg=DeviceOpenResult\nresult-code=%d\n", *result);  

   return len;
}

int Device::Close(char *sendBuf, int *result)
{
   char res[] = "msg=DeviceCloseResult\nresult-code=%d\n";
   int len=0;

   *result = R_AOK;

   if (pthread_mutex_trylock(&mutex) != 0)
      goto bugout;   /* device is still in use */

   if (OpenFD >=0 && ClientCnt==1)
   {
      close(OpenFD);
      OpenFD = -1;
   }

   pthread_mutex_unlock(&mutex);

bugout:
   len = sprintf(sendBuf, res, *result);  

   return len;
}

int Device::GetDeviceID(char *sendBuf, int slen, int *result)
{
   char res[] = "msg=DeviceIDResult\nresult-code=%d\n";
   int len=0, idLen;

   *result = R_AOK;

//   if (pthread_mutex_trylock(&mutex) == 0)
   if (pthread_mutex_lock(&mutex) == 0)
   {
      idLen = DeviceID(ID, sizeof(ID));  /* get new copy */
      pthread_mutex_unlock(&mutex);

      if (idLen == 0)
      {
	//         idLen = strlen(ID);  /* id not available, use cached copy */
	//         memcpy(id, ID, idLen);
         *result = R_IO_ERROR;
         len = sprintf(sendBuf, res, *result);  
         goto hijmp;
      }
   }
   else
   {
//      idLen = strlen(ID);  /* device is busy, use cached copy */
//      memcpy(id, ID, idLen);
      syslog(LOG_ERR, "unable to lock Device::GetDeviceID: %m\n");
      *result = R_IO_ERROR;
      len = sprintf(sendBuf, res, *result);  
      goto hijmp;
   }

   if ((idLen + HEADER_SIZE) > slen)
   {
      syslog(LOG_ERR, "invalid device id size Device::GetDeviceID: %d\n", idLen);
      *result = R_IO_ERROR;
      len = sprintf(sendBuf, res, *result);  
      goto hijmp;
   }
   len = sprintf(sendBuf, "msg=DeviceIDResult\nresult-code=%d\nlength=%d\ndata:\n", *result, idLen); 
   memcpy(&sendBuf[len], ID, idLen);
   len += idLen; 
//   sendBuf[len] = '\n';  /* for ascii data */

hijmp:
   return len;
}

int Device::GetDeviceStatus(char *sendBuf, int *result)
{
   char res[] = "msg=DeviceStatusResult\nresult-code=%d\nstatus-code=%d\nstatus-name=%s\n";
   int len=0, r;
   unsigned char status;
   char vstatus[16];

   *result = R_AOK;

   if (OpenFD<0)
   {
      syslog(LOG_ERR, "invalid data link Device::GetDeviceStatus: %d\n", OpenFD);
      *result = R_INVALID_DESCRIPTOR;
      len = sprintf(sendBuf, res, *result);  
      goto ujmp;
   }

   //   if (pthread_mutex_trylock(&mutex) == 0)
   if (pthread_mutex_lock(&mutex) == 0)
   {
      r = ioctl(OpenFD, LPGETSTATUS, &status);
      pthread_mutex_unlock(&mutex);

      if (r != 0)
      {
         syslog(LOG_ERR, "unable to read Device::GetDeviceStatus: %m\n");
         *result = R_IO_ERROR;
         len = sprintf(sendBuf, res, *result);  
         goto ujmp;
      }
   }
   else
   {
      syslog(LOG_ERR, "unable to lock Device::GetDeviceStatus: %m\n");
      *result = R_IO_ERROR;
      len = sprintf(sendBuf, res, *result);  
      goto ujmp;
   }

   vstatus[0] = 0;
   if (DEVICE_IS_OOP(status))
      strcpy(vstatus, "OutOfPaper");
   if (DEVICE_PAPER_JAMMED(status))
      strcpy(vstatus, "PaperJam");
   if (DEVICE_IO_TRAP(status))
      strcpy(vstatus, "IOTrap");

   if (vstatus[0] == 0)
      len = sprintf(sendBuf, res, *result, status, "NoFault");
   else  
      len = sprintf(sendBuf, res, *result, status, vstatus);

ujmp:
   return len;
}

int Device::WriteData(unsigned char *data, int length, int channel, char *sendBuf, int *result)
{   
   char res[] = "msg=ChannelDataOutResult\nresult-code=%d\n";
   int sLen;

   if (OpenFD<0)
   {
      syslog(LOG_ERR, "invalid data link Device::WriteData: %d\n", OpenFD);
      *result = R_INVALID_DESCRIPTOR;
      sLen = sprintf(sendBuf, res, *result);  
      goto wjmp;
   }

   if (pChannel[channel] == NULL)
   {
      syslog(LOG_ERR, "invalid channel descriptor Device::WriteData: %d\n", channel);
      *result = R_INVALID_CHANNEL_ID;
      sLen = sprintf(sendBuf, res, *result);  
      goto wjmp;
   }

   if (pthread_mutex_lock(&mutex) == 0)
   {
      sLen = pChannel[channel]->WriteData(data, length, sendBuf, result);
      pthread_mutex_unlock(&mutex);
   }
   else
   {
      syslog(LOG_ERR, "unable to lock Device::WriteData: %m\n");
      *result = R_IO_ERROR;
      sLen = sprintf(sendBuf, res, *result);  
      goto wjmp;
   }

wjmp:
   return sLen;
}

int Device::ReadData(int length, int channel, int timeout, char *sendBuf, int slen, int *result)
{   
   char res[] = "msg=ChannelDataInResult\nresult-code=%d\n";
   int sLen;

   if (OpenFD<0)
   {
      syslog(LOG_ERR, "invalid data link Device::ReadData: %d\n", OpenFD);
      *result = R_INVALID_DESCRIPTOR;
      sLen = sprintf(sendBuf, res, *result);  
      goto rjmp;
   }

   if (pChannel[channel] == NULL)
   {
      syslog(LOG_ERR, "invalid channel descriptor Device::ReadData: %d\n", channel);
      *result = R_INVALID_CHANNEL_ID;
      sLen = sprintf(sendBuf, res, *result);  
      goto rjmp;
   }

   if (pthread_mutex_lock(&mutex) == 0)
   {
      sLen = pChannel[channel]->ReadData(length, timeout, sendBuf, slen, result);
      pthread_mutex_unlock(&mutex);
   }
   else
   {
      syslog(LOG_ERR, "unable to lock Device::ReadData: %m\n");
      *result = R_IO_ERROR;
      sLen = sprintf(sendBuf, res, *result);  
      goto rjmp;
   }

rjmp:
   return sLen;
}

//Device::NewChannel
//!  Create channel object given the requested socket id and service name.
/*!
******************************************************************************/
Channel *Device::NewChannel(unsigned char sockid, char *sn)
{
   Channel *pC=NULL;
   int i, n, mode;

   /* Check for existing name service already open. */
   for (i=1, n=0; i<MAX_CHANNEL && n<ChannelCnt; i++)
   {
      if (pChannel[i] != NULL)
      {
         n++;
         if (strcasecmp(sn, pChannel[i]->GetService()) == 0)
         {
            if (sockid == PML_CHANNEL)
            {
               pC = pChannel[i];
               pC->SetClientCnt(pC->GetClientCnt()+1);    /* same channel, re-use it (PML only) */
            }
            goto bugout;
         }
      }
   }

   if (ChannelCnt >= MAX_CHANNEL)
      goto bugout;

   /* Get requested IO mode. */
   if (sockid == PRINT_CHANNEL)
      mode = GetPrintMode();
   else
      mode = GetMfpMode();

   /* Make sure requested io mode matches any current io mode. */
   if (ChannelCnt && ChannelMode != mode)
      goto bugout;  /* requested io mode does not match current */

   /* Look for unused slot in channel array. Note, slot 0 is unused. */
   for (i=1; i<MAX_CHANNEL; i++)
   {
      if (pChannel[i] == NULL)
      {
         if (mode == RAW_MODE)
            pC = new RawChannel(this);  /* constructor sets ClientCnt=1 */
         else if (mode == MLC_MODE)
            pC = new MlcChannel(this);  /* constructor sets ClientCnt=1 */
         else 
            pC = new Dot4Channel(this);  /* constructor sets ClientCnt=1 */

         pC->SetIndex(i);
         pC->SetSocketID(sockid);   /* static socket id is valid for MLC not 1284.4 */
         pC->SetService(sn);
         pChannel[i] = pC;
         ChannelCnt++;
         ChannelMode = mode;
         break;
      }
   }     

bugout:
   return pC;
}

//Device::DelChannel
//!  Remove channel object given the channel decriptor.
/*!
******************************************************************************/
int Device::DelChannel(int chan)
{
   Channel *pC = pChannel[chan];

   pC->SetClientCnt(pC->GetClientCnt()-1);
   if (pC->GetClientCnt() <= 0)
   {
      delete pC;
      pChannel[chan] = NULL;
      ChannelCnt--;
   }
   return 0;
}

int Device::ChannelOpen(char *sn, int *channel, char *sendBuf, int *result)
{
   char res[] = "msg=ChannelOpenResult\nresult-code=%d\n";
   Channel *pC;
   int len=0;
   unsigned char sockid;

   if (strncasecmp(sn, "print", 5) == 0)
   {
      sockid = PRINT_CHANNEL;
   }
   else if (strncasecmp(sn, "hp-message", 10) == 0)
   {
      sockid = PML_CHANNEL;
   }
   else if (strncasecmp(sn, "hp-scan", 7) == 0)
   {
      sockid = SCAN_CHANNEL;
   }
   else if (strncasecmp(sn, "hp-fax-send", 11) == 0)
   {
      sockid = FAX_SEND_CHANNEL;
   }
   else if (strncasecmp(sn, "hp-card-access", 14) == 0)
   {
      sockid = MEMORY_CARD_CHANNEL;
   }
   else if (strncasecmp(sn, "echo", 4) == 0)
   {
      sockid = ECHO_CHANNEL;
   }
   else
   {
      syslog(LOG_ERR, "unsupported service uri:%s Device::ChannelOpen: %s %s %d\n", URI, sn, __FILE__, __LINE__);
      len = sprintf(sendBuf, res, R_INVALID_SN);
      goto bugout;
   }

   //   if (pthread_mutex_trylock(&mutex) == 0)
   if (pthread_mutex_lock(&mutex) == 0)
   {
      if ((pC = NewChannel(sockid, sn)) == NULL)
      {
         syslog(LOG_ERR, "service busy uri:%s Device::ChannelOpen: %s %s %d\n", URI, sn, __FILE__, __LINE__);
         *result = R_CHANNEL_BUSY;
         len = sprintf(sendBuf, res, *result);
      }
      else
      {
         len = pC->Open(sendBuf, result);  
         *channel = pC->GetIndex();
         if (*result != R_AOK)
         {
            len = pChannel[*channel]->Close(sendBuf, result);  
            DelChannel(*channel);
            *result = R_IO_ERROR;
            len = sprintf(sendBuf, res, *result);  
         }
      }
      pthread_mutex_unlock(&mutex);
   }
   else
   {
      syslog(LOG_ERR, "unable to lock uri:%s Device::ChannelOpen: %m %s %d\n", URI, __FILE__, __LINE__);
      *result = R_IO_ERROR;
      len = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

bugout:
   return len;
}

int Device::ChannelClose(int channel, char *sendBuf, int *result)
{
   Channel *pC = pChannel[channel];
   char res[] = "msg=ChannelCloseResult\nresult-code=%d\n";
   int len=0;

   if (pC == NULL)
   {
      syslog(LOG_ERR, "invalid channel descriptor uri:%s Device::ChannelClose: %d\n", URI, channel);
      *result = R_INVALID_CHANNEL_ID;
      len = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

   //   if (pthread_mutex_trylock(&mutex) == 0)
   if (pthread_mutex_lock(&mutex) == 0)
   {
      if (pC->GetClientCnt()==1)
      {
         len = pC->Close(sendBuf, result);  
      }
      else
      {
         *result = R_AOK;
         len = sprintf(sendBuf, res, *result);  
      }
      DelChannel(channel);
      pthread_mutex_unlock(&mutex);
   }
   else
   {
      syslog(LOG_ERR, "unable to lock uri:%s Device::ChannelClose: %m\n", URI);
      *result = R_IO_ERROR;
      len = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

bugout:
   return len;
}

