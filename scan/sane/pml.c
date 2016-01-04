/************************************************************************************\

  pml.c - HP SANE backend for multi-function peripherals (libsane-hpaio)

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
  Original Author: David Paschal 

\************************************************************************************/

#include "hpaio.h"

int PmlSetID( PmlObject_t obj, char * oid )
{
    int len = 0;    /* TODO: Do we need this parameter? */

    //DBG( 0,  "PmlSetID(obj=0x%8.8X)\n", obj );

    if( !len )
    {
        len = strlen( oid );
        if( !len )
        {
            len++;
        }
    }
    if( len > PML_MAX_OID_LEN )
    {
        return ERROR;
    }

    /* TODO: Disable trap (if enabled) on old OID. */

    memcpy( obj->oid, oid, len );
    obj->oid[len] = 0;

    obj->numberOfValidValues = 0;

    /* TODO: Clear out other trap-related fields. */

    //DBG( 0,  "PmlSetID(obj=0x%8.8X) returns OK.\n", obj );
    return OK;
}



int PmlSetAsciiID( PmlObject_t obj, char * s )
{
    char oid[PML_MAX_OID_LEN + 1];
    int len = 0, c;

    while( 1 )
    {
        while( *s == '.' )
        {
            s++;
        }
        if( !*s )
        {
            break;
        }
        if( *s<'0' || *s>'9' )
        {
            return ERROR;
        }
        c = atoi( s );
        if( c<0 || c>255 )
        {
            return ERROR;
        }
        if( len >= PML_MAX_OID_LEN )
        {
            return ERROR;
        }
        oid[len++] = c;
        while( *s >= '0' && *s <= '9' )
        {
            s++;
        }
    }
    oid[len] = 0;

    return PmlSetID( obj, oid );
}

int PmlGetID( PmlObject_t obj, char * buffer, int maxlen )
{
    if( maxlen <= 1 )
    {
        return ERROR;
    }
    buffer[maxlen - 1] = 0;
    strncpy( buffer, obj->oid, maxlen );
    
    if( buffer[maxlen - 1] )
    {
        return ERROR;
    }

    return OK;
}

PmlValue_t PmlGetLastValue( PmlObject_t obj )
{
    if( obj->numberOfValidValues <= 0 )
    {
        return 0;
    }
    return &obj->value[obj->indexOfLastValue];
}

PmlValue_t PmlGetPreviousLastValue( PmlObject_t obj )
{
    if( obj->numberOfValidValues <= 1 )
    {
        return 0;
    }

    return &obj->value[( PML_MAX_OID_VALUES + obj->indexOfLastValue - 1 ) % PML_MAX_OID_VALUES];
}

PmlValue_t PmlPrepareNextValue( PmlObject_t obj )
{
    obj->indexOfLastValue = ( obj->indexOfLastValue + 1 ) %
                            PML_MAX_OID_VALUES;
    if( obj->numberOfValidValues < PML_MAX_OID_VALUES )
    {
        obj->numberOfValidValues++;
    }
    return &obj->value[obj->indexOfLastValue];
}

void PmlClearOldValues( PmlObject_t obj )
{
    if( obj->numberOfValidValues )
    {
        obj->numberOfValidValues = 1;
    }
}

int PmlSetPrefixValue( PmlObject_t obj,
                           int type,
                           char * prefix,
                           int lenPrefix,
                           char * value,
                           int lenValue )
{
    PmlValue_t v = PmlPrepareNextValue( obj );
    int r = ERROR;

    /*DBG( 0,  "PmlSetPrefixValue(obj=0x%8.8X,type=0x%4.4X,"
                    "lenPrefix=%d,lenValue=%d)\n",
                    obj,
                    type,
                    lenPrefix,
                    lenValue );*/

    if( lenPrefix < 0 ||
        lenValue<0 ||
        ( lenPrefix + lenValue )>PML_MAX_VALUE_LEN )
    {
        /*DBG( 0, "PmlSetPrefixValue(obj=0x%8.8X): "
                       "invalid lenPrefix=%d and/or lenValue=%d!\n",
                       obj,
                       lenPrefix,
                       lenValue );*/
        goto abort;
    }

    v->type = type;
    v->len = lenPrefix + lenValue;
    if( lenPrefix )
    {
        memcpy( v->value, prefix, lenPrefix );
    }
    if( lenValue )
    {
        memcpy( v->value + lenPrefix, value, lenValue );
    }
    v->value[lenPrefix + lenValue] = 0;

    r = OK;
abort:
    /*DBG( 0,  "PmlSetPrefixValue(obj=0x%8.8X) returns %d.\n",
                    obj,
                    r );*/
    return r;
}

int PmlSetValue( PmlObject_t obj, int type, char * value, int len )
{
    return PmlSetPrefixValue( obj, type, 0, 0, value, len );
}

int PmlSetStringValue( PmlObject_t obj,
                           int symbolSet,
                           char * value,
                           int len )
{
    char prefix[2];
    prefix[0] = ( symbolSet >> 8 ) & 0xFF;
    prefix[1] = ( symbolSet ) & 0xFF;

    if( !len )
    {
        len = strlen( value );
    }
    return PmlSetPrefixValue( obj,
                                  PML_TYPE_STRING,
                                  prefix,
                                  2,
                                  value,
                                  len );
}

int PmlSetIntegerValue( PmlObject_t obj, int type, int value )
{
    char buffer[sizeof( int )];
    int len = sizeof( int ), i = len - 1;

    while( 1 )
    {
        buffer[i] = value & 0xFF;
        value >>= 8;
        if( !i )
        {
            break;
        }
        i--;
    }
    for( ; !buffer[i] && i < ( len ); i++ )
        ;

    return PmlSetPrefixValue( obj, type, buffer + i, len - i, 0, 0 );
}

