#!/bin/sh
echo "AvoAssure Webserver"
cd "$(dirname "$0")"
BASE=$(pwd)
npmpath="${BASE}/npm"
$npmpath start  --scripts-prepend-node-path
