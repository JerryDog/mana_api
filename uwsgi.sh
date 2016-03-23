#!/bin/bash

proj_name='mana_api'

if [ ! -n "$1" ]
then
    echo "Usages: sh uwsgi.sh [start|stop|restart]"
    exit 0
fi

if [ $1 = start ]
then
    psid=`ps aux | grep "flask_${proj_name}" | grep -v "grep" | wc -l`
    if [ $psid -eq 4 ]
    then
        echo "${proj_name} is running!"
        exit 0
    else
        /usr/bin/uwsgi -x flask_${proj_name}.xml
        nginx -s reload
        echo "Start ${proj_name} service [OK]"
    fi
    

elif [ $1 = stop ];then
    ps aux | grep "flask_${proj_name}" | grep -v "grep" |awk '{print $2}'|xargs kill -9
    echo "Stop ${proj_name} service [OK]"
elif [ $1 = restart ];then
    ps aux | grep "flask_${proj_name}" | grep -v "grep" |awk '{print $2}'|xargs kill -9
    /usr/bin/uwsgi -x flask_${proj_name}.xml
    nginx -s reload
    echo "Restart ${proj_name} service [OK]"

else
    echo "Usages: sh uwsgi.sh [start|stop|restart]"
fi