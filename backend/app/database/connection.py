import os

import mysql.connector


def get_db_connection():
    required_settings = (
        "MYSQL_HOST",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_DATABASE",
    )
    missing_settings = [
        setting for setting in required_settings if setting not in os.environ
    ]
    if missing_settings:
        raise RuntimeError(
            "Missing database environment settings: "
            + ", ".join(missing_settings)
        )

    return mysql.connector.connect(
        host=os.environ["MYSQL_HOST"],
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
    )
