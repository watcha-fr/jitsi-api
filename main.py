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


class ApiStatus(Enum):
    FAIL = "No conference mapping was found"
    INVALID = "No conference or id provided"
    SUCCESS = "Successfully retrieved conference mapping"


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


@app.get("/conferenceMapper")
def conference_mapper(
    conference: Optional[str] = None,
    id: Optional[str] = None,
    credentials: str = Depends(get_credentials),
):
    conf_name = conference
    conf_id = id
    if conf_name:
        row = connection.execute(
            "SELECT conf_id FROM map WHERE conf_name = ?", (conf_name,)
        ).fetchone()
        conf_id = row[0] if row is not None else map(conf_name)
        return {
            "conference": conf_name,
            "id": conf_id,
            "message": ApiStatus.SUCCESS,
        }

    if conf_id:
        row = connection.execute(
            "SELECT conf_name FROM map WHERE conf_id = ?", (conf_id,)
        ).fetchone()
        if row is not None:
            return {
                "conference": row[0],
                "id": conf_id,
                "message": ApiStatus.SUCCESS,
            }
        else:
            return {
                "conference": False,
                "id": conf_id,
                "message": ApiStatus.FAIL,
            }

    return {
        "conference": False,
        "id": False,
        "message": ApiStatus.INVALID,
    }


def map(conf_name):
    """link and register the name of a conference with a random identifier"""

    clean()
    while True:
        conf_id = "".join(secrets.choice(string.digits) for i in range(10))
        try:
            connection.execute(
                "INSERT INTO map (conf_id, conf_name) VALUES (?,?)",
                (conf_id, conf_name),
            )
        except sqlite3.IntegrityError:
            continue
        break
    connection.commit()
    return conf_id


def clean():
    """deletes every 10 days, records older than 10 days"""

    global last_clean
    now = datetime.now()
    if last_clean is None or now - last_clean > timedelta(days=10):
        now_ts = int(now.timestamp())
        connection.execute(
            "DELETE FROM map WHERE ? - timestamp > 864000", (now_ts,)
        )  # 10d == 864000s
        last_clean = now


last_clean = None

connection = sqlite3.connect("conference-mapper.db", check_same_thread=False)

connection.execute(
    """CREATE TABLE IF NOT EXISTS map (
        conf_id TEXT UNIQUE NOT NULL,
        conf_name TEXT UNIQUE NOT NULL,
        timestamp DATETIME DEFAULT (strftime('%s','now')) NOT NULL,
        PRIMARY KEY (conf_id, conf_name)
    ) WITHOUT ROWID
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
