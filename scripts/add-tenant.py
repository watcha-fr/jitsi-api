#!/usr/bin/env python3

# usage: add-tenant.py [-h] [-d DATABASE] [-p PHONE] tenant_name

# positional arguments:
#   tenant_name           tenant name

# options:
#   -h, --help            show this help message and exit
#   -d DATABASE, --database DATABASE
#                         conference mapper database
#   -p PHONE, --phone PHONE
#                         SIP phone number

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
parser.add_argument(
    "-p",
    "--phone",
    help="SIP phone number",
)
args = parser.parse_args()

tenant_name = args.tenant_name
tenant_id = str(binascii.crc32(tenant_name.encode()))
database_path = args.database
phone_number = args.phone

connection = sqlite3.connect(database_path)

if not phone_number:
    watcha_tenant_id = str(binascii.crc32(b"watcha"))
    cursor = connection.execute(
        "SELECT number FROM phone_number WHERE tenant_id == ?", (watcha_tenant_id,)
    )
    (phone_number,) = cursor.fetchone()

connection.execute(
    "INSERT INTO tenant (id, name) VALUES (?,?)", (tenant_id, tenant_name)
)
connection.execute(
    "INSERT INTO phone_number (country, number, tenant_id) VALUES (?,?,?)",
    ("FR", phone_number, tenant_id),
)

connection.commit()
connection.close()
