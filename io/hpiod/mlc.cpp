/*****************************************************************************\

  mlc.cpp - MLC channel class  
 
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

MlcChannel::MlcChannel(Device *pD) : Channel(pD)
{
   credit = p2hcredit = 0;
   //   CurrentProtocol = USB_PROTOCOL_712;
   rcnt = rindex = 0;
   miser = 0;    /* assume Gusher flow control */
}

/* Map socket id to channel index. */
int MlcChannel::MlcSocket2Channel(unsigned char sockid)
{
   int i, n;

   for (i=0, n=0; i<MAX_CHANNEL && n<pDev->ChannelCnt; i++)
   {
      if (pDev->pChannel[i] != NULL)
      {
         n++;
         if (sockid == pDev->pChannel[i]->GetSocketID())
            return i;
      }
   }
   syslog(LOG_ERR, "no channel for sockid=%d\n", sockid);
   return -1;   
}

/* Write command reply back to peripheral. */
int MlcChannel::MlcForwardReply(int fd, unsigned char *buf, int size)
{
   int len=0;

   if ((len = pDev->pSys->Write(fd, buf, size)) != size)
   {
      syslog(LOG_ERR, "unable to MlcForwarReply: %m\n");
   }   
   return len;
}

/* Execute command from peripheral. */
int MlcChannel::MlcExecReverseCmd(int fd, unsigned char *buf)
{
   MLCCmd *pCmd;
   MLCReply *pReply;
   MLCCredit *pCredit;
   MLCCreditReply *pCreditReply;
   MLCCreditRequest *pCreditReq;
   MLCCreditRequestReply *pCreditReqReply;
   MLCError *pError;
   MlcChannel *pC;
   int i, len;

   pCmd = (MLCCmd *)buf;

   if (!(pCmd->h.hsid == 0 && pCmd->h.psid == 0))
   {
     //      len = ntohs(pCmd->h.length) - sizeof(MLCHeader);
      len = ntohs(pCmd->h.length);
      syslog(LOG_ERR, "unexpected data packet: hsid=%x, psid=%x, length=%d, credit=%d, status=%x\n", pCmd->h.hsid,
                                     pCmd->h.psid, len, pCmd->h.credit, pCmd->h.status);
      sysdump(buf, len);
      return 0;  
   }

   /* Process any command. */
   switch (pCmd->cmd)
   {
      case MLC_CREDIT:
         pCredit = (MLCCredit *)buf;
         if ((i = MlcSocket2Channel(pCredit->hsocket)) >= 0)
         {
            pC = (MlcChannel *)pDev->pChannel[i];
            pC->SetH2PCredit(pC->GetH2PCredit()+ntohs(pCredit->credit));
         }
         pCreditReply = (MLCCreditReply *)buf;
         pCreditReply->h.length = htons(sizeof(MLCCreditReply));
         pCreditReply->cmd |= 0x80;
         pCreditReply->result = 0;
         MlcForwardReply(fd, (unsigned char *)pCreditReply, sizeof(MLCCreditReply)); 
         break;
      case MLC_CREDIT_REQUEST:
         pCreditReq = (MLCCreditRequest *)buf;
         syslog(LOG_ERR, "unexpected MLCCreditRequest: cmd=%x, hid=%x, pid=%x, credit=%d\n", pCreditReq->cmd,
                                         pCreditReq->hsocket, pCreditReq->psocket, ntohs(pCreditReq->credit));
         pCreditReqReply = (MLCCreditRequestReply *)buf;
         pCreditReqReply->h.length = htons(sizeof(MLCCreditRequestReply));
         pCreditReqReply->cmd |= 0x80;
         pCreditReqReply->result = 0;
         pCreditReqReply->credit = 0;
         MlcForwardReply(fd, (unsigned char *)pCreditReqReply, sizeof(MLCCreditRequestReply)); 
         break;
      case MLC_ERROR:
         pError = (MLCError *)buf;
         syslog(LOG_ERR, "unexpected MLCError: cmd=%x, result=%x\n", pError->cmd, pError->result);
         return 1;
      default:
         pReply = (MLCReply *)buf;
         syslog(LOG_ERR, "unexpected command: cmd=%x, result=%x\n", pReply->cmd, pReply->result);
         pReply->h.length = htons(sizeof(MLCReply));
         pReply->cmd |= 0x80;
         pReply->result = 1;
         MlcForwardReply(fd, (unsigned char *)pReply, sizeof(MLCReply)); 
         break;
   }
   return 0;
}

