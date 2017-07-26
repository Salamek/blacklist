#!/bin/bash

SCRIPTPATH=`pwd -P`

echo $SCRIPTPATH/run.py

export FLASK_APP=$SCRIPTPATH/run.py
