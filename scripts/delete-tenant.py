#!/usr/bin/env python3

# usage: delete-tenant.py [-h] [-d DATABASE] tenant_name

# positional arguments:
#   tenant_name           tenant name

# options:
#   -h, --help            show this help message and exit
#   -d DATABASE, --database DATABASE
#                         conference mapper database

import argparse
import binascii
import sqlite3


parser = argparse.ArgumentParser()
parser.add_argument("tenant_name", help="tenant name")
parser.add_argument(
    "-d",
    "--database",
    default="jitsi.db",
    help="conference mapper database",
)
args = parser.parse_args()

tenant_name = args.tenant_name
tenant_id = str(binascii.crc32(tenant_name.encode()))
database_path = args.database

connection = sqlite3.connect(database_path)

cursor = connection.execute("DELETE FROM tenant WHERE id == ?", (tenant_id,))
cursor = connection.execute(
    "DELETE FROM phone_number WHERE tenant_id == ?", (tenant_id,)
)

connection.commit()
connection.close()