/* Get command from peripheral and processes the reverse command. */
int MlcChannel::MlcReverseCmd(int fd)
{
   unsigned char buf[MAX_COMMAND_PACKET];   
   int stat=0, len, size;
   unsigned int pklen;
   unsigned char *pBuf;
   MLCReply *pPk;

   pPk = (MLCReply *)buf;

   pBuf = buf;

   /* Read packet header. */
   size = sizeof(MLCHeader);
   while (size > 0)
   {
      if ((len = pDev->pSys->Read(fd, pBuf, size)) < 0)
      {
         syslog(LOG_ERR, "unable to read MlcReverseCmd header: %m\n");
         stat = 1;
         goto bugout;
      }
      size-=len;
      pBuf+=len;
   }

   /* Determine packet size. */
   if ((pklen = ntohs(pPk->h.length)) > sizeof(buf))
   {
      syslog(LOG_ERR, "invalid MlcReverseCmd packet size: size=%d\n", pklen);
      stat = 1;
      goto bugout;
   }

   /* Read packet data field. */
   size = pklen - sizeof(MLCHeader);
   while (size > 0)
   {
      if ((len = pDev->pSys->Read(fd, pBuf, size)) < 0)
      {
         syslog(LOG_ERR, "unable to read MlcReverseCmd data: %m\n");
         stat = 1;
         goto bugout;
      }
      size-=len;
      pBuf+=len;
   }

   stat = MlcExecReverseCmd(fd, buf);

bugout:
   return stat;
}

/*
 * Get command reply from peripheral. Waits for reply then returns. Processes any reverse commands
 * while waiting for a reply.
 */
int MlcChannel::MlcReverseReply(int fd, unsigned char *buf, int bufsize)
{
   int stat=0, len, size, pklen;
   unsigned char *pBuf;
   MLCReply *pPk;

   pPk = (MLCReply *)buf;
   
   while (1)
   {
      pBuf = buf;

      /* Read packet header. */
      size = sizeof(MLCHeader);
      while (size > 0)
      {
         if ((len = pDev->pSys->Read(fd, pBuf, size, 1, 0)) < 0)   /* wait 1 second */
         {
            syslog(LOG_ERR, "unable to read MlcReverseReply header: %m\n");
            stat = 2;  /* short timeout */
            goto bugout;
         }
         size-=len;
         pBuf+=len;
      }

      /* Determine packet size. */
      if ((pklen = ntohs(pPk->h.length)) > bufsize)
      {
         syslog(LOG_ERR, "invalid MlcReverseReply packet size: size=%d, buf=%d\n", pklen, bufsize);
         stat = 1;
         goto bugout;
      }

      /* Read packet data field. */
      size = pklen - sizeof(MLCHeader);
      while (size > 0)
      {
         if ((len = pDev->pSys->Read(fd, pBuf, size)) < 0)
         {
            syslog(LOG_ERR, "unable to read MlcReverseReply data: %m\n");
            stat = 1;
            goto bugout;
         }
         size-=len;
         pBuf+=len;
      }

      /* Check for reply. */
      if (pPk->cmd & 0x80)
         break;

      stat = MlcExecReverseCmd(fd, buf);

      if (stat != 0)
         break;

   } /* while (1) */

bugout:
   return stat;
}

