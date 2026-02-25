import pytest


# --- Registration Tests ---


@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Jane Smith", "email": "jane@example.com", "password": "securepass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["name"] == "Jane Smith"
    assert "id" in data["user"]
    assert "created_at" in data["user"]
    # Cookie should be set
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Jane", "email": "jane@example.com", "password": "securepass123"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Jane 2", "email": "jane@example.com", "password": "anotherpass123"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Jane", "email": "not-an-email", "password": "securepass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Jane", "email": "jane@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_empty_name(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "", "email": "jane@example.com", "password": "securepass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_fields(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "jane@example.com"},
    )
    assert response.status_code == 422


# --- Login Tests ---


@pytest.mark.asyncio
async def test_login_success(client):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Jane", "email": "jane@example.com", "password": "securepass123"},
    )
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "jane@example.com", "password": "securepass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "jane@example.com"
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Jane", "email": "jane@example.com", "password": "securepass123"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "jane@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "somepassword"},
    )
    assert response.status_code == 401


# --- Logout Tests ---


@pytest.mark.asyncio
async def test_logout(auth_client):
    response = await auth_client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


# --- Get Current User Tests ---


@pytest.mark.asyncio
async def test_get_me_authenticated(auth_client):
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    client.cookies.set("access_token", "invalid-token-here")
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


# --- UI Route Tests ---


@pytest.mark.asyncio
async def test_register_page(client):
    response = await client.get("/register", follow_redirects=False)
    assert response.status_code == 200
    assert "Create your account" in response.text


@pytest.mark.asyncio
async def test_login_page(client):
    response = await client.get("/login", follow_redirects=False)
    assert response.status_code == 200
    assert "Sign in to your account" in response.text


@pytest.mark.asyncio
async def test_register_page_redirects_when_authenticated(auth_client):
    response = await auth_client.get("/register", follow_redirects=False)
    assert response.status_code == 302
    assert "/dashboard" in response.headers["location"]


@pytest.mark.asyncio
async def test_login_page_redirects_when_authenticated(auth_client):
    response = await auth_client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert "/dashboard" in response.headers["location"]


# --- Dashboard Access Tests ---


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client):
    response = await client.get("/dashboard", follow_redirects=False)
    # Should return 401 since it's an API-guarded route
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_redirects_to_sites(auth_client):
    response = await auth_client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/sites" in response.headers["location"]


# --- Root Redirect Tests ---


@pytest.mark.asyncio
async def test_root_redirects_to_login(client):
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]


@pytest.mark.asyncio
async def test_root_redirects_to_dashboard_when_authenticated(auth_client):
    response = await auth_client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/dashboard" in response.headers["location"]
