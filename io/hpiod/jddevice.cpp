/*****************************************************************************\

  jddevice.cpp - JetDirect device class 
 
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

static const char *kStatusOID = "1.3.6.1.4.1.11.2.3.9.1.1.7.0";            /* device id oid */
static const char *SnmpPort[] = { "","public.1","public.2","public.3" };

#ifdef HAVE_LIBSNMP
#include <net-snmp/net-snmp-config.h>
#include <net-snmp/net-snmp-includes.h>
#include <net-snmp/types.h>

int JetDirectDevice::GetSnmpStr(char *szoid, char *buffer, int size)
{
   struct snmp_session session, *ss=NULL;
   struct snmp_pdu *pdu=NULL;
   struct snmp_pdu *response=NULL;
   int len=0;
   oid anOID[MAX_OID_LEN];
   size_t anOID_len = MAX_OID_LEN;
   struct variable_list *vars;
   int status;
   int count=1;

   init_snmp("snmpapp");

   snmp_sess_init(&session );                   /* set up defaults */
   session.peername = IP;
   session.version = SNMP_VERSION_1;
   session.community = (unsigned char *)SnmpPort[Port];
   session.community_len = strlen((const char *)session.community);
   SOCK_STARTUP;
   ss = snmp_open(&session);                     /* establish the session */
   if (ss == NULL)
      goto bugout;

   pdu = snmp_pdu_create(SNMP_MSG_GET);
   read_objid(szoid, anOID, &anOID_len);
   snmp_add_null_var(pdu, anOID, anOID_len);
  
   /* Send the request and get response. */
   status = snmp_synch_response(ss, pdu, &response);

   if (status == STAT_SUCCESS && response->errstat == SNMP_ERR_NOERROR) 
   {
      vars = response->variables;
      if (vars->type == ASN_OCTET_STR) 
      {
         len = (vars->val_len < size) ? vars->val_len : size-1;
         memcpy(buffer, vars->val.string, len);
         buffer[len] = 0;
      }
   }

bugout:
   if (response != NULL)
      snmp_free_pdu(response);
   if (ss != NULL)
      snmp_close(ss);
    SOCK_CLEANUP;
    return len;
}

#else

int JetDirectDevice::GetSnmpStr(char *szoid, char *buffer, int size)
{
   syslog(LOG_ERR, "no JetDirect support enabled\n");
   return 0;
}

#endif

int JetDirectDevice::DeviceID(char *buffer, int size)
{
   int len=0, maxSize;

   maxSize = (size > 1024) ? 1024 : size;   /* RH8 has a size limit for device id */

   if ((len = GetSnmpStr((char *)kStatusOID, buffer, size)) == 0)
      syslog(LOG_ERR, "unable to read JetDirectDevice::DeviceID\n");

   return len; /* length does not include zero termination */
}

int JetDirectDevice::Open(char *sendBuf, int *result)
{
   char dev[255];
   char uriModel[128];
   char model[128];
   char *p, *tail;
   int len=0;
   unsigned char nullByte=0;

   *result = R_AOK;

   if (pthread_mutex_trylock(&mutex) != 0)
      goto bugout;   /* device is already open. */ 

   //   if (ClientCnt==1)
   if (ID[0] == 0)
   {
      pSys->GetURIDataLink(URI, IP, sizeof(IP));

      if ((p = strstr(URI, "port=")) != NULL)
         Port = strtol(p+5, &tail, 10);
      else
         Port = 1;
      if (Port > 3)
      {
         *result = R_IO_ERROR;
         goto blackout;
      }

      len = DeviceID(ID, sizeof(ID));  /* get new copy and cache it  */ 

      if (len == 0)
      {
         *result = R_IO_ERROR;
         goto blackout;
      }

      /* Powerup??? */
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
   pSys->GetURIModel(URI, uriModel, sizeof(uriModel));
   if (strcmp(uriModel, "ANY") != 0)
   {
      pSys->GetModel(ID, model, sizeof(model));
      if (strcmp(uriModel, model) != 0)
      {
         *result = R_INVALID_DEVICE_NODE;  /* probably a laserjet, or different device plugged in */  
         syslog(LOG_ERR, "invalid model %s != %s JetdirectDevice::Open\n", uriModel, model);
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

int JetDirectDevice::Close(char *sendBuf, int *result)
{
   char res[] = "msg=DeviceCloseResult\nresult-code=%d\n";
   int len=0;

   *result = R_AOK;

   //   if (pthread_mutex_trylock(&mutex) != 0)
   //      goto bugout;   /* device is still in use */

   //   pthread_mutex_unlock(&mutex);

   //bugout:
   len = sprintf(sendBuf, res, *result);  

   return len;
}

int JetDirectDevice::GetDeviceStatus(char *sendBuf, int *result)
{
   char res[] = "msg=DeviceStatusResult\nresult-code=%d\nstatus-code=%d\nstatus-name=%s\n";
   int len=0, r;
   unsigned char status = NFAULT_BIT;

   *result = R_AOK;

   len = sprintf(sendBuf, res, *result, status, "NoFault");  /* no 8-bit status */

   return len;
}

int JetDirectDevice::WriteData(unsigned char *data, int length, int channel, char *sendBuf, int *result)
{   
   char res[] = "msg=ChannelDataOutResult\nresult-code=%d\n";
   int sLen;

   if (pChannel[channel] == NULL)
   {
      syslog(LOG_ERR, "invalid channel descriptor JetDirectDevice::WriteData: %d\n", channel);
      *result = R_INVALID_CHANNEL_ID;
      sLen = sprintf(sendBuf, res, *result);  
      goto wjmp;
   }

   sLen = pChannel[channel]->WriteData(data, length, sendBuf, result);

wjmp:
   return sLen;
}

int JetDirectDevice::ReadData(int length, int channel, int timeout, char *sendBuf, int slen, int *result)
{   
   char res[] = "msg=ChannelDataInResult\nresult-code=%d\n";
   int sLen;

   if (pChannel[channel] == NULL)
   {
      syslog(LOG_ERR, "invalid channel descriptor JetDirectDevice::ReadData: %d\n", channel);
      *result = R_INVALID_CHANNEL_ID;
      sLen = sprintf(sendBuf, res, *result);  
      goto rjmp;
   }

   sLen = pChannel[channel]->ReadData(length, timeout, sendBuf, slen, result);

rjmp:
   return sLen;
}

//JetdirectDevice::NewChannel
//!  Create channel object given the service name.
/*!
******************************************************************************/
Channel *JetDirectDevice::NewChannel(unsigned char sockid, char *io_mode, char *unused)
{
   Channel *pC=NULL;
   int i, n, mode;

   /* Check for existing name service already open. */
   for (i=1, n=0; i<MAX_CHANNEL && n<ChannelCnt; i++)
   {
      if (pChannel[i] != NULL)
      {
         n++;
         if (sockid == pChannel[i]->GetSocketID())
         {
            pC = pChannel[i];   /* same channel, re-use it */
            pC->SetClientCnt(pC->GetClientCnt()+1);
            goto bugout;
         }
      }
   }

   if (ChannelCnt >= MAX_CHANNEL)
      goto bugout;

   /* Look for unused slot in channel array. Note, slot 0 is unused. */
   for (i=1; i<MAX_CHANNEL; i++)
   {
      if (pChannel[i] == NULL)
      {
         pC = new JetDirectChannel(this);
         pC->SetIndex(i);
         pC->SetSocketID(sockid);
         pChannel[i] = pC;
         ChannelCnt++;
         ChannelMode = mode;
         break;
      }
   }     

bugout:
   return pC;
}