int MlcChannel::MlcInit(int fd)
{
   unsigned char buf[MAX_COMMAND_PACKET];
   int stat=0, len, n, cnt;
   MLCInit *pCmd;
   MLCInitReply *pReply;

   memset(buf, 0, sizeof(buf));
   pCmd = (MLCInit *)buf;
   n = sizeof(MLCInit);
   pCmd->h.length = htons(n);
   pCmd->cmd = MLC_INIT;
   pCmd->rev = 3;
   
   if ((len = pDev->pSys->Write(fd, pCmd, n)) != n)
   {
      syslog(LOG_ERR, "unable to write MLCInit: %m\n");
      stat = 1;
      goto bugout;
   }

   cnt=0;
   while(1)
   {
      stat = MlcReverseReply(fd, buf, sizeof(buf));
      pReply = (MLCInitReply *)buf;

      if ((stat != 0) || (pReply->cmd != (0x80 | MLC_INIT)) || (pReply->result != 0))
      {
         if (errno == EIO && cnt<1)
         {
            /* hack for usblp.c 2.6.5 */
            syslog(LOG_INFO, "invalid MLCInitReply retrying...\n");
            sleep(1);   
            cnt++;
            continue;
         }
         if (stat == 2 && cnt<1)
         {
            /* hack for Tahoe */
            syslog(LOG_INFO, "invalid MLCInitReply retrying command...\n");
            pDev->pSys->Write(fd, pCmd, n);
            cnt++;
            continue;
         }
         syslog(LOG_ERR, "invalid MLCInitReply: cmd=%x, result=%x\n, revision=%x\n", pReply->cmd, pReply->result, pReply->rev);
         stat = 1;
         goto bugout;
      }
      break;
   }

bugout:
   return stat;
}

int MlcChannel::MlcExit(int fd)
{
   unsigned char buf[MAX_COMMAND_PACKET];
   int stat=0, len, n;
   MLCExit *pCmd;
   MLCExitReply *pReply;

   memset(buf, 0, sizeof(buf));
   pCmd = (MLCExit *)buf;
   n = sizeof(MLCExit);
   pCmd->h.length = htons(n);
   pCmd->cmd = MLC_EXIT;
   
   if ((len = pDev->pSys->Write(fd, pCmd, n)) != n)
   {
      syslog(LOG_ERR, "unable to write MLCExit: %m\n");
      stat = 1;
      goto bugout;
   }

   stat = MlcReverseReply(fd, buf, sizeof(buf));
   pReply = (MLCExitReply *)buf;

   if ((stat != 0) || (pReply->cmd != (0x80 | MLC_EXIT)) || (pReply->result != 0))
   {
      syslog(LOG_ERR, "invalid MLCExitReply: cmd=%x, result=%x\n", pReply->cmd, pReply->result);
      stat = 1;
      goto bugout;
   }

bugout:
   return stat;
}

int MlcChannel::MlcConfigSocket(int fd)
{
   unsigned char buf[MAX_COMMAND_PACKET];
   int stat=0, len, n;
   MLCConfigSocket *pCmd;
   MLCConfigSocketReply *pReply;

   if (GetH2PSize() > 0)
     return stat;   /* already got host/peripheral packet sizes */

   memset(buf, 0, sizeof(buf));
   pCmd = (MLCConfigSocket *)buf;
   n = sizeof(MLCConfigSocket);
   pCmd->h.length = htons(n);
   pCmd->cmd = MLC_CONFIG_SOCKET;
   pCmd->socket = GetSocketID();
   pCmd->h2psize = htons(MAX_SENDER_DATA);
   pCmd->p2hsize = htons(MAX_RECEIVER_DATA);
   pCmd->status = 0;   /* status level?? */
   
   if ((len = pDev->pSys->Write(fd, pCmd, n)) != n)
   {
      syslog(LOG_ERR, "unable to write MLCConfigSocket: %m\n");
      stat = 1;
      goto bugout;
   }

   stat = MlcReverseReply(fd, buf, sizeof(buf));
   pReply = (MLCConfigSocketReply *)buf;

   if ((stat != 0) || (pReply->cmd != (0x80 | MLC_CONFIG_SOCKET)) || (pReply->result != 0))
   {
      syslog(LOG_ERR, "invalid MLCConfigSocketReply: cmd=%x, result=%x\n", pReply->cmd, pReply->result);
      stat = 1;
      goto bugout;
   }

   SetH2PSize(ntohs(pReply->h2psize));
   SetP2HSize(ntohs(pReply->p2hsize));

bugout:
   return stat;
}

