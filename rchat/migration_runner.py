from yoyo import get_backend, read_migrations

from rchat.conf import DATABASE_DSN, MIGRATIONS_PATH


def apply_migrations():
    migrations_backend = get_backend(DATABASE_DSN)
    migrations = read_migrations(MIGRATIONS_PATH)

    with migrations_backend.lock():
        migrations_backend.apply_migrations(
            migrations_backend.to_apply(migrations)
        )
