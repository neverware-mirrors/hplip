/*****************************************************************************\

  jetdirect.cpp - JetDirect channel class 
 
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

static const int PrintPort[] = { 0, 9100, 9101, 9102 };
static const int ScanPort[] = { 0, 9290, 9291, 9292 };
static const int GenericPort[] = { 0, 9220, 9221, 9222 };

JetDirectChannel::JetDirectChannel(Device *pDev) : Channel(pDev)
{
   Socket = -1;
}

int JetDirectChannel::ReadReply()
{
   char tmpBuf[HEADER_SIZE];
   MsgAttributes ma;
   int len, num=0, result;
   char *tail;

   len = ReadData(sizeof(tmpBuf)-1, 2, tmpBuf, sizeof(tmpBuf), &result);
   tmpBuf[len] = 0;
   pDev->pSys->ParseMsg(tmpBuf, len, &ma);

   if (ma.result == 0)
      num = strtol((char *)ma.data, &tail, 10);

   return num;
}

int JetDirectChannel::Open(char *sendBuf, int *result)
{
   struct sockaddr_in pin;  
   JetDirectDevice *pD = (JetDirectDevice *)pDev;
   char buf[LINE_SIZE];
   int r, len;

   *result = R_IO_ERROR;

   /* If _not_ PML establish TCP/IP connection (PML will use UDP/IP via SNMP). */
   if (GetSocketID() != PML_CHANNEL)
   {
      bzero(&pin, sizeof(pin));  
      pin.sin_family = AF_INET;  
      pin.sin_addr.s_addr = inet_addr(pD->GetIP());  

      if (GetSocketID() == PRINT_CHANNEL)
      {
         pin.sin_port = htons(PrintPort[pD->GetPort()]);
         if ((Socket = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
         {  
            syslog(LOG_ERR, "unable to open print socket %d JetDirectChannel::Open: %m\n", Socket);  
            goto bugout;  
         }  
         if (connect(Socket, (struct sockaddr *)&pin, sizeof(pin)) == -1) 
         {  
            syslog(LOG_ERR, "unable to connect to print socket %d JetDirectChannel::Open: %m\n", Socket);  
            goto bugout;  
         }  
      }
#if 0
      else if (GetSocketID() == SCAN_CHANNEL)
      {
         pin.sin_port = htons(ScanPort[pD->GetPort()]);
         if ((Socket = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
         {  
            syslog(LOG_ERR, "unable to open scan socket %d JetDirectChannel::Open: %m\n", Socket);  
            goto bugout;  
         }  
         if (connect(Socket, (struct sockaddr *)&pin, sizeof(pin)) == -1) 
         {  
            syslog(LOG_ERR, "unable to connect to scan socket %d JetDirectChannel::Open: %m\n", Socket);  
            goto bugout;  
         }  
      }
#endif
      else if (GetSocketID() == MEMORY_CARD_CHANNEL)
      {
         pin.sin_port = htons(GenericPort[pD->GetPort()]);
         if ((Socket = socket(AF_INET, SOCK_STREAM, 0)) == -1) 
         {  
            syslog(LOG_ERR, "unable to open photo card socket %d JetDirectChannel::Open: %m\n", Socket);  
            goto bugout;  
         }  
         if (connect(Socket, (struct sockaddr *)&pin, sizeof(pin)) == -1) 
         {  
            syslog(LOG_ERR, "unable to connect to photo card socket %d JetDirectChannel::Open: %m\n", Socket);  
            goto bugout;  
         } 
         
         r = ReadReply();
         if (r != 220)
         {  
            syslog(LOG_ERR, "invalid photo card response %d socket %d JetDirectChannel::Open: line %d\n", r, Socket, __LINE__);  
            goto bugout;  
         } 

         len = sprintf(buf, "open %d\n", GetSocketID());
         send(Socket, buf, len, 0);
         r = ReadReply();
         if (r != 200)
         {  
            syslog(LOG_ERR, "invalid photo card response %d socket %d JetDirectChannel::Open: line %d\n", r, Socket, __LINE__);  
            goto bugout;  
         } 

         len = sprintf(buf, "data\n");
         send(Socket, "data\n", len, 0);
         r = ReadReply();
         if (r != 200)
         {  
            syslog(LOG_ERR, "invalid photo card response %d socket %d JetDirectChannel::Open: line %d\n", r, Socket, __LINE__);  
            goto bugout;  
         } 
      }
      else 
      {  
         syslog(LOG_ERR, "unsupported service %d JetDirectChannel::Open\n", GetSocketID());
         *result = R_INVALID_SN;
         goto bugout;
      }  
   }

   *result = R_AOK;

bugout:

   return sprintf(sendBuf, "msg=ChannelOpenResult\nresult-code=%d\nchannel-id=%d\n", *result, Index);  
}

int JetDirectChannel::Close(char *sendBuf, int *result)
{
   *result = R_AOK;

   if (Socket >= 0)
      close(Socket);
   Socket = -1;  

   return sprintf(sendBuf, "msg=ChannelCloseResult\nresult-code=%d\n", *result);
}

int JetDirectChannel::WriteData(unsigned char *data, int length, char *sendBuf, int *result)
{
   char res[] = "msg=ChannelDataOutResult\nresult-code=%d\nbytes-written=%d\n"; 
   int len, size, sLen, total=0;
   struct timeval tmo;
   fd_set master;
   fd_set writefd;
   int maxfd, ret;

   *result=R_IO_ERROR;

   if (Socket<0)
   {
      syslog(LOG_ERR, "invalid data link JetDirectChannel::WriteData: %d\n", Socket);
      goto bugout;
   }

   FD_ZERO(&master);
   FD_SET(Socket, &master);
   maxfd = Socket;
   tmo.tv_sec = EXCEPTION_TIMEOUT;
   tmo.tv_usec = 0;
   size = length;

   while (size > 0)
   {
      writefd = master;
      if ((ret = select(maxfd+1, NULL, &writefd, NULL, &tmo)) == 0)
      {
         len = -1;
         goto bugout;   /* timeout */
      }
      len = send(Socket, data+total, size, 0);
      if (len < 0)
      {
         syslog(LOG_ERR, "unable to JetDirectChannel::WriteData: %m\n");
         goto bugout;
      }
      size-=len;
      total+=len;
   }
   
   *result = R_AOK;

bugout:
   sLen = sprintf(sendBuf, res, *result, total);  

   return sLen;
}

//JetdirectChannel::ReadData
//! ReadData() tries to read "length" bytes from the peripheral.  
//! The returned read count may be zero (timeout, no data available), less than "length" or equal "length".
//!
//! The "timeout" specifies how many seconds to wait for a data packet. 
/*!
******************************************************************************/
int JetDirectChannel::ReadData(int length, int timeout, char *sendBuf, int sendBufLength, int *result)
{
   char res[] = "msg=ChannelDataInResult\nresult-code=%d\n";
   int len=0, sLen;
   char buffer[BUFFER_SIZE];
   struct timeval tmo;
   fd_set master;
   fd_set readfd;
   int maxfd, ret;

   *result=R_IO_ERROR;

   if (Socket<0)
   {
      syslog(LOG_ERR, "invalid data link JetDirectChannel::ReadData: %d\n", Socket);
      sLen = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

   if (length > sendBufLength)
   {
      syslog(LOG_ERR, "invalid data size JetDirectChannel::ReadData: %d\n", length);
      sLen = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

   FD_ZERO(&master);
   FD_SET(Socket, &master);
   maxfd = Socket;
   tmo.tv_sec = timeout;
   tmo.tv_usec = 0;

   readfd = master;
   if ((ret = select(maxfd+1, &readfd, NULL, NULL, &tmo)) == 0)
   {
      syslog(LOG_ERR, "timeout JetDirectChannel::ReadData: %m\n");
      sLen = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

   len = recv(Socket, buffer, length, 0);

   if (len < 0)
   {
      syslog(LOG_ERR, "unable to JetDirectChannel::ReadData: %m\n");
      sLen = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

   *result=R_AOK;
   sLen = sprintf(sendBuf, "msg=ChannelDataInResult\nresult-code=%d\nlength=%d\ndata:\n", *result, len); 
   memcpy(&sendBuf[sLen], buffer, len);
   sLen += len; 

bugout:
   return sLen;
}