/* Write data to peripheral. */
int MlcChannel::MlcForwardData(int fd, int sockid, unsigned char *buf, int size)
{
   int stat=0, len, n;
   MLCHeader h;

   memset(&h, 0, sizeof(h));
   n = sizeof(MLCHeader) + size;
   h.length = htons(n);
   h.hsid = sockid;
   h.psid = sockid;
      
   if ((len = pDev->pSys->Write(fd, &h, sizeof(MLCHeader))) != sizeof(MLCHeader))
   {
      syslog(LOG_ERR, "unable to write MlcForwardData header: %m\n");
      stat = 1;
      goto bugout;
   }

   if ((len = pDev->pSys->Write(fd, buf, size)) != size)
   {
      syslog(LOG_ERR, "unable to write MlcForwardData: %m\n");
      stat = 1;
      goto bugout;
   }

bugout:
   return stat;
}

/* Read data from peripheral. */
int MlcChannel::MlcReverseData(int fd, int sockid, unsigned char *buf, int length, int timeout)
{
   int len, size, total;
   MLCHeader *pPk;

   pPk = (MLCHeader *)buf;

   while (1)
   {
      total = 0;

      /* Read packet header. */
      size = sizeof(MLCHeader);
      while (size > 0)
      {
         /* Use requested client timeout until we start reading. */
         if (total == 0)
            len = pDev->pSys->Read(fd, buf+total, size, timeout, 0);
         else
            len = pDev->pSys->Read(fd, buf+total, size);

         if (len < 0)
         {
            /* Got a timeout, if timeout occured after read started thats an error. */
            if (total > 0)
               syslog(LOG_ERR, "unable to read MlcReverseData header: %m\n");
            goto bugout;
         }
         size-=len;
         total+=len;
      }

      /* Determine data size. */
      size = ntohs(pPk->length) - sizeof(MLCHeader);

      if (size > length)
      {
         syslog(LOG_ERR, "invalid MlcReverseData size: size=%d, buf=%d\n", size, length);
         goto bugout;
      } 

      /* Make sure data packet is for this channel. */
      if (pPk->hsid != sockid && pPk->psid != sockid)
      {
         if (pPk->hsid == 0 && pPk->psid == 0)
         {
            /* Ok, got a command channel packet instead of a data packet, handle it... */
            while (size > 0)
            {
               if ((len = pDev->pSys->Read(fd, buf+total, size)) < 0)
               {
                  syslog(LOG_ERR, "unable to read MlcReverseData command: %m\n");
                  goto bugout;
               }
               size-=len;
               total=len;
            }
            MlcExecReverseCmd(fd, buf);
            continue;   /* try again for data packet */
         }
         else
         {
            MLCCmd *pCmd = (MLCCmd *)buf;
            syslog(LOG_ERR, "invalid MlcReverseData state: unexpected packet hsid=%x, psid=%x, cmd=%x\n", pPk->hsid, pPk->psid, pCmd->cmd);
            goto bugout;
         }
      }

      if (pPk->credit)
      {
         SetH2PCredit(GetH2PCredit() + pPk->credit);  /* note, piggy back credit is 1 byte wide */ 
      }

      total = 0;  /* eat packet header */
   
      /* Read packet data field without exception_timeout. */
      while (size > 0)
      {
         if ((len = pDev->pSys->Read(fd, buf+total, size)) < 0)
         {
            syslog(LOG_ERR, "unable to read MlcReverseData: %m\n");
            goto bugout;
         }
         size-=len;
         total+=len;
      }
      break; /* done reading data packet */
   }  /* while (1) */

bugout:
   return total;
}

