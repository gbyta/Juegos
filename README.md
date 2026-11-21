![CI](https://github.com/gbyta/Juegos/actions/workflows/ci.yml/badge.svg)
[![Coverage](https://codecov.io/gh/gbyta/Juegos/branch/main/graph/badge.svg)](https://codecov.io/gh/gbyta/Juegos)
# Suite de Pruebas Unitarias — Aplicación Web de Videojuegos (Flask)

**Autora:** Gabriela Aguilar  
**Módulo:** Pruebas automatizadas con `unittest`

## Descripción General

Este proyecto incorpora una batería de 17 pruebas unitarias implementadas con la librería estándar `unittest` de Python para validar el comportamiento del ORM SQLAlchemy, el control de acceso mediante `Flask-Login` y las operaciones de la API RESTful.

## Cobertura de la Suite (`tests/`)

| Módulo de Prueba | Clase | Casos | Funcionalidades Verificadas |
| :--- | :--- | :---: | :--- |
| `tests/test_models.py` | `PruebasModelosORM` | 5 | Alta, edición, eliminación, inserción múltiple de registros en `Juego` y cifrado de contraseñas en `User`. |
| `tests/test_routes.py` | `PruebasRutasWeb` | 6 | Acceso público a `/auth/login`, redirección `302` sin sesión, consulta del catálogo autenticado, alta/baja vía formulario y error `404`. |
| `tests/test_api.py` | `PruebasApiRest` | 6 | Endpoints `GET`, `POST`, `PUT` y `DELETE` en `/api/juegos`, validación de cabeceras JSON y códigos `200`, `201`, `204`, `400` y `404`. |

## Instrucciones de Ejecución

Desde la carpeta raíz del proyecto, ejecutar:

```bash
python -m unittest discover -s tests -v