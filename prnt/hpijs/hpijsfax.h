/*****************************************************************************\
    hpijsfax.h : HP Inkjet Server

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

#ifdef  HAVE_LIBHPIP

#ifndef HPIJSFAX_H
#define HPIJSFAX_H

#define IJS_MAX_PARAM 256

#ifdef __cplusplus
extern "C" {
#endif

extern int bug(const char *fmt, ...);

#ifdef __cplusplus
}
#endif

#define HPLIPPUTBYTES(bytearr, val) \
		bytearr[0] = (val & 0xFF000000) >> 24; \
		bytearr[1] = (val & 0x00FF0000) >> 16; \
		bytearr[2] = (val & 0x0000FF00) >> 8;  \
		bytearr[3] = (val & 0x000000FF)

/*
typedef	struct
{
    char		szHeader[8];
    uint32_t	uiVersion;
	uint32_t	uiNumPages;				// >= 1
	uint32_t	uiHorzRes;				// 204
	uint32_t	uiVertRes;				// 98 or 196
	uint32_t	uiPageSize;				// Letter - 1, A4 - 2, Legal - 3
	uint32_t	uiOutputQuality;		// Standard - 1 or Fine - 2
	uint32_t	uiReserved;
} HPLIPFaxFileHeader;

typedef struct
{
	uint32_t	uiPageNum;
	uint32_t	uiPixelsPerRow;
	uint32_t	uiNumOfRowsThisPage;
	uint32_t	uiImageSize;			// Size of fax data only, in bytes
	uint32_t	uiReserved;
} HPLIPFaxPageHeader;
*/

class HPIJSFax
{

public:
	HPIJSFax ()
	{
		iQuality = 1;
		iColorMode = 1;
		iMediaType = 0;
		iPaperSize = 1;
		iFirstRaster = 1;
		fPaperWidth = 8.5;
		fPaperHeight = 11.0;
	}
	char	*PrinterModel ();
	void	SetOutputPath (int fd)
	{
		iOutputPath = fd;
	}
	void    SetPaperSize (float w, float h)
	{
		fPaperWidth = w;
		fPaperHeight = h;
		if (fabs (8.5 - w) < 0.05 && fabs (11.0 - w) < 0.05)
		{
		    iPaperSize = 1;
		}
		else if (fabs (8.27 - w) < 0.05 && fabs (11.69 - h) < 0.05)
		{
		    iPaperSize = 2;
		}
		else if (fabs (8.5 - w) < 0.05 && fabs (14.0 - h) < 0.05)
		{
		    iPaperSize = 3;
		}
	}
	void	SetPaperWidth (float w)
	{
	    fPaperWidth = w;
	}
	void	SetPaperHeight (float h)
	{
		fPaperHeight = h;
	}
	int		GetQuality ()
	{
		return iQuality;
	}
	void	SetQuality (int iQ)
	{
	    iQuality = iQ;
	}
	void	SetMediaType (int iM)
	{
	    iMediaType = iM;
	}
	void	SetColorMode (int iCm)
	{
		iColorMode = iCm; // 1 - Monochrome, 2 - Color
	}
	void	SetFirstRaster (int iFirst)
	{
		iFirstRaster = iFirst;
	}

	int		GetColorMode ()
	{
		return iColorMode;
	}
	int		GetMediaType ()
	{
		return iMediaType;
	}
	int		GetPaperSize ()
	{
		return iPaperSize;
	}
	float	GetPaperWidth ()
	{
		return fPaperHeight;
	}
	float	GetPaperHeight ()
	{
		return fPaperHeight;
	}
	int		IsFirstRaster ()
	{
		return iFirstRaster;
	}
	float	PrintableStartX ()
	{
		//return (float) 0.25;
		return (float) 0.0;
	}
	float	PrintableStartY ()
	{
		return (float) 0.0;
	}
	float	PrintableWidth ()
	{
		return fPaperWidth;
	}
	float	PrintableHeight ()
	{
		return fPaperHeight;
	}
	float	PhysicalPageSizeX ()
	{
		return fPaperWidth;
	}
	float	PhysicalPageSizeY ()
	{
		return fPaperHeight;
	}
	int		EffectiveResolutionX ()
	{
		return 200;
	}
	int		EffectiveResolutionY ()
	{
		if (iQuality == 2)
		{
		    return 200;
		}
		return 100;
	}

    IjsPageHeader	ph;
	int				iOutputPath;
private:
    int		iQuality;
	int		iColorMode;
	int		iMediaType;
	int		iPaperSize;
	float	fPaperWidth;
	float	fPaperHeight;
	int		iFirstRaster;
	char	szPrinterModelName[64];
};

#endif        /* HPIJSFAX_H */

#endif // HAVE_LIBHPIP