int MlcChannel::MlcOpenChannel(int fd)
{
   unsigned char buf[MAX_COMMAND_PACKET];
   int stat=0, len, n;
   MLCOpenChannel *pCmd;
   MLCOpenChannelReply *pReply;

   memset(buf, 0, sizeof(buf));
   pCmd = (MLCOpenChannel *)buf;
   n = sizeof(MLCOpenChannel);
   pCmd->h.length = htons(n);
   pCmd->cmd = MLC_OPEN_CHANNEL;
   pCmd->hsocket = GetSocketID();   /* assume static socket ids */    
   pCmd->psocket = GetSocketID();
   pCmd->credit = htons(0);             /* credit sender will accept from receiver (set by MlcDevice::ReadData) */
   //   SetH2PCredit(0);                    /* initialize sender to receiver credit */
   
   if ((len = pDev->pSys->Write(fd, pCmd, n)) != n)
   {
      syslog(LOG_ERR, "unable to write MlcOpenChannel: %m\n");
      stat = 1;
      goto bugout;
   }

   stat = MlcReverseReply(fd, buf, sizeof(buf));
   pReply = (MLCOpenChannelReply *)buf;

   if ((stat != 0) || (pReply->cmd != (0x80 | MLC_OPEN_CHANNEL)) || (pReply->result != 0))
   {
      syslog(LOG_ERR, "invalid MlcOpenChannelReply: cmd=%x, result=%x\n", pReply->cmd, pReply->result);
      stat = 1;
      goto bugout;
   }

   SetH2PCredit(ntohs(pReply->credit));

bugout:
   return stat;
}

int MlcChannel::MlcCloseChannel(int fd)
{
   unsigned char buf[MAX_COMMAND_PACKET];
   int stat=0, len, n;
   MLCCloseChannel *pCmd;
   MLCCloseChannelReply *pReply;

   memset(buf, 0, sizeof(buf));
   pCmd = (MLCCloseChannel *)buf;
   n = sizeof(MLCCloseChannel);
   pCmd->h.length = htons(n);
   pCmd->cmd = MLC_CLOSE_CHANNEL;
   pCmd->hsocket = GetSocketID();   /* assume static socket ids */    
   pCmd->psocket = GetSocketID();
   
   if ((len = pDev->pSys->Write(fd, pCmd, n)) != n)
   {
      syslog(LOG_ERR, "unable to write MlcCloseChannel: %m\n");
      stat = 1;
      goto bugout;
   }

   stat = MlcReverseReply(fd, buf, sizeof(buf));
   pReply = (MLCCloseChannelReply *)buf;

   if ((stat != 0) || (pReply->cmd != (0x80 | MLC_CLOSE_CHANNEL)) || (pReply->result != 0))
   {
      syslog(LOG_ERR, "invalid MlcCloseChannelReply: cmd=%x, result=%x\n", pReply->cmd, pReply->result);
      stat = 1;
      goto bugout;
   }

bugout:
   return stat;
}

int MlcChannel::MlcCredit(int fd, unsigned short credit)
{
   unsigned char buf[MAX_COMMAND_PACKET];
   int stat=0, len, n;
   MLCCredit *pCmd;
   MLCCreditReply *pReply;

   memset(buf, 0, sizeof(buf));
   pCmd = (MLCCredit *)buf;
   n = sizeof(MLCCredit);
   pCmd->h.length = htons(n);
   pCmd->cmd = MLC_CREDIT;
   pCmd->hsocket = GetSocketID();   /* assume static socket ids */    
   pCmd->psocket = GetSocketID();
   pCmd->credit = htons(credit);                /* set peripheral to host credit */
   
   if ((len = pDev->pSys->Write(fd, pCmd, n)) != n)
   {
      syslog(LOG_ERR, "unable to write MlcCredit: %m\n");
      stat = 1;
      goto bugout;
   }

   stat = MlcReverseReply(fd, buf, sizeof(buf));
   pReply = (MLCCreditReply *)buf;

   if ((stat != 0) || (pReply->cmd != (0x80 | MLC_CREDIT)) || (pReply->result != 0))
   {
      syslog(LOG_ERR, "invalid MlcCreditReply: cmd=%x, result=%x\n", pReply->cmd, pReply->result);
      stat = 1;
      goto bugout;
   }

bugout:
   return stat;
}

