/*****************************************************************************\
  djgenericvip.h : Interface for the generic VIP printer class

  Copyright (c) 2001 - 2002, Hewlett-Packard Co.
  All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions
  are met:
  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
  3. Neither the name of Hewlett-Packard nor the names of its
     contributors may be used to endorse or promote products derived
     from this software without specific prior written permission.

  THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
  WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
  MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN
  NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
  TO, PATENT INFRINGEMENT; PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
  ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
  THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
\*****************************************************************************/


#ifndef APDK_DJ_GENERIC_VIP_H
#define APDK_DJ_GENERIC_VIP_H

APDK_BEGIN_NAMESPACE

//DJGenericVIP
//!
/*!
\internal
******************************************************************************/
class DJGenericVIP : public DJ9xxVIP
{
public:
    DJGenericVIP (SystemServices* pSS, BOOL proto = FALSE);

    DRIVER_ERROR VerifyPenInfo ();
    virtual BOOL FullBleedCapable (PAPER_SIZE ps, FullbleedType  *fbType, float *xOverSpray, float *yOverSpray,
                                   float *fLeftOverSpray, float *fTopOverSpray);
	virtual BOOL UseGUIMode (PrintMode *pPrintMode);
	virtual PAPER_SIZE MandatoryPaperSize ();
    virtual PHOTOTRAY_STATE PhotoTrayEngaged (BOOL bQueryPrinter);
    //! Returns TRUE if a hagaki feed is present in printer.
    virtual BOOL HagakiFeedPresent(BOOL bQueryPrinter);

#ifdef APDK_AUTODUPLEX
    //!Returns TRUE if duplexer and hagaki feed (combined) unit is present in printer.

    virtual BOOL HagakiFeedDuplexerPresent(BOOL bQueryPrinter);
#endif


private:
	virtual void AdjustModeSettings (BOOL bDoFullBleed, MEDIATYPE ReqMedia,
									 MediaType *medium, Quality *quality);

}; //DJGenericVIP

class VIPFastDraftMode : public PrintMode
{
public:
    VIPFastDraftMode ();
}; // VIPFastDraftMode

#if defined(APDK_DJGENERICVIP) && defined (APDK_DJ9xxVIP)
//! DJGenericVIPProxy
/*!
******************************************************************************/
class DJGenericVIPProxy : public PrinterProxy
{
public:
    DJGenericVIPProxy() : PrinterProxy(
        "GenericVIP",                       // family name
        "photosmart 7150\0"                 // Twister
        "photosmart 7350\0"                 // Dorothy
		"photosmart 7345\0"                 // Dorothy
        "photosmart 7550\0"                 // Tinman
        "deskjet 5550\0"                    // Malibu
        "deskjet 5551\0"                    // Malibu Japan
        "dj450\0"                           // Crystal
		"deskjet 450\0"                     // Crystal Plus
		"hp business inkjet 1100\0"         // 1100 - Crick
   		"HP Business Inkjet 1200\0"         // 1200 - Crick MLK
        "photosmart 7960\0"                 // Gran Prix
        "photosmart 7760\0"                 // Bonneville
		"photosmart 7660\0"                 // Catalina
        "photosmart 7260\0"                 // Crayola
		"photosmart 7268\0"                 // Crayola
        "deskjet 5600\0"                    // Malibu +
        "deskjet 5100\0"                    // Malibu Mid
		"deskjet 5800\0"                    // Gepetto
		"deskjet 9600\0"                    // Euclid
		"Deskjet 6500\0"                    // Dolphin
		"Deskjet 5700\0"                    // Pelican Plus
		"Deskjet 6800\0"                    // Marlin
		"Photosmart 7400\0"					// Yogi
		"Photosmart 8100\0"                 // Shaggy
		"Photosmart 8400\0"                 // Squiddly
#ifdef APDK_MLC_PRINTER
        "PSC 2100\0"                        // Bonzai               
        "PSC 2150\0"
        "PSC 2200\0"
        "psc 2300\0"                        // Bonzai + Lo
        "psc 2400\0"                        // Bonzai + Mid
        "psc 2500\0"                        // Bonzai + Hi
		"PSC 2170\0"                        // Bonzai 3P
		"OfficeJet 6100\0"                  // Solar
		"OfficeJet 6150\0"                  // Solar Japan
		"Officejet 7400\0"                  // Atlas Super
		"Officejet 7300\0"                  // Atlas Mid
		"Officejet 7200\0"                  // Atlas Base
		"Officejet 6200\0"                  // Balboa Base
		"psc 1600\0"                        // Shazam Base
		"psc 2350\0"                        // Shazam High
		"Photosmart 2600\0"                 // Ares Mid
		"Photosmart 2700\0"                 // Ares Super
#endif
    ) {m_iPrinterType = eDJGenericVIP;}
    inline Printer* CreatePrinter(SystemServices* pSS) const { return new DJGenericVIP(pSS); }
	inline PRINTER_TYPE GetPrinterType() const { return eDJGenericVIP;}
	inline unsigned int GetModelBit() const { return 0x80;}
};
#endif

APDK_END_NAMESPACE

#endif  // APDK_DJ_GENERIC_VIP_H
