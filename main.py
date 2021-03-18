from datetime import datetime, timedelta
from enum import Enum
import secrets
import string
import sqlite3
from typing import Optional

from fastapi import FastAPI


app = FastAPI()


class status(Enum):
    FAIL = "No conference mapping was found"
    INVALID = "No conference or id provided"
    SUCCESS = "Successfully retrieved conference mapping"


@app.get("/conferenceMapper")
def conference_mapper(conference: Optional[str] = None, id: Optional[str] = None):
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
            "message": status.SUCCESS,
        }

    if conf_id:
        row = connection.execute(
            "SELECT conf_name FROM map WHERE conf_id = ?", (conf_id,)
        ).fetchone()
        if row is not None:
            return {
                "conference": row[0],
                "id": conf_id,
                "message": status.SUCCESS,
            }
        else:
            return {
                "conference": False,
                "id": conf_id,
                "message": status.FAIL,
            }

    return {
        "conference": False,
        "id": False,
        "message": status.INVALID,
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
    ) WITHOUT ROWID;
    """
)
