/************************************************************************************\

  mfpdtf.h - HP Multi-Function Peripheral Data Transfer Format filter.

  (c) 2001-2004 Copyright Hewlett-Packard Development Company, LP

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

  Current Author: Don Welch
  Contributing Author: David Paschal

\************************************************************************************/

#if !defined( __MFPDTF_H__ )
#define __MFPDTF_H__

#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>


enum MfpdtfImageRecordID_e { MFPDTF_ID_START_PAGE = 0,
                             MFPDTF_ID_RASTER_DATA = 1,
                             MFPDTF_ID_END_PAGE = 2 };

struct MfpdtfFixedHeader_s
{
        unsigned char   blockLength[4]; /* Includes header(s). */
        unsigned char   headerLength[2];    /* Just header(s). */
        unsigned char   dataType;
        unsigned char   pageFlags;
}               __attribute__(( packed) );

struct MfpdtfImageRasterDataHeader_s
{
        unsigned char   traits;         /* Unused. */
        unsigned char   byteCount[2];
}               __attribute__(( packed) );

struct MfpdtfImageStartPageRecord_s
{
        unsigned char   encoding;
        unsigned char   pageNumber[2];
        struct
        {
                unsigned char   pixelsPerRow[2];
                unsigned char   bitsPerPixel[2];
                unsigned char   rowsThisPage[4];
                unsigned char   xres[4];
                unsigned char   yres[4];
        } black, color;
}               __attribute__(( packed) );

struct MfpdtfImageEndPageRecord_s
{
        unsigned char   unused[3];
        struct
        {
                unsigned char   numberOfRows[4];
        } black, color;
}               __attribute__(( packed) );

struct Mfpdtf_s
{
        //ptalChannel_t   chan;
        int deviceid;
        int channelid;
        int fdLog;              /* <0 means not (yet) open. */
        int logOffset;

        struct
        {
                struct timeval                          timeout;
                int                                     simulateImageHeaders;

                int                                     lastServiceResult;
                int                                     dataType;           /* <0 means not (yet) valid. */
                int                                     arrayRecordCount;
                int                                     arrayRecordSize;
                int                                     fixedBlockBytesRemaining;   /* Also generic data. */
                int                                     innerBlockBytesRemaining;   /* Image or array data. */
                int                                     dontDecrementInnerBlock;

                struct MfpdtfFixedHeader_s              fixedHeader;
                int                                     lenVariantHeader;
                union  MfpdtfVariantHeader_u *          pVariantHeader;
                struct MfpdtfImageStartPageRecord_s     imageStartPageRecord;
                struct MfpdtfImageRasterDataHeader_s    imageRasterDataHeader;
                struct MfpdtfImageEndPageRecord_s       imageEndPageRecord;
        } read;
};

typedef struct Mfpdtf_s * Mfpdtf_t;

#define MFPDTF_RESULT_NEW_PAGE                 0x00000001
#define MFPDTF_RESULT_END_PAGE                 0x00000002
#define MFPDTF_RESULT_NEW_DOCUMENT             0x00000004
#define MFPDTF_RESULT_END_DOCUMENT             0x00000008

#define MFPDTF_RESULT_END_STREAM               0x00000010
#define MFPDTF_RESULT_RESERVED_20              0x00000020
#define MFPDTF_RESULT_RESERVED_40              0x00000040
#define MFPDTF_RESULT_RESERVED_80              0x00000080

#define MFPDTF_RESULT_00000100                 0x00000100
#define MFPDTF_RESULT_READ_TIMEOUT             0x00000200
#define MFPDTF_RESULT_READ_ERROR               0x00000400
#define MFPDTF_RESULT_OTHER_ERROR              0x00000800

#define MFPDTF_RESULT_ERROR_MASK               0x00000E00

#define MFPDTF_RESULT_NEW_DATA_TYPE            0x00001000
#define MFPDTF_RESULT_NEW_VARIANT_HEADER       0x00002000
#define MFPDTF_RESULT_GENERIC_DATA_PENDING     0x00004000
#define MFPDTF_RESULT_ARRAY_DATA_PENDING       0x00008000

