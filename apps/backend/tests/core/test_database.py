from app.core.database import prepare_async_database_url


def test_prepare_async_database_url_normalizes_neon_connection_string():
    url, connect_args = prepare_async_database_url(
        "postgresql://user:secret@example.neon.tech/rag"
        "?sslmode=require&channel_binding=require"
    )

    assert url.drivername == "postgresql+asyncpg"
    assert "sslmode" not in url.query
    assert "channel_binding" not in url.query
    assert connect_args == {"ssl": "require"}


def test_prepare_async_database_url_preserves_local_async_url():
    url, connect_args = prepare_async_database_url(
        "postgresql+asyncpg://user:secret@localhost/rag"
    )

    assert url.drivername == "postgresql+asyncpg"
    assert connect_args == {}
