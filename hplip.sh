#! /bin/bash
#
# Startup/shutdown script for HPLIP 
#
# Note, this script file must start before cupsd.
#
# For chkconfig the HPLIP priority (ie: 50) must be less the cupsd 
# priority (ie: 55).
#
# For LSB install_initd the cups script file should have "hplip" in the
# Should-Start field.
# 
#   chkconfig: 2345 50 10
#   description: Start/stop script for HP Linux Imaging and Printing (HPLIP).
#
# (c) 2004 Copyright Hewlett-Packard Development Company, LP
#
### BEGIN INIT INFO
# Provides: hplip
# Required-Start:
# Required-Stop:
# Should-Start:
# Should-Stop:
# Default-Start: 3 5
# Default-Stop: 
# Description: Start/stop script for HP Linux Imaging and Printing (HPLIP)
### END INIT INFO

if [ -f /etc/init.d/functions ] ; then
. /etc/init.d/functions
else

daemon() {
   $* >/dev/null 2>&1
   if [ $? -eq 0 ]; then
      echo -ne "                                           [  OK  ]\r"
   else
      echo -ne "                                           [FAILED]\r"
   fi
}

killproc() {
   pid=`su - root -c "pidof -s $1"`
   pidfile=/var/run/${1}.pid
   if [ -z $pid ]; then
      if [ -f $pidfile ]; then
         read pid < $pidfile
         kill $pid
      fi      
   else
      kill $pid
   fi
   retval=$?
   if [ -f $pidfile ]; then
      rm $pidfile
   fi      
   if [ $retval -eq 0 ]; then
      echo -ne "                                           [  OK  ]\r"
   else
      echo -ne "                                           [FAILED]\r"
   fi
}

fi 

mystatus() {
   pid=`su - root -c "pidof -s $1"`
   if [ -z $pid ]; then
      pidfile=/var/run/${1}.pid
      if [ -f $pidfile ]; then
         read pid < $pidfile
      fi      
   fi

   if [ -n "$pid" ]; then
      echo $"$1 (pid $pid) is running..."
      return 0
   fi

   echo $"$1 is stopped"
   return 3
}

RETVAL=0

HPIODDIR=
HPSSDDIR=

start() {
        echo -n $"Starting hpiod: "
        cd $HPIODDIR
        daemon ./hpiod
        RETVAL=$?
        echo
        [ $RETVAL = 0 ] && [ -d /var/lock/subsys ] && touch /var/lock/subsys/hpiod
        echo -n $"Starting hpssd: "
        cd $HPSSDDIR
        daemon ./hpssd.py
        RETVAL=$?
        echo
        [ $RETVAL = 0 ] && [ -d /var/lock/subsys ] && touch /var/lock/subsys/hpssd.py
#        killall -HUP cupsd
        return $RETVAL
}

stop() {
        echo -n $"Stopping hpiod: "
        killproc hpiod
        RETVAL=$?
        echo
        [ $RETVAL = 0 ] && rm -f /var/lock/subsys/hpiod
        echo -n $"Stopping hpssd: "
        killproc hpssd
        RETVAL=$?
        echo
        [ $RETVAL = 0 ] && rm -f /var/lock/subsys/hpssd.py
        for pidfile in /var/run/*; do
	   case "$( basename $pidfile )" in 
       		hpguid-*.pid)
                   read pid < $pidfile
                   kill $pid
                   rm $pidfile
	   esac
        done
        return $RETVAL
}       

restart() {
        stop
        start
}       

case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  restart)
        restart
        ;;
  status)
        mystatus hpiod
        mystatus hpssd
        ;;
  condrestart)
        [ -f /var/lock/subsys/hpiod ] && [ -f /var/lock/subsys/hpssd ] && restart || :
        ;;
  *)
        echo $"Usage: $0 {start|stop|status|restart|condrestart}"
        exit 1
esac

exit $?