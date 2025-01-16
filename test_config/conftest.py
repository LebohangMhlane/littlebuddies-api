import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

@pytest.fixture(autouse=True)
def destroy_database(db):
    """
    Drops all database tables after each test.
    """
    yield  # Let the test run first.
    with connection.cursor() as cursor:
        # Drop all tables in the database
        cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
        for table_name in connection.introspection.table_names():
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

    # Reapply migrations to reset the database state
    executor = MigrationExecutor(connection)
    executor.migrate()
    # executor.migrate(
    #     [
    #         ("contenttypes", "0002_remove_content_type_name"),
    #         ("auth", "0012_auto_20201219_1357"),
    #     ]
    # )  # Add required migrations here
