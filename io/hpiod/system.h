/*****************************************************************************\

  system.h - class provides common system services  
 
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
  (c) 2003-2004 Copyright Hewlett-Packard Development Company, LP

\*****************************************************************************/

#ifndef _SYSTEM_H
#define _SYSTEM_H

class Device;

//System
//! Class that encapsulates common system services.
/*!
******************************************************************************/
class System
{
   int HpiodPortNumber;       /* IP port number */
   pthread_mutex_t mutex;

   Device *pDevice[MAX_DEVICE];
   int DeviceCnt;
   Device *NewDevice(char *uri);
   int DelDevice(int i);

   int UsbDiscovery(char *list, int *cnt);
   int ProbeDevices(char *sendBuf);

public:
   System();
   ~System();

   int Permsd;
   int Reset;

   inline int GetHpiodPortNumber() { return HpiodPortNumber; }
   int ReadConfig();
   int GetPair(char *buf, char *key, char *value, char **tail);
   int ParseMsg(char *buf, int len, MsgAttributes *ma);
   int ExecuteMsg(SessionAttributes *psa, char *recvBuf, int rlen, char *sendBuf, int slen);
   int GetURIDataLink(char *uri, char *buf, int bufSize);
   int GetURIModel(char *uri, char *buf, int bufSize);
   int GetURISerial(char *uri, char *buf, int bufSize);
   int GeneralizeURI(MsgAttributes *ma);
   int ModelQuery(char *uri, MsgAttributes *ma);
   int Write(int fd, const void *buf, int size);
   int Read(int fd, void *buf, int size, int sec=EXCEPTION_TIMEOUT, int usec=0);
   int IsHP(char *id);
   int GetModel(char *id, char *buf, int bufSize);
   int GetSerialNum(char *id, char *buf, int bufSize);
   int DeviceCleanUp(int index);

}; //System

#endif // _SYSTEM_H

