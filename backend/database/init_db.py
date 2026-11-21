
from sqlalchemy import inspect, text

from database.connection import engine, Base
from database import models  # noqa: F401


# Columns added to tables that may already exist in older databases.
NEW_COLUMNS = {
    "students": {
        "age": "INTEGER",
        "interested_field": "VARCHAR",
        "learning_preferences": "VARCHAR",
        "user_id": "INTEGER",
    },
}



from sqlalchemy import inspect, text

from database.connection import engine, Base
from database import models  # noqa: F401


NEW_COLUMNS = {
    "students": {
        "age": "INTEGER",
        "interested_field": "VARCHAR",
        "learning_preferences": "VARCHAR",
        "user_id": "INTEGER",
    },
}


def init_database():
    """Create missing tables and add missing columns safely."""

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        inspector = inspect(connection)

        for table, columns in NEW_COLUMNS.items():
            if not inspector.has_table(table):
                continue

            existing = {
                column["name"]
                for column in inspector.get_columns(table)
            }

            for column, column_type in columns.items():
                if column not in existing:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table} "
                            f"ADD COLUMN {column} {column_type}"
                        )
                    )
                    print(f"Added column: {table}.{column}")

    print("Aspirixa AI database initialized successfully.")


if __name__ == "__main__":
    init_database()