int MlcChannel::MlcCreditRequest(int fd, unsigned short credit)
{
   unsigned char buf[MAX_COMMAND_PACKET];
   int stat=0, len, n;
   MLCCreditRequest *pCmd;
   MLCCreditRequestReply *pReply;

   memset(buf, 0, sizeof(buf));
   pCmd = (MLCCreditRequest *)buf;
   n = sizeof(MLCCreditRequest);
   pCmd->h.length = htons(n);
   pCmd->cmd = MLC_CREDIT_REQUEST;
   pCmd->hsocket = GetSocketID();   /* assume static socket ids */    
   pCmd->psocket = GetSocketID();
   pCmd->credit = htons(credit);                /* request host to peripheral credit */
   
   if ((len = pDev->pSys->Write(fd, pCmd, n)) != n)
   {
      syslog(LOG_ERR, "unable to write MlcCreditRequest: %m\n");
      stat = 1;
      goto bugout;
   }

   stat = MlcReverseReply(fd, buf, sizeof(buf));
   pReply = (MLCCreditRequestReply *)buf;

   if ((stat != 0) || (pReply->cmd != (0x80 | MLC_CREDIT_REQUEST)) || (pReply->result != 0))
   {
      syslog(LOG_ERR, "invalid MlcCreditRequestReply: cmd=%x, result=%x\n", pReply->cmd, pReply->result);
      stat = 1;
      goto bugout;
   }

   SetH2PCredit(GetH2PCredit()+ntohs(pReply->credit));

bugout:
   return stat;
}

int MlcChannel::Open(char *sendBuf, int *result)
{
   char res[] = "msg=OpenChannelResult\nresult-code=%d\n";
   int supportedProtocols=0;
   int twoints[2];
   int len, slen;
   unsigned i;
   unsigned char buf[255];

   *result = R_IO_ERROR;
   slen = sprintf(sendBuf, res, R_IO_ERROR);  

   /* Check for multiple opens on the same channel (ie: two clients using PML). */
   if (ClientCnt==1)
   {
      /* Initialize MLC transport if this is the first MLC channel. */
      if (pDev->ChannelCnt==1)
      {
         /* Get current USB protocol. */
         if (ioctl(pDev->GetOpenFD(), LPIOC_GET_PROTOCOLS, &twoints) >= 0)
         {
            pDev->CurrentProtocol=twoints[0];
            supportedProtocols=twoints[1]; 
#ifdef HPIOD_DEBUG
            syslog(LOG_INFO, "currentProtocol=%x supportedProtocols=%x: %s %d\n", pDev->CurrentProtocol, supportedProtocols, __FILE__, __LINE__);
#endif
         }

         /* If 7/1/3 (MLC/1284.4) protocol is available use it. */
         if (supportedProtocols & (1<<USB_PROTOCOL_713))
         {
            if (ioctl(pDev->GetOpenFD(), LPIOC_SET_PROTOCOL, USB_PROTOCOL_713) < 0) 
            {
               syslog(LOG_ERR, "unable to set %s 7/1/3: %m\n", pDev->GetURI());
               goto blackout;
            }
         }
         else if (supportedProtocols & (1<<USB_PROTOCOL_712))
         { 
            /* Emulate 7/1/3 on 7/1/2 using vendor-specific ECP channel-77. */
            if (ioctl(pDev->GetOpenFD(), LPIOC_SET_PROTOCOL, USB_PROTOCOL_712) < 0) 
            {
               syslog(LOG_ERR, "unable to set %s 7/1/2: %m\n", pDev->GetURI());
               goto blackout;
            }
            if (ioctl(pDev->GetOpenFD(), LPIOC_HP_SET_CHANNEL, 77) < 0) 
            {
               syslog(LOG_ERR, "unable to set %s chan77: %m\n", pDev->GetURI());
               goto blackout;
            }
         }
         else
         {
            syslog(LOG_ERR, "unable to set %s MLC/1284.4: not supported\n", pDev->GetURI());
            goto blackout;
         }

         /* Drain any reverse data. */
         for (i=0,len=1; len > 0 && i < sizeof(buf); i++)
            len = pDev->pSys->Read(pDev->GetOpenFD(), buf+i, 1, 0, 0);    /* no blocking */

         /* MLC initialize */
         if (MlcInit(pDev->GetOpenFD()) != 0)
            goto blackout;

         pDev->MlcUp=1;

      } /* if (pDev->ChannelCnt==1) */
 
      if (MlcConfigSocket(pDev->GetOpenFD()) != 0)
         goto blackout;

      if (MlcOpenChannel(pDev->GetOpenFD()) != 0)
         goto blackout;

   } /* if (ClientCnt==1) */

   *result = R_AOK;
   slen = sprintf(sendBuf, "msg=ChannelOpenResult\nresult-code=%d\nchannel-id=%d\n", *result, Index);

blackout:

   return slen;  
}

