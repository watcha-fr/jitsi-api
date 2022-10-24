#!/usr/bin/env bash

# usage: ./del-user.sh <username> [<database>]

if [ -z "$1" ]; then
    echo "Username not provided"
    exit 1
else
    username=$1
fi

if [ -n "$2" ]; then
    path=$2
else
    path="conference-mapper.db"
fi

sqlite3 "$path" <<<"DELETE FROM user WHERE NAME = '$username'"
