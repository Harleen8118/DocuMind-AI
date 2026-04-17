"""Pytest configuration and shared fixtures."""

import asyncio
import os
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.config import settings
from app.models.user import User
from app.models.document import Document, FileType, ProcessingStatus
from app.models.chat import ChatSession, Message, MessageRole
from app.utils.auth import hash_password, create_access_token

# Use SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_documind.db"

# Override settings for testing
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["UPLOAD_DIR"] = "./test_uploads"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    # Cleanup test DB file
    db_path = Path("./test_documind.db")
    if db_path.exists():
        db_path.unlink()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_app(test_engine):
    """Create test FastAPI application with overridden dependencies."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Import app after setting env vars
    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(test_app):
    """Create test HTTP client."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(test_session):
    """Create a test user and return (user, token)."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpassword123"),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    token = create_access_token(user.id)
    return user, token


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Create authorization headers for test user."""
    _, token = test_user
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_document(test_session, test_user):
    """Create a test document."""
    user, _ = test_user
    document = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        filename="test_file.pdf",
        original_filename="test_document.pdf",
        file_type=FileType.PDF,
        file_size=1024,
        mime_type="application/pdf",
        status=ProcessingStatus.READY,
        transcript_text="This is a test document about machine learning and AI.",
        page_count=3,
    )
    test_session.add(document)
    await test_session.commit()
    await test_session.refresh(document)
    return document


@pytest_asyncio.fixture
async def test_video_document(test_session, test_user):
    """Create a test video document with highlights."""
    user, _ = test_user
    import json
    highlights = [
        {"timestamp": 10.0, "timestamp_formatted": "00:10", "summary": "Introduction", "importance_score": 0.9},
        {"timestamp": 60.0, "timestamp_formatted": "01:00", "summary": "Main point", "importance_score": 0.95},
    ]
    document = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        filename="test_video.mp4",
        original_filename="test_video.mp4",
        file_type=FileType.VIDEO,
        file_size=10240,
        mime_type="video/mp4",
        status=ProcessingStatus.READY,
        transcript_text="This is a test video transcript about technology.",
        duration_seconds=120.0,
        highlights_json=json.dumps(highlights),
    )
    test_session.add(document)
    await test_session.commit()
    await test_session.refresh(document)
    return document


@pytest_asyncio.fixture
async def test_chat_session(test_session, test_user, test_document):
    """Create a test chat session."""
    user, _ = test_user
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=user.id,
        document_id=test_document.id,
        title="Test Chat",
    )
    test_session.add(session)
    await test_session.commit()
    await test_session.refresh(session)
    return session


@pytest.fixture
def upload_dir():
    """Create and cleanup test upload directory."""
    test_dir = Path("./test_uploads")
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
    # Cleanup
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.zremrangebyscore = AsyncMock()
    mock.zadd = AsyncMock()
    mock.zcard = AsyncMock(return_value=1)
    mock.expire = AsyncMock()
    mock.pipeline = MagicMock(return_value=mock)
    mock.execute = AsyncMock(return_value=[0, 0, 1, True])
    return mock
