import os
import re
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from models import Juego, User

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


class PruebasRutasWeb(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['REMEMBER_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_DOMAIN'] = None
        app.config['SERVER_NAME'] = None
        app.config['SESSION_PROTECTION'] = None

        self.contexto = app.app_context()
        self.contexto.push()
        db.create_all()

        if hasattr(app, 'login_manager'):
            app.login_manager.session_protection = None

        self.cliente = app.test_client()

        datos_usuario = {
            "username": "gabriela_dev",
            "password": "GabyPassword2026"
        }
        if hasattr(User, "email"):
            datos_usuario["email"] = "gabriela@example.com"

        usuario = User(**datos_usuario)
        db.session.add(usuario)
        db.session.commit()
        self.id_usuario = str(usuario.get_id())

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.contexto.pop()

    def _autenticar_cliente(self):
        vista_login = self.cliente.get('/auth/login')
        html = vista_login.get_data(as_text=True)

        inputs = re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
        form_data = {}
        for campo in inputs:
            nombre_campo = campo.lower()
            if nombre_campo in ('csrf_token', 'submit'):
                continue
            elif 'mail' in nombre_campo or 'correo' in nombre_campo:
                form_data[campo] = 'gabriela@example.com'
            elif 'pass' in nombre_campo or 'contra' in nombre_campo or 'clave' in nombre_campo:
                form_data[campo] = 'GabyPassword2026'
            elif 'remember' in nombre_campo or 'recordar' in nombre_campo:
                continue
            else:
                form_data[campo] = 'gabriela_dev'

        if not form_data:
            form_data = {'username': 'gabriela_dev', 'password': 'GabyPassword2026'}

        self.cliente.post('/auth/login', data=form_data, follow_redirects=True)

        with self.cliente.session_transaction() as sesion:
            sesion['_user_id'] = self.id_usuario
            sesion['_fresh'] = True

    def test_vista_login_accesible(self):
        """Comprueba que la pantalla pública de acceso responda 200 OK."""
        res = self.cliente.get('/auth/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/html', res.content_type)

    def test_bloqueo_rutas_sin_autenticar(self):
        """Comprueba que las rutas protegidas redirijan (302) a usuarios anónimos."""
        for ruta in ('/juegos', '/agregar_juego'):
            res = self.cliente.get(ruta, follow_redirects=False)
            self.assertEqual(res.status_code, 302)
            self.assertIn('/auth/login', res.headers['Location'])

    def test_acceso_catalogo_con_usuario_autenticado(self):
        """Comprueba que un usuario autenticado visualice el listado de juegos."""
        juego = Juego(nombre="Portal 2", descripcion="Puzles en primera persona", precio=9.99)
        db.session.add(juego)
        db.session.commit()

        self._autenticar_cliente()
        res = self.cliente.get('/juegos')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Portal 2", res.get_data(as_text=True))

    def test_alta_videojuego_desde_formulario(self):
        """Comprueba el registro de un videojuego mediante POST /guardar_juego."""
        self._autenticar_cliente()
        res = self.cliente.post('/guardar_juego', data={
            'nombre': "Baldur's Gate 3",
            'descripcion': 'RPG táctico basado en D&D',
            'precio': '59.99'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        guardado = Juego.query.filter_by(nombre="Baldur's Gate 3").first()
        self.assertIsNotNone(guardado)

    def test_eliminacion_videojuego_desde_formulario(self):
        """Comprueba el borrado de un videojuego mediante POST /eliminar_juego."""
        juego = Juego(nombre="Juego Temporal", descripcion="Registro de prueba", precio=5.00)
        db.session.add(juego)
        db.session.commit()
        id_borrar = juego.id

        self._autenticar_cliente()
        res = self.cliente.post('/eliminar_juego', data={'id': id_borrar}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(db.session.get(Juego, id_borrar))

    def test_manejo_error_404_url_desconocida(self):
        """Comprueba la respuesta 404 ante rutas inexistentes."""
        res = self.cliente.get('/catalogo/seccion_no_disponible')
        self.assertEqual(res.status_code, 404)


if __name__ == '__main__':
    unittest.main()