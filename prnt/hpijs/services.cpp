/*****************************************************************************\
    services.cpp : HP Inkjet Server

    Copyright (c) 2001 - 2004, Hewlett-Packard Co.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:
    1. Redistributions of source code must retain the above copyright
       notice, this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.
    3. Neither the name of the Hewlett-Packard nor the names of its
       contributors may be used to endorse or promote products derived
       from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
    IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
    OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
    IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
    NOT LIMITED TO, PATENT INFRINGEMENT; PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
    HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
    STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
    IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.
\*****************************************************************************/

#include <sys/stat.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <syslog.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include "header.h"
#include "ijs.h"
#include "ijs_server.h"
#include "hpijs.h"
#include "services.h"
#include "hpiom.h"

int UXServices::InitDuplexBuffer()
{
    /* Calculate duplex page buffer */
    CurrentRaster = ph.height - 1;  /* Height = physical page in pixels */
    RastersOnPage = (BYTE **) new BYTE[(ph.height) * sizeof (BYTE *)];
    KRastersOnPage = (BYTE **) new BYTE[(ph.height) * sizeof (BYTE *)];
    for (int i = 0; i < ph.height; i++)
    {
       RastersOnPage[i] = NULL;
       KRastersOnPage[i] = NULL;
    }
    return 0;
}

int UXServices::SendBackPage()
{
    DRIVER_ERROR    err;
    int i = CurrentRaster+1;

    while (i < ph.height)
    {
       if (KRGB)
       {
          if ((err = pJob->SendRasters(KRastersOnPage[i], RastersOnPage[i])) != NO_ERROR)
            return err;
       }
       else
       {
          if ((err = pJob->SendRasters(RastersOnPage[i])) != NO_ERROR)
            return err;
       }

       if (RastersOnPage[i])
           delete [] RastersOnPage[i];
       if (KRastersOnPage[i])
           delete [] KRastersOnPage[i];
       i++;
    }

    CurrentRaster = ph.height - 1;   /* reset raster index */

    return 0;
}

static unsigned char xmask[] =
{
   0x80,    /* x=0 */
   0x40,    /* 1 */
   0x20,    /* 2 */
   0x10,    /* 3 */
   0x08,    /* 4 */
   0x04,    /* 5 */
   0x02,    /* 6 */
   0x01     /* 7 */
};

int UXServices::ProcessRaster(char *raster, char *k_raster)
{
    if (!((pPC->QueryDuplexMode() == DUPLEXMODE_BOOK) && pPC->RotateImageForBackPage() && BackPage))
    {
       if (KRGB)
          return pJob->SendRasters((unsigned char *)k_raster, (unsigned char *)raster);
       else
          return pJob->SendRasters((unsigned char *)raster);
    }
    else
    {
        if (CurrentRaster < 0)
           return -1;

        BYTE   *new_raster;
        int    new_raster_size;
        int    i,w,last_bit;

        if (raster == NULL)
        {
           RastersOnPage[CurrentRaster] = NULL;
        }
        else
        {
           new_raster_size = pPC->InputPixelsPerRow() * 3;
           new_raster = new BYTE[new_raster_size];
           if (new_raster == 0)
           {
               bug("unable to create duplex buffer, size=%d: %m\n", new_raster_size);
               return -1;
           }
           memset(new_raster, 0xFF, new_raster_size);
           RastersOnPage[CurrentRaster] = new_raster;
           BYTE *p = new_raster + new_raster_size - 3;
           for (i = 0; i < new_raster_size; i += 3)
           {
               memcpy (p, raster+i, 3);  /* rotate rgb image */
               p -= 3;
           }
        }

        if (k_raster == NULL)
        {
           KRastersOnPage[CurrentRaster] = NULL;
        }
        else
        {
           new_raster_size = (pPC->InputPixelsPerRow() + 7) >> 3;
           new_raster = new BYTE[new_raster_size];
           if (new_raster == 0)
           {
               bug("unable to create black duplex buffer, size=%d: %m\n", new_raster_size);
               return -1;
           }
           memset(new_raster, 0, new_raster_size);
           KRastersOnPage[CurrentRaster] = new_raster;
           w = pPC->InputPixelsPerRow();
           last_bit = w & 7;
           for (i=0; i<w; i++)
           {
               if (k_raster[i>>3] & xmask[i&7])
                  new_raster[(w-(last_bit+i))>>3] |= xmask[(w-(last_bit+i))&7];  /* rotate k image */
           }
        }

        CurrentRaster--;

        return 0;
    }
}

UXServices::UXServices():SystemServices()
{
   char *hpDev;

   constructor_error = NO_ERROR;
   hpFD = -1;
   OldStatus = 0x55;

   // instead of InitDeviceComm(), just do...
   IOMode.bDevID = IOMode.bStatus = FALSE;   /* uni-di support is default */

   /* Check for CUPS environment and HP backend. */
   if ((hpDev = getenv("DEVICE_URI")) != NULL)
   {
      if (strncmp(hpDev, "hp:", 3) == 0)
      {
         if ((hpFD = OpenHP(hpDev)) >= 0)
         {
            InitDeviceComm();            /* lets try bi-di support */
         }
         if(IOMode.bDevID == FALSE)
         {
            bug("unable to set bi-di for hp backend\n");
         }
      }
   }

   Quality = 0;     /* normal */
   MediaType = 0;   /* plain */
   ColorMode = 2;   /* color */
   PenSet = DUMMY_PEN;
   
   RastersOnPage = 0;
   pPC = NULL;
   pJob = NULL;
   Duplex = 0;
   Tumble = 0;
   FullBleed = 0;
   FirstRaster = 1;
   MediaPosition = sourceTrayAuto;
   Model = -1;
   strcpy(ph.cs, "sRGB");
   VertAlign = -1;
}

