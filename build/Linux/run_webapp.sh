#!/bin/sh
echo "AvoAssure Webserver"
cd "$(dirname "$0")"
BASE=$(pwd)
npm start
