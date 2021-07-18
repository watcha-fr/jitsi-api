# https://github.com/jitsi/jitsi-meet/blob/master/resources/cloud-api.swagger

from datetime import datetime, timedelta
from enum import Enum
from hashlib import blake2b
import secrets
import string
import sqlite3
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials


app = FastAPI()
security = HTTPBasic()


def get_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    row = connection.execute(
        "SELECT password_hash FROM user WHERE name = ?", (credentials.username,)
    ).fetchone()
    if row is None or row[0] != blake2b(credentials.password.encode()).hexdigest():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


@app.get("/tenants/{tenant}/phone-numbers")
def get_phone_numbers(tenant: str, conference: Optional[str] = None):
    sql = """
        SELECT
            country,
            number
        FROM
            phone_number
            JOIN tenant ON phone_number.tenant_id == tenant.id
        WHERE
            tenant.name == ?"""

    numbers = {}

    for country, number in connection.execute(sql, (tenant,)):
        numbers.setdefault(country, []).append(number)

    if not numbers:
        raise HTTPException(status_code=404)

    return {
        "message": "Phone numbers available.",
        "numbers": numbers,
        "numbersEnabled": True,
    }


@app.get("/conferences/{conference_id}")
def get_conference_name(conference_id: str):
    row = connection.execute(
        "SELECT tenant_id, name FROM conference WHERE id == ?", (conference_id,)
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404)

    tenant_id, conference = row

    return {
        "tenant_id": tenant_id,
        "conference": conference,
    }


# this crappy endpoint must remain upstream compliant (ie: get while binding if not found)
@app.get("/tenants/{tenant}/conferences")
def get_conference_id(tenant: str, conference: str):
    row = connection.execute(
        "SELECT id FROM tenant WHERE name = ?", (tenant,)
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404)

    tenant_id = row[0]

    row = connection.execute(
        "SELECT id FROM conference WHERE tenant_id == ? AND name == ?",
        (tenant_id, conference),
    ).fetchone()

    conference_id = (
        row[0] if row is not None else bind_conference(tenant_id, conference)
    )

    return {
        "id": conference_id,
        "conference": conference, # prevent "[features/invite] Error encountered while fetching dial-in numbers: undefined"
    }


def bind_conference(tenant_id, conference):
    """bind conference name with random identifier"""

    clean()

    while True:
        conference_id = "".join(secrets.choice(string.digits) for i in range(10))
        try:
            connection.execute(
                "INSERT INTO conference (tenant_id, id, name) VALUES (?,?,?)",
                (tenant_id, conference_id, conference),
            )
        except sqlite3.IntegrityError:
            continue
        break
    connection.commit()
    return conference_id


def clean():
    """deletes every 10 days, records older than 10 days"""

    global last_clean
    now = datetime.now()
    if last_clean is None or now - last_clean > timedelta(days=10):
        now_ts = int(now.timestamp())
        connection.execute(
            "DELETE FROM conference WHERE ? - timestamp > 864000", (now_ts,)
        )  # 10d == 864000s
        last_clean = now


last_clean = None

connection = sqlite3.connect("jitsi.db", check_same_thread=False)

connection.execute(
    """CREATE TABLE IF NOT EXISTS conference (
        tenant_id INTEGER,
        id TEXT UNIQUE,
        name TEXT,
        timestamp DATETIME DEFAULT (strftime('%s','now')) NOT NULL,
        PRIMARY KEY (tenant_id, id, name)
    ) WITHOUT ROWID
    """
)
connection.execute(
    """CREATE TABLE IF NOT EXISTS phone_number (
        country TEXT NOT NULL,
        number TEXT UNIQUE NOT NULL,
        tenant_id INTEGER NOT NULL
    )
    """
)
connection.execute(
    """CREATE TABLE IF NOT EXISTS tenant (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    )
    """
)
connection.execute(
    """CREATE TABLE IF NOT EXISTS user (
        name TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
)
