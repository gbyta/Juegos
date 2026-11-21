import os
import sys
import unittest
from werkzeug.security import check_password_hash

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


class PruebasModelosORM(unittest.TestCase):

    def setUp(self):
        self.contexto = app.app_context()
        self.contexto.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.contexto.pop()

    def test_registro_nuevo_videojuego(self):
        """Comprueba que un juego se almacene y recupere con su ID asignado."""
        nuevo = Juego(nombre="Hollow Knight", descripcion="Metroidvania independiente", precio=14.99)
        db.session.add(nuevo)
        db.session.commit()

        consulta = Juego.query.filter_by(nombre="Hollow Knight").first()
        self.assertIsNotNone(consulta)
        self.assertIsNotNone(consulta.id)
        self.assertAlmostEqual(float(consulta.precio), 14.99)

    def test_modificacion_datos_videojuego(self):
        """Comprueba la edición de nombre y precio en un registro existente."""
        juego = Juego(nombre="Celeste", descripcion="Plataformas de precisión", precio=19.99)
        db.session.add(juego)
        db.session.commit()

        juego.nombre = "Celeste: Farewell Edition"
        juego.precio = 24.50
        db.session.commit()

        editado = db.session.get(Juego, juego.id)
        self.assertEqual(editado.nombre, "Celeste: Farewell Edition")
        self.assertAlmostEqual(float(editado.precio), 24.50)

    def test_borrado_videojuego_existente(self):
        """Comprueba que al eliminar un juego ya no exista en la tabla."""
        juego = Juego(nombre="Stardew Valley", descripcion="Simulación de granja", precio=14.99)
        db.session.add(juego)
        db.session.commit()

        db.session.delete(juego)
        db.session.commit()

        self.assertEqual(Juego.query.count(), 0)

    def test_insercion_multiple_catalogo(self):
        """Comprueba el guardado simultáneo de varios videojuegos."""
        catalogo = [
            Juego(nombre="Hades", descripcion="Roguelike mitológico", precio=24.99),
            Juego(nombre="Cuphead", descripcion="Acción estilo animación clásica", precio=19.99)
        ]
        db.session.add_all(catalogo)
        db.session.commit()

        self.assertEqual(Juego.query.count(), 2)

    def test_seguridad_y_cifrado_usuario(self):
        """Comprueba el hash de contraseña y el bloqueo de lectura directa."""
        clave_original = "GabySegura2026!"
        cuenta = User(username="gabriela_dev", password=clave_original)
        db.session.add(cuenta)
        db.session.commit()

        registrado = User.query.filter_by(username="gabriela_dev").first()
        self.assertIsNotNone(registrado)
        with self.assertRaises(AttributeError):
            _ = registrado.password
        self.assertTrue(check_password_hash(registrado.password_hash, clave_original))
        self.assertFalse(check_password_hash(registrado.password_hash, "ClaveIncorrecta"))


if __name__ == '__main__':
    unittest.main()