#!/bin/sh
set -e

# check if "SEARCH" or "DYNAMIC"
if [ "$1" = 'SEARCH' ]; then
    echo "SEARCH"
    python ./search.py -p -s /extensions/
elif [ "$1" = 'DYNAMIC' ]; then
    echo "DYNAMIC"
    python ./dynamic_standalone.py
fi
