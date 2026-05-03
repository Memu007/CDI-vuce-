import unittest
from fastapi.testclient import TestClient
from proyecto_maria.main import app

client = TestClient(app)

class TestAPIBase(unittest.TestCase):
    def test_root_html(self):
        r = client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('<!DOCTYPE html>', r.text)

    def test_clientes_endpoints(self):
        r = client.get('/api/clientes')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('clientes', data)
        self.assertGreaterEqual(len(data['clientes']), 1)
        cid = data['clientes'][0]['id']

        fav = client.post(f'/api/clientes/{cid}/favorito', json={'favorito': True}).json()
        self.assertIn('mensaje', fav)

        demo = client.post(f'/api/clientes/{cid}/operaciones/demo').json()
        self.assertIn('mensaje', demo)

        hist = client.get(f'/api/clientes/{cid}/operaciones').json()
        self.assertIn('operaciones', hist)
        self.assertGreaterEqual(len(hist['operaciones']), 1)

    def test_ncm_notes(self):
        add = client.post('/api/ncm/notas', json={'ncm': '8471', 'nota': 'Test note'}).json()
        self.assertEqual(add['mensaje'], 'Nota agregada')
        notes = client.get('/api/ncm/notas/8471').json()['notas']
        self.assertGreaterEqual(len(notes), 1)

if __name__ == '__main__':
    unittest.main()
