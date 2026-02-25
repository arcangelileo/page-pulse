import pytest

from app.services.site import SiteService


def test_normalize_domain_plain():
    assert SiteService.normalize_domain("example.com") == "example.com"


def test_normalize_domain_with_www():
    assert SiteService.normalize_domain("www.example.com") == "example.com"


def test_normalize_domain_with_https():
    assert SiteService.normalize_domain("https://www.example.com") == "example.com"


def test_normalize_domain_with_http_path():
    assert SiteService.normalize_domain("http://example.com/page?q=1") == "example.com"


def test_normalize_domain_uppercase():
    assert SiteService.normalize_domain("EXAMPLE.COM") == "example.com"


def test_normalize_domain_trailing_spaces():
    assert SiteService.normalize_domain("  example.com  ") == "example.com"


def test_generate_tracking_snippet():
    snippet = SiteService.generate_tracking_snippet("test-site-id")
    assert 'data-site="test-site-id"' in snippet
    assert "p.js" in snippet
    assert "<script" in snippet


@pytest.mark.asyncio
async def test_create_and_list_sites(db):
    from app.services.auth import AuthService
    user = await AuthService.create_user(db, "Test", "test@test.com", "pass1234")
    await db.commit()

    site = await SiteService.create_site(db, user.id, "Blog", "https://blog.example.com")
    await db.commit()
    assert site.domain == "blog.example.com"
    assert site.name == "Blog"

    sites = await SiteService.list_sites(db, user.id)
    assert len(sites) == 1
    assert sites[0].id == site.id


@pytest.mark.asyncio
async def test_update_site(db):
    from app.services.auth import AuthService
    user = await AuthService.create_user(db, "Test", "test@test.com", "pass1234")
    site = await SiteService.create_site(db, user.id, "Old", "old.com")
    await db.commit()

    updated = await SiteService.update_site(db, site, name="New", public=True)
    assert updated.name == "New"
    assert updated.public is True
    assert updated.domain == "old.com"


@pytest.mark.asyncio
async def test_delete_site(db):
    from app.services.auth import AuthService
    user = await AuthService.create_user(db, "Test", "test@test.com", "pass1234")
    site = await SiteService.create_site(db, user.id, "Delete Me", "del.com")
    await db.commit()
    site_id = site.id

    await SiteService.delete_site(db, site)
    await db.commit()

    found = await SiteService.get_site(db, site_id)
    assert found is None


@pytest.mark.asyncio
async def test_get_site_by_domain(db):
    from app.services.auth import AuthService
    user = await AuthService.create_user(db, "Test", "test@test.com", "pass1234")
    await SiteService.create_site(db, user.id, "Test", "mysite.com")
    await db.commit()

    found = await SiteService.get_site_by_domain(db, "https://www.mysite.com")
    assert found is not None
    assert found.domain == "mysite.com"

    not_found = await SiteService.get_site_by_domain(db, "other.com")
    assert not_found is None
