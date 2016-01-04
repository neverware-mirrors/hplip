#!/usr/bin/env python
#
# $Revision: 1.27 $
# $Date: 2005/11/14 20:27:09 $
# $Author: dwelch $
#
# (c) Copyright 2003-2004 Hewlett-Packard Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#


# Std Lib
import sys, cStringIO, select, socket

# Local
from g import *
from codes import *

valid_encodings = ('', 'none', 'base64')
valid_char_encodings = ('', 'utf-8', 'latin-1')


def buildResultMessage(msg_type, payload=None, result_code=ERROR_SUCCESS, other_fields={}):
    other_fields.update({'result-code' : result_code})
    return buildMessage(msg_type, payload, other_fields)

def buildMessage(msg_type, payload=None, other_fields={}):

    if msg_type is None or not msg_type:
        raise Error(ERROR_INVALID_MSG_TYPE)

    msg = cStringIO.StringIO()
    msg.write("msg=%s\n" % msg_type.lower())

    if other_fields:
        for k in other_fields:
            msg.write('%s=%s\n' % (k, str(other_fields[k])))

    if payload is not None:
        msg.write("encoding=none\n")
        msg.write("length=%d\n" % len(str(payload)))
        msg.write("data:\n%s" % str(payload))

    return msg.getvalue()


def parseMessage(message):
    fields, data_found, data, remaining_msg = {}, False, '', ''
    msg_key_found, second_msg_key = False, False
    
    try:
        msg = cStringIO.StringIO(message)
    except TypeError:
        raise Error(ERROR_INVALID_MSG_TYPE)

    while True:
        pos = msg.tell()
        line = msg.readline().strip()

        if line == "":
            break

        if line.startswith('data:'):
            data = msg.read(fields['length']) or ''
            data_found = True
            continue

        if line.startswith('#'):
            continue

        try:
            key, value = line.split('=', 1)
            key = key.strip().lower()
        except ValueError:
            raise Error(ERROR_INVALID_MSG_TYPE)
        
        if key == 'msg':
            if msg_key_found:
                # already found, another message...
                second_msg_key = True
                break
            else:
                msg_key_found = True

        # If it looks like a number, convert it, otherwise leave it alone
        try:
            fields[key] = int(value)
        except ValueError:
            fields[key] = value
    
    if second_msg_key:
        msg.seek(pos)
        remaining_msg = msg.read() or ''

    return fields, data, remaining_msg


def sendEvent(sock, msg_type, payload=None, other_fields={}, 
              timeout=prop.read_timeout):
              
    m = buildMessage(msg_type, payload, other_fields)
    
    log.debug("Sending data on channel (%d)" % sock.fileno())
    log.debug(repr(m))

    r, w, e = select.select([], [sock], [], timeout)

    if w == []:
        raise Error(ERROR_INTERNAL)

    try:
        sock.send(m)
    except socket.error:
        log.exception()
        raise Error(ERROR_INTERNAL)


def xmitMessage(sock, msg_type, payload=None,
                 other_fields={},
                 timeout=prop.read_timeout):

    m = buildMessage(msg_type, payload, other_fields)

    log.debug("Sending data on channel (%d)" % sock.fileno())
    log.debug(repr(m))

    r, w, e = select.select([], [sock], [], timeout)

    if w == []:
        raise Error(ERROR_INTERNAL)

    try:
        sock.send(m)
    except socket.error:
        log.exception()
        raise Error(ERROR_INTERNAL)

    r, w, e = select.select([sock], [], [], timeout)

    if r == []:
        raise Error(ERROR_INTERNAL)

    m = sock.recv(prop.max_message_read)
    log.debug("Reading data on channel (%d)" % sock.fileno())
    log.debug(repr(m))
    fields, data, remaining = parseMessage(m)
    
    if remaining:
        log.warn("xmitMessage() remaining message != '' ('%s')" % remaining)
        
    try:
        result_code = fields['result-code']
    except KeyError:
        result_code = ERROR_INTERNAL
    else:
        del fields['result-code']
    
    try:
        result_msg_type = fields['msg']
    except KeyError:
        result_msg_type = ''
    else:
        del fields['msg']
        
    if result_msg_type.lower().strip() != ''.join([msg_type.lower(), 'result']):
        log.error("Unexpected message")

    return fields, data, result_code

