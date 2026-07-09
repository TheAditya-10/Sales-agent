import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_engine):
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def parse_sse_events(raw_text: str) -> list[dict]:
    events = []
    for block in raw_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_line = next((line for line in block.splitlines() if line.startswith("event: ")), None)
        data_line = next((line for line in block.splitlines() if line.startswith("data: ")), None)
        if not event_line or not data_line:
            continue
        import json

        events.append(
            {
                "event": event_line[len("event: ") :],
                "data": json.loads(data_line[len("data: ") :]),
            }
        )
    return events