int MlcChannel::Close(char *sendBuf, int *result)
{
   char res[] = "msg=ChannelCloseResult\nresult-code=%d\n";
   int len=0;
   unsigned char nullByte=0;

   *result = R_AOK;

   if (ClientCnt==1)
   {
      if (pDev->MlcUp)
      {
         if (MlcCloseChannel(pDev->GetOpenFD()) != 0)
            *result = R_IO_ERROR;
      }
   }

   /* Remove MLC transport if this is the last MLC channel. */
   if (pDev->ChannelCnt==1)
   {
      if (pDev->MlcUp)
      {
         if (MlcExit(pDev->GetOpenFD()) != 0)
            *result = R_IO_ERROR;
      }
      pDev->MlcUp=0;
      memset(pDev->CA, 0, sizeof(pDev->CA));

      /* For Officejet K series and G series, leave in 7/1/3 protocol. These printers do not like being set to raw mode. */
      if (pDev->CurrentProtocol != USB_PROTOCOL_713)
      {
         ioctl(pDev->GetOpenFD(), LPIOC_HP_SET_CHANNEL, 78);  /* reset MLC (ECP channel-78) */
         pDev->pSys->Write(pDev->GetOpenFD(), &nullByte, 1);  
         ioctl(pDev->GetOpenFD(), LPIOC_HP_SET_CHANNEL, 0);   /* set raw mode (ECP channel-0) */
         ioctl(pDev->GetOpenFD(), LPIOC_SET_PROTOCOL, pDev->CurrentProtocol);
      }
   }

   len = sprintf(sendBuf, res, *result);  

   return len;
}