int PmlGetType( PmlObject_t obj )
{
    PmlValue_t v = PmlGetLastValue( obj );
    if( !v )
    {
        return ERROR;
    }
    return v->type;
}

int PmlGetPrefixValue( PmlObject_t obj,
                           int * pType,
                           char * prefix,
                           int lenPrefix,
                           char * buffer,
                           int maxlen )
{
    int len;
    PmlValue_t v = PmlGetLastValue( obj );

    if( !v )
    {
        return ERROR;
    }
    if( pType )
    {
        *pType = v->type;
    }
    if( !prefix && !buffer )
    {
        return OK;
    }

    if( lenPrefix < 0 || maxlen < 0 )
    {
        return ERROR;
    }

    if( v->len > lenPrefix + maxlen )
    {
        return ERROR;
    }
    if( v->len < lenPrefix )
    {
        return ERROR;
    }

    if( lenPrefix )
    {
        memcpy( prefix, v->value, lenPrefix );
    }
    len = v->len - lenPrefix;
    if( len )
    {
        memcpy( buffer, v->value + lenPrefix, len );
    }
    if( len < maxlen )
    {
        buffer[len] = 0;
    }

    return len;
}

int PmlGetValue( PmlObject_t obj,
                     int * pType,
                     char * buffer,
                     int maxlen )
{
    return PmlGetPrefixValue( obj, pType, 0, 0, buffer, maxlen );
}

int PmlGetStringValue( PmlObject_t obj,
                           int * pSymbolSet,
                           char * buffer,
                           int maxlen )
{
    int type, len;
    unsigned char prefix[2];

    if( PmlGetPrefixValue( obj, &type, 0, 0, 0, 0 ) == ERROR )
    {
        return ERROR;
    }

    len = PmlGetPrefixValue( obj, &type, prefix, 2, buffer, maxlen );
    if( len == ERROR )
    {
        return ERROR;
    }
    if( pSymbolSet )
    {
        *pSymbolSet = ( ( prefix[0] << 8 ) | prefix[1] );
    }

    return len;
}

int PmlGetIntegerValue( PmlObject_t obj, int * pType, int * pValue )
{
    int type;
    unsigned char svalue[sizeof( int )];
    int accum = 0, i, len;

    if( !pType )
    {
        pType = &type;
    }

    len = PmlGetPrefixValue( obj, pType, 0, 0, svalue, sizeof( int ) );
    /*if( len == ERROR )
            {
                return ERROR;
            }*/

    for( i = 0; i < len; i++ )
    {
        accum = ( ( accum << 8 ) | ( svalue[i] & 0xFF ) );
    }
    if( pValue )
    {
        *pValue = accum;
    }

    return OK;
}

int PmlDoLastValuesDiffer( PmlObject_t obj )
{
    PmlValue_t vNew = PmlGetLastValue( obj );
    PmlValue_t vOld = PmlGetPreviousLastValue( obj );

    return ( vNew &&
             vOld &&
             ( vOld->type !=
               vNew->type ||
               vOld->len !=
               vNew->len ||
               memcmp( vOld->value,
                       vNew->value,
                       vOld->len ) ) );
}

int PmlSetStatus( PmlObject_t obj, int status )
{
    obj->status = status;

    return status;
}

int PmlGetStatus( PmlObject_t obj )
{
    return obj->status;
}

int PmlReadReply( /*ptalDevice_t dev,*/
                  int deviceid,
                  int channelid,
                  unsigned char * data,
                  int maxDatalen,
                  int request )
{
    //return ptalChannelRead( dev->pmlChannel, data, maxDatalen );
    return ReadChannel( deviceid, channelid, data, maxDatalen, -1 );

    /* TODO: Check for and handle traps. */
}

int PmlRequestSet( int deviceid, int channelid, PmlObject_t obj )
{
    unsigned char data[PML_MAX_DATALEN];
    int datalen=0, status=ERROR, type, pml_result;

    DBG( 0,  "PmlRequestSet(obj=0x%8.8X)\n", obj );

    PmlSetStatus(obj, PML_ERROR);
                
    datalen = PmlGetValue(obj, &type, data, sizeof(data));

    datalen = SetPml(deviceid, channelid, obj->oid, type, data, datalen, &pml_result); 

    if (datalen > 0)
    {
        PmlSetStatus(obj, pml_result);
        status = OK;
    }

    return status;
}

int PmlRequestSetRetry( int deviceid, int channelid, PmlObject_t obj, int count, int delay )
{
    int r = ERROR;

    if( count <= 0 )
    {
        count = 20;
    }
    if( delay <= 0 )
    {
        delay = 2;
    }
    while( 1 )
    {
        r = PmlRequestSet( deviceid, channelid, obj );
        
        if( r != ERROR || count <= 0 ||
            ( PmlGetStatus( obj ) != PML_ERROR_ACTION_CAN_NOT_BE_PERFORMED_NOW ) )
        {
            break;
        }
        sleep( delay );
        count--;
    }

    return r;
}

int PmlRequestGet( int deviceid, int channelid, PmlObject_t obj ) 
{
    unsigned char data[PML_MAX_DATALEN];
    int datalen=0, status=ERROR, type, pml_result;

    DBG( 0,  "PmlRequestGet(obj=0x%8.8X)\n", obj );
    
    PmlSetStatus(obj, PML_ERROR);
                
    datalen = GetPml(deviceid, channelid, obj->oid, data, sizeof(data), &type, &pml_result); 

    if (datalen > 0)
    {
        PmlSetStatus(obj, pml_result);
        PmlSetValue(obj, type, data, datalen);
        status = OK;
    }

    return status;
}

