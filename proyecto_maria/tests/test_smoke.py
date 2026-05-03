import os
import json
import unittest

os.environ.setdefault('DATABASE_URL', 'postgresql://invalid')  # fuerza fallback si no hay PG

from fastapi.testclient import TestClient
from proyecto_maria.main import app


class APISmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_list_clients(self):
        r = self.client.get('/api/clientes')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('clientes', data)
        self.assertGreaterEqual(len(data['clientes']), 1)

    def test_02_favorite_toggle(self):
        cid = self.client.get('/api/clientes').json()['clientes'][0]['id']
        r = self.client.post(f'/api/clientes/{cid}/favorito', json={'favorito': True})
        self.assertEqual(r.status_code, 200)
        self.assertIn('mensaje', r.json())

    def test_03_demo_operations_and_history(self):
        cid = self.client.get('/api/clientes').json()['clientes'][0]['id']
        r = self.client.post(f'/api/clientes/{cid}/operaciones/demo')
        self.assertEqual(r.status_code, 200)
        hist = self.client.get(f'/api/clientes/{cid}/operaciones').json()['operaciones']
        self.assertGreaterEqual(len(hist), 1)

    def test_04_ncm_notes(self):
        r = self.client.post('/api/ncm/notas', json={'ncm': '8471', 'nota': 'Test note'})
        self.assertEqual(r.status_code, 200)
        notes = self.client.get('/api/ncm/notas/8471').json()['notas']
        self.assertGreaterEqual(len(notes), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)


