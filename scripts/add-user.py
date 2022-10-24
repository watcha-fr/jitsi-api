#!/usr/bin/env python3

# usage: ./add-user.sh <username> <password> [<database>]

from hashlib import blake2b
import sqlite3
import sys

username = sys.argv[1]
password = sys.argv[2]
path = sys.argv[3] if len(sys.argv) > 3 else "conference-mapper.db"

password_hash = blake2b(password.encode()).hexdigest()

connection = sqlite3.connect(path)
connection.execute(
    "INSERT INTO user (name, password_hash) VALUES (?,?)", (username, password_hash)
)
connection.commit()
connection.close()