UXServices::~UXServices()
{
    if (RastersOnPage)
        delete [] RastersOnPage;
   if (hpFD >= 0)
      CloseHP(hpFD);   
}

DRIVER_ERROR UXServices::ToDevice(const BYTE * pBuffer, DWORD * Count)
{
   /* Write must be not-buffered, don't use streams */
   if (write(OutputPath, pBuffer, *Count) != (ssize_t)*Count) 
   {
      bug("unable to write to output, fd=%d, count=%d: %m\n", OutputPath, *Count);
      return IO_ERROR;
   }

   *Count = 0;
   return NO_ERROR;
}

BOOL UXServices::GetStatusInfo (BYTE * bStatReg)
{
   if (ReadHPStatus(hpFD, (char *)bStatReg, 1) == 1)
      return TRUE;
   return FALSE;
}

DRIVER_ERROR UXServices::ReadDeviceID (BYTE * strID, int iSize)
{
   if (ReadHPDeviceID(hpFD, (char *)strID, iSize) < 3)
      return IO_ERROR;
   return NO_ERROR;
}

BOOL UXServices::GetVerticalAlignmentValue(BYTE* cVertAlignVal)
{
   if (VertAlign == -1)
      return FALSE;

   *cVertAlignVal = (BYTE)VertAlign;
   return TRUE;
}

BOOL UXServices::GetVertAlignFromDevice()
{
   if ((VertAlign = ReadHPVertAlign(hpFD)) == -1)
      return FALSE;
   return TRUE;
}

const char * UXServices::GetDriverMessage (DRIVER_ERROR err)
{
   const char *p=NULL;

	/* Map driver error to text message. TODO: text needs to be localized. */
   switch(err)
   {
      case(WARN_MODE_MISMATCH):
         p = "printmode mismatch with pen, tray, etc.";
         break;
      case(WARN_LOW_INK_BOTH_PENS):
         p = "both pens have low ink";
         break;
      case(WARN_LOW_INK_BLACK):
         p = "black pen has low ink";
         break;
      case(WARN_LOW_INK_COLOR):
         p = "color pen has low ink";
         break;
      case(WARN_LOW_INK_PHOTO):
         p = "photo pen has low ink";
         break;
      case(WARN_LOW_INK_GREY):
         p = "grey pen has low ink";
         break;
      case(WARN_LOW_INK_BLACK_PHOTO):
         p = "black photo has low ink";
         break;
      case(WARN_LOW_INK_COLOR_PHOTO):
         p = "color photo pen has low ink";
         break;
      case(WARN_LOW_INK_GREY_PHOTO):
         p = "grey photo pen has low ink";
         break;
      case(WARN_LOW_INK_COLOR_GREY):
         p = "grey pen has low ink";
         break;
      case(WARN_LOW_INK_COLOR_GREY_PHOTO):
         p = "color grey photo pen has low ink";
         break;
      case(WARN_LOW_INK_COLOR_BLACK_PHOTO):
         p = "color back pen has low ink";
         break;
      case(WARN_LOW_INK_CYAN):
         p = "cyan has low ink";
         break;
      case(WARN_LOW_INK_MAGENTA):
         p = "magenta has low ink";
         break;
      case(WARN_LOW_INK_YELLOW):
         p = "yellow has low ink";
         break;
      case(WARN_LOW_INK_MULTIPLE_PENS):
         p = "more that one ink is low";
         break;
      case(WARN_FULL_BLEED_UNSUPPORTED):
         p = "fullbleed is not supported";
         break;
      case(WARN_FULL_BLEED_3SIDES):
         p = "fullbleed is 3 sides";
         break;
      case(WARN_FULL_BLEED_PHOTOPAPER_ONLY):
         p = "fullbleed photo paper only";
         break;
      case(WARN_FULL_BLEED_3SIDES_PHOTOPAPER_ONLY):
         p = "fullbleed 3 sides photo paper only";
         break;
      case(WARN_ILLEGAL_PAPERSIZE):
         p = "illegal paper size";
         break;
      case(WARN_INVALID_MEDIA_SOURCE):
         p = "invalid media source";
         break;
      default:
         p = "driver error";
         bug("driver error=%d\n", err);
         break;
   }
   return p;
}

int UXServices::MapPaperSize(float width, float height)
{
   int i, r, size;
   float dx, dy;

   /* Map gs paper sizes to APDK paper sizes, or do custom. */
   size = CUSTOM_SIZE;
   for (i=0; i<MAX_PAPER_SIZE; i++)
   {
      r = pPC->SetPaperSize((PAPER_SIZE)i);

      if (r != NO_ERROR)
         continue;

      dx = width > pPC->PhysicalPageSizeX() ? width - pPC->PhysicalPageSizeX() : pPC->PhysicalPageSizeX() - width;
      dy = height > pPC->PhysicalPageSizeY() ? height - pPC->PhysicalPageSizeY() :  pPC->PhysicalPageSizeY() - height;

      if ((dx < 0.05) && (dy < 0.05))
      {
         size = i;   /* found standard paper size */
         break;
      }
   }

   if (size == CUSTOM_SIZE)
      pPC->SetCustomSize(width, height);

   if ((r = pPC->SetPaperSize((PAPER_SIZE)size, FullBleed)) != NO_ERROR)
   {
      if (r > 0)
         bug("unable to set paper size=%d, err=%d\n", size, r);
      else 
         bug("warning setting paper size=%d, err=%d\n", size, r);
      return -1;
   }

   return 0; 
}