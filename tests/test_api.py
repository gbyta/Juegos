import os
import sys
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from models import Juego

if app.config.get('SQLALCHEMY_DATABASE_URI') != 'sqlite:///:memory:':
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    if hasattr(db, '_app_engines') and app in db._app_engines:
        for engine in db._app_engines[app].values():
            engine.dispose()
        db._app_engines.pop(app, None)
    app.extensions.pop('sqlalchemy', None)
    db.init_app(app)


class PruebasApiRest(unittest.TestCase):

    def setUp(self):
        self.contexto = app.app_context()
        self.contexto.push()
        db.create_all()

        self.cliente = app.test_client()

        base = Juego(
            nombre="Red Dead Redemption 2",
            descripcion="Aventura en el viejo oeste",
            precio=59.99
        )
        db.session.add(base)
        db.session.commit()
        self.id_base = base.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.contexto.pop()

    def test_obtener_catalogo_json(self):
        """Verifica que GET /api/juegos retorne la colección en formato JSON."""
        res = self.cliente.get('/api/juegos')
        self.assertEqual(res.status_code, 200)
        self.assertIn('application/json', res.content_type)

        cuerpo = json.loads(res.data)
        self.assertEqual(len(cuerpo), 1)
        self.assertEqual(cuerpo[0]['nombre'], "Red Dead Redemption 2")

    def test_registrar_videojuego_api_exitoso(self):
        """Verifica la creación vía POST /api/juegos con código 201 Created."""
        nuevo_juego = {
            "nombre": "The Legend of Zelda: Tears of the Kingdom",
            "descripcion": "Exploración y aventuras en Hyrule",
            "precio": 69.99
        }
        res = self.cliente.post(
            '/api/juegos',
            data=json.dumps(nuevo_juego),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 201)
        cuerpo = json.loads(res.data)
        self.assertEqual(cuerpo['nombre'], "The Legend of Zelda: Tears of the Kingdom")
        self.assertEqual(Juego.query.count(), 2)

    def test_rechazo_payload_invalido_api(self):
        """Verifica el error 400 Bad Request cuando faltan campos obligatorios."""
        incompleto = {"descripcion": "Falta el nombre y el precio"}
        res = self.cliente.post(
            '/api/juegos',
            data=json.dumps(incompleto),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)

    def test_consulta_detalle_y_recurso_no_encontrado(self):
        """Verifica GET /api/juegos/<id> válido (200) e inexistente (404)."""
        res_existente = self.cliente.get(f'/api/juegos/{self.id_base}')
        self.assertEqual(res_existente.status_code, 200)
        self.assertEqual(json.loads(res_existente.data)['id'], self.id_base)

        res_inexistente = self.cliente.get('/api/juegos/8888')
        self.assertEqual(res_inexistente.status_code, 404)

    def test_edicion_completa_videojuego_api(self):
        """Verifica la actualización mediante PUT /api/juegos/<id> (200 OK)."""
        actualizacion = {
            "nombre": "Red Dead Redemption 2: Ultimate Edition",
            "descripcion": "Incluye contenido adicional de historia",
            "precio": 79.99
        }
        res = self.cliente.put(
            f'/api/juegos/{self.id_base}',
            data=json.dumps(actualizacion),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['nombre'], "Red Dead Redemption 2: Ultimate Edition")

    def test_baja_videojuego_api(self):
        """Verifica la eliminación vía DELETE /api/juegos/<id> (204 No Content)."""
        res = self.cliente.delete(f'/api/juegos/{self.id_base}')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        self.assertIsNone(db.session.get(Juego, self.id_base))


if __name__ == '__main__':
    unittest.main()