#define MFPDTF_RESULT_NEW_START_OF_PAGE_RECORD 0x00010000
#define MFPDTF_RESULT_IMAGE_DATA_PENDING       0x00020000
#define MFPDTF_RESULT_NEW_END_OF_PAGE_RECORD   0x00040000
#define MFPDTF_RESULT_00080000                 0x00080000

#define MFPDTF_RESULT_INNER_DATA_PENDING       0x00028000

enum MfpdtfDataType_e { MFPDTF_DT_UNKNOWN = 0,
                        MFPDTF_DT_FAX_IMAGES = 1,
                        MFPDTF_DT_SCANNED_IMAGES = 2,
                        MFPDTF_DT_DIAL_STRINGS = 3,
                        MFPDTF_DT_DEMO_PAGES = 4,
                        MFPDTF_DT_SPEED_DIALS = 5,
                        MFPDTF_DT_FAX_LOGS = 6,
                        MFPDTF_DT_CFG_PARMS = 7,
                        MFPDTF_DT_LANG_STRS = 8,
                        MFPDTF_DT_JUNK_FAX_CSIDS = 9, /* MFPDTF_DT_DIAL_STRINGS */
                        MFPDTF_DT_REPORT_STRS = 10, /* MFPDTF_DT_LANG_STRS    */
                        MFPDTF_DT_FONTS = 11,
                        MFPDTF_DT_TTI_BITMAP = 12,
                        MFPDTF_DT_COUNTERS = 13,
                        MFPDTF_DT_DEF_PARMS = 14, /* MFPDTF_DT_CFG_PARMS    */
                        MFPDTF_DT_SCAN_OPTIONS = 15,
                        MFPDTF_DT_FW_JOB_TABLE = 17 };
#define MFPDTF_DT_MASK_IMAGE \
    ((1<<MFPDTF_DT_FAX_IMAGES) | \
     (1<<MFPDTF_DT_SCANNED_IMAGES) | \
     (1<<MFPDTF_DT_DEMO_PAGES))

enum MfpdtfImageEncoding_e { MFPDTF_RASTER_BITMAP                                  = 0,
                             MFPDTF_RASTER_GRAYMAP = 1,
                             MFPDTF_RASTER_MH = 2,
                             MFPDTF_RASTER_MR = 3,
                             MFPDTF_RASTER_MMR = 4,
                             MFPDTF_RASTER_RGB = 5,
                             MFPDTF_RASTER_YCC411 = 6,
                             MFPDTF_RASTER_JPEG = 7,
                             MFPDTF_RASTER_PCL = 8,
                             MFPDTF_RASTER_NOT = 9 };


union MfpdtfVariantHeader_u
{
        struct MfpdtfVariantHeaderFaxDataArtoo_s
        {
                unsigned char   majorVersion;   /* 1 */
                unsigned char   minorVersion;   /* 0 */
                unsigned char   dataSource; /* unknown=0,prev,host,fax,pollfax,scanner */
                unsigned char   dataFormat; /* unknown=0,ASCII=3,CCITT_G3=10 */
                unsigned char   dataCompression;    /* native=1,MH,MR,MMR */
                unsigned char   pageResolution; /* fine=0,std,CCITT300,CCITT400 */
                unsigned char   pageSize;       /* unknown=0 */
                unsigned char   pixelsPerRow[2];
                unsigned char   year;
                unsigned char   month;
                unsigned char   day;
                unsigned char   hour;
                unsigned char   minute;
                unsigned char   second;
                unsigned char   T30_CSI[20];
                unsigned char   T30_SUB[20];
        }               __attribute__(( packed) )                            faxArtoo;

