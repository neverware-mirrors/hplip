/*****************************************************************************\

  mlc.h - MLC channel class 
 
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

#ifndef _MLC_H
#define _MLC_H

#define MAX_COMMAND_PACKET 64
#define MAX_SENDER_DATA BUFFER_SIZE
#define MAX_RECEIVER_DATA BUFFER_SIZE

enum MLC_COMMAND
{
  MLC_INIT = 0,
  MLC_OPEN_CHANNEL = 1,
  MLC_CLOSE_CHANNEL = 2,
  MLC_CREDIT = 3,
  MLC_CREDIT_REQUEST = 4,
  MLC_DEBIT = 5,
  MLC_DEBIT_REQUEST = 6,
  MLC_CONFIG_SOCKET = 7,
  MLC_EXIT = 8,
  MLC_ERROR = 0x7f
};

#pragma pack(1)

typedef struct
{
   unsigned char hsid;   /* host socket id */
   unsigned char psid;   /* peripheral socket id */
   unsigned short length;   /* packet length (includes header) */ 
   unsigned char credit;   /* data packet credit, reserved if command */
   unsigned char status;  /* upper layer status */
} MLCHeader;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
   unsigned char rev;
} MLCInit;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
   unsigned char result;
   unsigned char rev;
} MLCInitReply;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
} MLCExit;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
   unsigned char result;
} MLCExitReply;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
   unsigned char socket;      /* socket id */
   unsigned short h2psize;    /* host-to-peripheral packet size */
   unsigned short p2hsize;    /* peripheral-to-host packet size */
   unsigned char status;      /* status level */
} MLCConfigSocket;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
   unsigned char result;
   unsigned short h2psize;    /* host-to-peripheral packet size */
   unsigned short p2hsize;    /* peripheral-to-host packet size */
   unsigned char status;      /* status level */
} MLCConfigSocketReply;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
   unsigned char hsocket;      /* host socket id */
   unsigned char psocket;      /* peripheral socket id */
   unsigned short credit;
} MLCOpenChannel;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
   unsigned char result;
   unsigned short credit;
} MLCOpenChannelReply;

typedef struct
{
   MLCHeader h;
   unsigned char cmd;
   unsigned char hsocket;      /* host socket id */
   unsigned char psocket;      /* peripheral socket id */
} MLCCloseChannel;

typedef MLCExitReply MLCCloseChannelReply;
typedef MLCExitReply MLCReply;
typedef MLCExit MLCCmd;
typedef MLCOpenChannel MLCCredit;
typedef MLCExitReply MLCCreditReply;
typedef MLCOpenChannel MLCCreditRequest;
typedef MLCOpenChannelReply MLCCreditRequestReply;
typedef MLCExitReply MLCError;

#pragma pack()

class Channel;

//MlcChannel
//! Class that encapsulates common channel services requiring MLC.
/*!
******************************************************************************/
class MlcChannel : public Channel
{
//   unsigned short h2psize;  /* host to peripheral packet size in bytes */
//   unsigned short p2hsize;  /* peripheral to host packet size in bytes */
   unsigned short credit;  /* host to peripheral credit */
   unsigned short p2hcredit;  /* peripheral to host credit */   
//   int CurrentProtocol;
   unsigned char rbuf[MAX_RECEIVER_DATA];  /* read packet buffer */
   int rindex;
   int rcnt;
   int miser;

public:
   MlcChannel(Device *pDev);

   inline unsigned short GetH2PSize() { return pDev->CA[GetSocketID()].h2psize; }
   inline void SetH2PSize(unsigned short i) { pDev->CA[GetSocketID()].h2psize=i; }
   inline unsigned short GetP2HSize() { return pDev->CA[GetSocketID()].p2hsize; }
   inline void SetP2HSize(unsigned short i) { pDev->CA[GetSocketID()].p2hsize=i; }
   inline unsigned short GetP2HCredit() { return p2hcredit; }
   inline void SetP2HCredit(unsigned short i) { p2hcredit=i; }
   inline unsigned short GetH2PCredit() { return credit; }
   inline void SetH2PCredit(unsigned short i) { credit=i; }
   inline unsigned short GetMiser() { return miser; }
   inline void SetMiser(int i) { miser=i; }

   int MlcSocket2Channel(unsigned char sockid);
   int MlcForwardReply(int fd, unsigned char *buf, int size);
   int MlcExecReverseCmd(int fd, unsigned char *buf);
   int MlcReverseCmd(int fd);
   int MlcReverseReply(int fd, unsigned char *buf, int bufsize);
   int MlcCredit(int fd, unsigned short credit);
   int MlcCreditRequest(int fd, unsigned short credit);
   int MlcForwardData(int fd, int sockid, unsigned char *buf, int size);
   int MlcReverseData(int fd, int sockid, unsigned char *buf, int bufsize, int timeout);
   int MlcInit(int fd);
   int MlcExit(int fd);
   int MlcConfigSocket(int fd);
   int MlcOpenChannel(int fd);
   int MlcCloseChannel(int fd);
   int Open(char *sendBuf, int *result);
   int Close(char *sendBuf, int *result);
   int WriteData(unsigned char *data, int length, char *sendBuf, int *result);
   int ReadData(int length, int timeout, char *sendBuf, int sendBufLength, int *result);   
   int CutBuf(char *sendBuf, int length);

}; //MlcDevice

#endif // _MLC_H

