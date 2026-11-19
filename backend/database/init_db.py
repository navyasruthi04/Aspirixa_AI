from sqlalchemy import text

from database.connection import engine, Base
from database import models  # noqa: F401  (registers all tables)


# Columns added to tables that already exist in an older database file.
# create_all() creates NEW tables, but it never adds columns to old ones.
NEW_COLUMNS = {
    "students": {
        "age": "INTEGER",
        "interested_field": "VARCHAR",
        "learning_preferences": "VARCHAR",
        "user_id": "INTEGER",
    },
}


def init_database():
    """Creates missing tables and adds missing columns. Safe to run many times."""

    Base.metadata.create_all(bind=engine)

    with engine.connect() as connection:
        for table, columns in NEW_COLUMNS.items():
            existing = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table})"))
            }

            for column, column_type in columns.items():
                if column not in existing:
                    connection.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                    )
                    print(f"Added column: {table}.{column}")

        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_students_user_id ON students (user_id)")
        )
        connection.commit()


if __name__ == "__main__":
    init_database()
    print("Aspirixa AI database updated successfully!")