        struct MfpdtfVariantHeaderFaxDataSolo_s
        {
                unsigned char   majorVersion;   /* 1 */
                unsigned char   minorVersion;   /* 1 */
                unsigned char   dataSource;
                unsigned char   dataFormat;
                unsigned char   dataCompression;
                unsigned char   pageResolution;
                unsigned char   pageSize;
                unsigned char   pixelsPerRow[2];
                unsigned char   year;
                unsigned char   month;
                unsigned char   day;
                unsigned char   hour;
                unsigned char   minute;
                unsigned char   second;
                unsigned char   suppressTTI;
                unsigned char   T30_CSI[20];
                unsigned char   T30_SUB[20];
                unsigned char   T30_PWD[20];
        }               __attribute__(( packed) )                            faxSolo;

        struct MfpdtfVariantHeaderFaxData_s
        {
                unsigned char   majorVersion;
                unsigned char   minorVersion;
                /* TODO: Finish. */
        }               __attribute__(( packed) )                            fax;

        struct MfpdtfVariantHeaderImageData_s
        {
                unsigned char   majorVersion;
                unsigned char   minorVersion;
                unsigned char   sourcePages[2];
                unsigned char   copiesPerPage[2];
                unsigned char   zoomFactor[2];
                unsigned char   jpegQualityFactor[2];
        }               __attribute__(( packed) ) image;

        struct MfpdtfVariantHeaderArrayData_s
        {
                unsigned char   majorVersion;
                unsigned char   minorVersion;
                unsigned char   recordCount[2];
                unsigned char   recordSize[2];
        } __attribute__(( packed) ) array;
} __attribute__(( packed) );

Mfpdtf_t        MfpdtfAllocate( /*ptalChannel_t chan */int deviceid, int channelid );
int             MfpdtfDeallocate( Mfpdtf_t mfpdtf );
int             MfpdtfSetChannel( Mfpdtf_t mfpdtf, /*ptalChannel_t chan */ int channelid );
int             MfpdtfLogToFile( Mfpdtf_t mfpdtf, char * filename );
int             MfpdtfReadGetTimeout( Mfpdtf_t mfpdtf );
int             MfpdtfReadSetTimeout( Mfpdtf_t mfpdtf, int seconds );
int             MfpdtfReadGetSimulateImageHeaders( Mfpdtf_t mfpdtf );
int             MfpdtfReadSetSimulateImageHeaders( Mfpdtf_t mfpdtf,
                                                   int simulateImageHeaders );
int             MfpdtfReadStart( Mfpdtf_t mfpdtf );
int             MfpdtfReadService( Mfpdtf_t mfpdtf );
int             MfpdtfReadGetDataType( Mfpdtf_t mfpdtf );
int             MfpdtfReadIsImageData( Mfpdtf_t mfpdtf );
int             MfpdtfReadIsArrayData( Mfpdtf_t mfpdtf );
int             MfpdtfReadGetArrayRecordCountSize( Mfpdtf_t mfpdtf,
                                                   int * pCount,
                                                   int * pSize );
int             MfpdtfReadGetFixedBlockBytesRemaining( Mfpdtf_t mfpdtf );
int             MfpdtfReadGetInnerBlockBytesRemaining( Mfpdtf_t mfpdtf );
int             MfpdtfReadGetLastServiceResult( Mfpdtf_t mfpdtf );
int             MfpdtfReadGetVariantHeader( Mfpdtf_t mfpdtf,
                                            union MfpdtfVariantHeader_u * buffer,
                                            int maxlen );
int             MfpdtfReadGetStartPageRecord( Mfpdtf_t mfpdtf,
                                              struct MfpdtfImageStartPageRecord_s * buffer,
                                              int maxlen );
int             MfpdtfReadGetEndPageRecord( Mfpdtf_t mfpdtf,
                                            struct MfpdtfImageEndPageRecord_s * buffer,
                                            int maxlen );
int             MfpdtfReadGeneric( Mfpdtf_t mfpdtf,
                                   unsigned char * buffer,
                                   int datalen );
int             MfpdtfReadInnerBlock( Mfpdtf_t mfpdtf,
                                      unsigned char * buffer,
                                      int countdown );


#endif