int MlcChannel::WriteData(unsigned char *data, int length, char *sendBuf, int *result)
{
   char res[] = "msg=ChannelDataOutResult\nresult-code=%d\nbytes-written=%d\n"; 
   int ret, len, size, sLen, dlen, total=0;

   *result=R_IO_ERROR;

   size = length;
   dlen = GetH2PSize() - sizeof(MLCHeader);
   while (size > 0)
   {
      len = (size > dlen) ? dlen : size;

      if (miser)
      {
         if (MlcCreditRequest(pDev->GetOpenFD(), 1) != 0)  /* Miser flow control */
         {
            syslog(LOG_ERR, "invalid MlcCreditRequest from peripheral\n");
            goto bugout;
         }
      }

      if (!GetH2PCredit())
      {
         ret = MlcReverseCmd(pDev->GetOpenFD());
         if (!GetH2PCredit())
         {
            if (ret == 0)
               continue;  /* Got a reverse command, but no MlcCredit, try again. */ 

            if (!miser)
            {
               /* If miser flow control works for this device, set "miser" in models.xml. */ 
               syslog(LOG_ERR, "invalid MlcCredit from peripheral, trying miser\n");
               miser = 1;    
               continue;
            } 

            syslog(LOG_ERR, "invalid MlcCredit from peripheral\n");
            goto bugout;
         }
      }

      if (MlcForwardData(pDev->GetOpenFD(), GetSocketID(), data+total, len) != 0)
      {
         goto bugout;
      }

      SetH2PCredit(GetH2PCredit()-1);
      size-=len;
      total+=len;
   }

   *result = R_AOK;

bugout:
   //   if (*result != R_AOK)
   //      pDev->MlcUp=0;
   sLen = sprintf(sendBuf, res, *result, total);  
   return sLen;
}

int MlcChannel::CutBuf(char *sendBuf, int length)
{
   char res[] =  "msg=ChannelDataInResult\nresult-code=%d\nlength=%d\ndata:\n";
   int sendLen, total;

   if (rcnt > length)
   {
      /* Return part of rbuf. */
      total = length;
      sendLen = sprintf(sendBuf, res, R_AOK, total); 
      memcpy(&sendBuf[sendLen], &rbuf[rindex], total);
      sendLen += total; 
      rindex += total;
      rcnt -= total;
   }
   else
   {
      /* Return all of rbuf. */
      total = rcnt;
      sendLen = sprintf(sendBuf, res, R_AOK, total); 
      memcpy(&sendBuf[sendLen], &rbuf[rindex], total);
      sendLen += total; 
      rindex = rcnt = 0;
   }

   return sendLen;
} 

/*
 * ReadData() tries to read "length" bytes from the peripheral. ReadData() reads data in packet size chunks. 
 * The returned read count may be zero (timeout, no data available), less than "length" or equal "length".
 *
 * ReadData() may read more the "length" if the data packet is greater than "length". For this case the
 * return value will equal "length" and the left over data will be buffered for the next ReadData() call.
 *
 * The "timeout" specifies how many seconds to wait for a data packet. Once the read of the data packet has
 * started the "timeout" is no longer used.
 */
int MlcChannel::ReadData(int length, int timeout, char *sendBuf, int sendBufLength, int *result)
{
   char res[] = "msg=ChannelDataInResult\nresult-code=%d\n";
   int sendLen;

   *result=R_IO_ERROR;

   if ((length + HEADER_SIZE) > sendBufLength)
   {
      syslog(LOG_ERR, "invalid data size MlcChannel::ReadData: %d\n", length);
      sendLen = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

   if (GetP2HSize()==0)
   {
      syslog(LOG_ERR, "invalid peripheral to host packet size MlcChannel::ReadData: %d\n", GetP2HSize());
      sendLen = sprintf(sendBuf, res, *result);  
      goto bugout;
   }

   if (rcnt)
   {
      *result=R_AOK;
      sendLen = CutBuf(sendBuf, length);
      goto bugout;
   }

   if (!GetP2HCredit())
   {
      /* Issue enough credit to the peripheral to read one data packet. */ 
      if (MlcCredit(pDev->GetOpenFD(), 1) != 0)
      {
         sendLen = sprintf(sendBuf, res, *result);  
         goto bugout;
      }     
   }

   *result=R_AOK;
   rcnt = MlcReverseData(pDev->GetOpenFD(), GetSocketID(), rbuf, sizeof(rbuf), timeout);
   sendLen = CutBuf(sendBuf, length);

   if (rcnt)
      SetP2HCredit(0); /* one data packet was read, reset credit count */

bugout:
   //   if (*result != R_AOK)
   //      pDev->MlcUp=0;
   return sendLen;
}

