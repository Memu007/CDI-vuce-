"""
Test SEO Implementation
Verifica que los elementos de SEO estén correctamente implementados:
- Meta tags (title, description, keywords)
- Open Graph tags
- Schema.org structured data
- robots.txt
- sitemap.xml
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import json
import re


@pytest_asyncio.fixture
async def client():
    """Cliente HTTP para tests."""
    from proyecto_maria.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ==================== LANDING PAGE SEO ====================

@pytest.mark.asyncio
async def test_landing_has_title(client):
    """Landing page debe tener título SEO-friendly."""
    response = await client.get("/")
    assert response.status_code == 200
    html = response.text
    
    # Verificar título
    title_match = re.search(r'<title>(.+?)</title>', html)
    assert title_match, "Falta el tag <title>"
    title = title_match.group(1)
    
    # Debe contener keywords importantes
    assert "CDI" in title, "Título debe contener 'CDI'"
    assert "Aduana" in title or "MARIA" in title, "Título debe mencionar 'Aduana' o 'MARIA'"


@pytest.mark.asyncio
async def test_landing_has_meta_description(client):
    """Landing page debe tener meta description."""
    response = await client.get("/")
    html = response.text
    
    # Buscar meta description
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)
    assert desc_match, "Falta meta description"
    description = desc_match.group(1)
    
    # Debe ser suficientemente descriptiva (50-160 chars ideal)
    assert len(description) >= 50, f"Description muy corta: {len(description)} chars"
    assert len(description) <= 300, f"Description muy larga: {len(description)} chars"
    
    # Debe contener keywords relevantes
    keywords_found = any(kw in description.lower() for kw in 
                       ["despachante", "avg", "ncm", "aduana", "maria", "afip"])
    assert keywords_found, "Description debe contener keywords del negocio"


@pytest.mark.asyncio
async def test_landing_has_meta_keywords(client):
    """Landing page debe tener meta keywords competitivas."""
    response = await client.get("/")
    html = response.text
    
    kw_match = re.search(r'<meta\s+name="keywords"\s+content="([^"]+)"', html)
    assert kw_match, "Falta meta keywords"
    keywords = kw_match.group(1).lower()
    
    # Debe incluir términos competitivos
    competitive_terms = ["software", "aduana", "argentina"]
    for term in competitive_terms:
        assert term in keywords, f"Keywords debe incluir '{term}'"


@pytest.mark.asyncio
async def test_landing_has_open_graph(client):
    """Landing page debe tener Open Graph tags para social sharing."""
    response = await client.get("/")
    html = response.text
    
    # OG tags requeridos
    og_tags = ["og:title", "og:description", "og:type"]
    for tag in og_tags:
        pattern = f'<meta\\s+property="{tag}"\\s+content="[^"]+"'
        assert re.search(pattern, html), f"Falta Open Graph tag: {tag}"


@pytest.mark.asyncio
async def test_landing_has_schema_org(client):
    """Landing page debe tener Schema.org structured data."""
    response = await client.get("/")
    html = response.text
    
    # Buscar JSON-LD
    jsonld_match = re.search(
        r'<script\s+type="application/ld\+json">\s*(\{.+?\})\s*</script>',
        html, 
        re.DOTALL
    )
    assert jsonld_match, "Falta Schema.org structured data (JSON-LD)"
    
    # Parsear y validar JSON
    try:
        schema = json.loads(jsonld_match.group(1))
        assert "@context" in schema, "Schema debe tener @context"
        assert "@type" in schema, "Schema debe tener @type"
    except json.JSONDecodeError:
        pytest.fail("Schema.org JSON-LD inválido")


@pytest.mark.asyncio
async def test_landing_has_canonical_url(client):
    """Landing page debe tener canonical URL."""
    response = await client.get("/")
    html = response.text
    
    canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
    assert canonical_match, "Falta canonical URL"


# ==================== DASHBOARD SEO (noindex) ====================

@pytest.mark.asyncio
async def test_dashboard_has_noindex(client):
    """Dashboard debe tener noindex (requiere login)."""
    response = await client.get("/dashboard")
    html = response.text
    
    # Debe tener robots noindex
    noindex_match = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', html)
    assert noindex_match, "Dashboard debe tener meta robots"
    robots_content = noindex_match.group(1).lower()
    assert "noindex" in robots_content, "Dashboard debe tener noindex"


# ==================== ROBOTS.TXT ====================

@pytest.mark.asyncio
async def test_robots_txt_exists(client):
    """robots.txt debe ser accesible."""
    response = await client.get("/static/robots.txt")
    assert response.status_code == 200, "robots.txt no accesible"
    
    content = response.text
    assert "User-agent:" in content, "robots.txt debe tener User-agent"
    assert "Allow:" in content or "Disallow:" in content, "robots.txt debe tener reglas"


@pytest.mark.asyncio
async def test_robots_txt_blocks_sensitive_paths(client):
    """robots.txt debe bloquear rutas sensibles."""
    response = await client.get("/static/robots.txt")
    content = response.text
    
    # Rutas que deben estar bloqueadas
    blocked_paths = ["/dashboard", "/api/", "/admin/"]
    for path in blocked_paths:
        assert f"Disallow: {path}" in content, f"robots.txt debe bloquear {path}"


@pytest.mark.asyncio
async def test_robots_txt_has_sitemap(client):
    """robots.txt debe referenciar sitemap."""
    response = await client.get("/static/robots.txt")
    content = response.text
    
    assert "Sitemap:" in content, "robots.txt debe referenciar sitemap"


# ==================== SITEMAP.XML ====================

@pytest.mark.asyncio
async def test_sitemap_xml_exists(client):
    """sitemap.xml debe ser accesible."""
    response = await client.get("/static/sitemap.xml")
    assert response.status_code == 200, "sitemap.xml no accesible"
    
    content = response.text
    assert '<?xml' in content, "sitemap.xml debe ser XML válido"
    assert '<urlset' in content, "sitemap.xml debe tener urlset"
    assert '<loc>' in content, "sitemap.xml debe tener URLs"


@pytest.mark.asyncio
async def test_sitemap_has_valid_urls(client):
    """sitemap.xml debe tener URLs válidas."""
    response = await client.get("/static/sitemap.xml")
    content = response.text
    
    # Verificar que tenga al menos una URL
    loc_match = re.search(r'<loc>(.+?)</loc>', content)
    assert loc_match, "sitemap.xml debe tener al menos una URL"
    
    url = loc_match.group(1)
    assert url.startswith("http"), f"URL en sitemap debe ser absoluta: {url}"


# ==================== SUMMARY TEST ====================

@pytest.mark.asyncio
async def test_seo_checklist_complete(client):
    """Verifica que todos los elementos de SEO estén presentes."""
    checklist = {
        "title": False,
        "meta_description": False,
        "meta_keywords": False,
        "og_tags": False,
        "schema_org": False,
        "canonical": False,
        "robots_txt": False,
        "sitemap_xml": False,
    }
    
    # Landing page
    resp = await client.get("/")
    html = resp.text
    
    checklist["title"] = bool(re.search(r'<title>.+</title>', html))
    checklist["meta_description"] = bool(re.search(r'name="description"', html))
    checklist["meta_keywords"] = bool(re.search(r'name="keywords"', html))
    checklist["og_tags"] = bool(re.search(r'property="og:', html))
    checklist["schema_org"] = bool(re.search(r'application/ld\+json', html))
    checklist["canonical"] = bool(re.search(r'rel="canonical"', html))
    
    # Static files
    checklist["robots_txt"] = (await client.get("/static/robots.txt")).status_code == 200
    checklist["sitemap_xml"] = (await client.get("/static/sitemap.xml")).status_code == 200
    
    # Reportar resultados
    failed = [k for k, v in checklist.items() if not v]
    assert not failed, f"SEO checklist incompleto: {failed}"
    
    print("\n✅ SEO Checklist completo:")
    for item, passed in checklist.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {item}")
