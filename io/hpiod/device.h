/*****************************************************************************\

  device.h - base class for all devices 
 
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

#ifndef _DEVICE_H
#define _DEVICE_H

class Channel;

/* Channel attributes that must remain persistant for life of the device object. */
typedef struct
{
   unsigned short h2psize;  /* host to peripheral packet size in bytes */
   unsigned short p2hsize;  /* peripheral to host packet size in bytes */
} ChannelAttributes;

//Device
//! Abstract base class that encapsulates common device services. Each Device
//! has a unique URI. Multiple clients can open a Device. 
/*!
******************************************************************************/
class Device
{
friend class Channel;
friend class MlcChannel;
friend class JetDirectChannel;

protected:
   char URI[LINE_SIZE];
   int OpenFD;            /* kernal file descriptor from Open */ 
   int ClientCnt;           /* number of clients using this device */
   int Index;             /* System::pDevice[index] of this object */
   char ID[1024];         /* device id */
   pthread_mutex_t mutex;

   Channel *pChannel[MAX_CHANNEL];
   int ChannelCnt;
   virtual Channel *NewChannel(unsigned char sockid, char *io_mode, char *flow_ctl);
   int DelChannel(int i);
   int ChannelMode;            /* raw | mlc */
   int MlcUp;
   int CurrentProtocol;
   ChannelAttributes CA[MAX_SOCKETID];

   System *pSys;
   virtual int DeviceID(char *buffer, int size);
   int SFieldPrinterState(char *id);
   int PowerUp();

public:
   Device(System *pSys);
   virtual ~Device();

   inline int GetIndex() { return Index; }
   inline void SetIndex(int i) { Index=i; }
   inline int GetClientCnt() { return ClientCnt; }
   inline void SetClientCnt(int i) { ClientCnt=i; }
   inline int GetOpenFD() { return OpenFD; }
   inline char *GetURI() { return URI; }
   inline void SetURI(char *uri) { strcpy(URI, uri); }
   inline char *GetID() { return ID; }
   inline int GetChannelMode() { return ChannelMode; }
   virtual int Open(char *sendBuf, int *result);
   virtual int Close(char *sendBuf, int *result);
   int ChannelOpen(char *sn, char *io_mode, char *flow_ctl, int *channel_result, char *sendBuf, int *result);
   int ChannelClose(int channel, char *sendBuf, int *result);
   int GetDeviceID(char *sendBuf, int sendBufLength, int *result);
   virtual int GetDeviceStatus(char *sendBuf, int *result);
   virtual int WriteData(unsigned char *data, int length, int channel, char *sendBuf, int *result);
   virtual int ReadData(int length, int channel, int timeout, char *sendBuf, int sendBufLength, int *result);   
}; //Device

//UsbDevice
//! Class that encapsulates common usb device services.
/*!
******************************************************************************/
class UsbDevice : public Device
{
public:
   UsbDevice(System *pSys) : Device(pSys) {}
}; //RawDevice


//JetDirectDevice
//! Class that encapsulates common JetDirect device services.
/*!
******************************************************************************/
class JetDirectDevice : public Device
{
protected:
   char IP[LINE_SIZE];
   int Port;      /* jetdirect port specified by uri */

   Channel *NewChannel(unsigned char sockid, char *io_mode, char *unused);
   int DeviceID(char *buffer, int size);
   int GetSnmpStr(char *oid, char *buffer, int size);

public:

   JetDirectDevice(System *pSys) : Device(pSys) {}

   inline char *GetIP() { return IP; }
   inline int GetPort() { return Port; }
   int Open(char *sendBuf, int *result);
   int Close(char *sendBuf, int *result);
   int GetDeviceStatus(char *sendBuf, int *result);
   int WriteData(unsigned char *data, int length, int channel, char *sendBuf, int *result);
   int ReadData(int length, int channel, int timeout, char *sendBuf, int sendBufLength, int *result);   
}; //JetDirectDevice

#endif // _DEVICE_H

