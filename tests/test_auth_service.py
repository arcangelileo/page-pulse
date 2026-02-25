import pytest

from app.services.auth import AuthService


@pytest.mark.asyncio
async def test_password_hashing():
    password = "mysecretpassword"
    hashed = AuthService.hash_password(password)
    assert hashed != password
    assert AuthService.verify_password(password, hashed) is True
    assert AuthService.verify_password("wrongpassword", hashed) is False


@pytest.mark.asyncio
async def test_jwt_token_roundtrip():
    user_id = "test-user-id-123"
    token = AuthService.create_access_token(user_id)
    decoded_id = AuthService.decode_access_token(token)
    assert decoded_id == user_id


@pytest.mark.asyncio
async def test_jwt_invalid_token():
    result = AuthService.decode_access_token("not-a-valid-token")
    assert result is None


@pytest.mark.asyncio
async def test_create_and_get_user(db):
    user = await AuthService.create_user(db, name="Jane", email="jane@test.com", password="pass123")
    await db.commit()
    assert user.id is not None
    assert user.email == "jane@test.com"
    assert user.name == "Jane"
    assert user.password_hash != "pass123"

    fetched = await AuthService.get_user_by_email(db, "jane@test.com")
    assert fetched is not None
    assert fetched.id == user.id

    fetched_by_id = await AuthService.get_user_by_id(db, user.id)
    assert fetched_by_id is not None
    assert fetched_by_id.email == "jane@test.com"


@pytest.mark.asyncio
async def test_get_nonexistent_user(db):
    result = await AuthService.get_user_by_email(db, "nobody@test.com")
    assert result is None

    result = await AuthService.get_user_by_id(db, "nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_success(db):
    await AuthService.create_user(db, name="Jane", email="jane@test.com", password="securepass")
    await db.commit()

    user = await AuthService.authenticate_user(db, "jane@test.com", "securepass")
    assert user is not None
    assert user.email == "jane@test.com"


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db):
    await AuthService.create_user(db, name="Jane", email="jane@test.com", password="securepass")
    await db.commit()

    user = await AuthService.authenticate_user(db, "jane@test.com", "wrongpass")
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent(db):
    user = await AuthService.authenticate_user(db, "nobody@test.com", "anypass")
    assert user is None
