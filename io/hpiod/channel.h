/*****************************************************************************\

  channel.h - base class for MLC and Raw channels 
 
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

#ifndef _CHANNEL_H
#define _CHANNEL_H

//Channel
//! Class that encapsulates common channel services. Channels
//! have a unique service name and only one service name can be open at a time.
/*!
******************************************************************************/
class Channel
{
   unsigned char sockid;    /* static socket id */

protected:
   Device *pDev;
   int ClientCnt;           /* number of clients using this device */
   int Index;             /* Device::pChannel[index] of this object */

public:
   Channel(Device *pDev);
   virtual ~Channel();

   inline int GetIndex() { return Index; }
   inline void SetIndex(int i) { Index=i; }
   inline int GetClientCnt() { return ClientCnt; }
   inline void SetClientCnt(int i) { ClientCnt=i; }
   inline unsigned char GetSocketID() { return sockid; }
   inline void SetSocketID(unsigned char s) { sockid=s; }
   virtual int Open(char *sendBuf, int *result);
   virtual int Close(char *sendBuf, int *result);
   virtual int WriteData(unsigned char *data, int length, char *sendBuf, int *result);
   virtual int ReadData(int length, int timeout, char *sendBuf, int sendBufLength, int *result);   

}; //Channel

//RawChannel
//! Class that encapsulates raw channel services.
/*!
******************************************************************************/
class RawChannel : public Channel
{
public:
   RawChannel(Device *pDev) : Channel(pDev) {}
}; //RawChannel

//JetdirectChannel
//! Class that encapsulates jetdirect channel services.
/*!
******************************************************************************/
class JetDirectChannel : public Channel
{
   int Socket;
   int ReadReply();

public:
   JetDirectChannel(Device *pDev);

   int Open(char *sendBuf, int *result);
   int Close(char *sendBuf, int *result);
   int WriteData(unsigned char *data, int length, char *sendBuf, int *result);
   int ReadData(int length, int timeout, char *sendBuf, int sendBufLength, int *result);   
}; //JetdirectChannel

/*
 * See mlc.h for MlcChannel class definition.
 */

#endif // _CHANNEL_H

