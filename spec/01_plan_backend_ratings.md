# Plan de implementación Backend: ratings de cursos (1 a 5 estrellas)

> Referencia principal: [`spec/00_sistema_ratings_cursos.md`](00_sistema_ratings_cursos.md) (análisis del arquitecto). Este documento baja a detalle **solo el Backend**; la numeración de fases sigue la del spec 00 para facilitar la trazabilidad.
> Alcance: `Backend/`. El Frontend lo planifica otro agente; aquí solo se listan las dependencias con él. Mobile queda fuera.
> Estado verificado contra el código en la rama `mi-curso`, commit `fac28cd`, y contra los contenedores `backend-api-1` / `backend-db-1` en ejecución (2026-09-30).

## 1. Resumen

El Backend del feature está implementado y funcionando (fases 1 a 4 ✅): contrato, tabla `course_ratings` con CHECK 1–5 e índice único parcial, `RatingService` con upsert/consulta/soft delete, estadísticas agregadas sin N+1 en `CourseService._get_rating_stats`, 3 rutas nuevas y 25 tests unitarios con mocks en verde. Quedan dos fases para cerrarlo:

- **Fase 8** ✅: `httpx` en las deps dev; los tests corren con el comando documentado, sin `--with`.
- **Fase 9** ✅: 18 tests de integración contra Postgres real (base `platziflix_test`) que cubren agregación y redondeo, upsert, soft delete, restricciones de BD, la rama de `IntegrityError` y la ausencia de N+1.

> Ejecución de las fases 8 y 9: 2026-09-30, rama `mi-curso` (sin commit). Decisiones D2 y D4 aceptadas por el usuario tal como se recomendaron.

### Hallazgo que corrige el supuesto de partida
El `Backend/Dockerfile` **sí instala las deps dev**: línea 15, `RUN uv sync --frozen --extra dev`. Verificado en el contenedor: `pytest 8.4.0` está instalado y `import httpx` falla con `ModuleNotFoundError`. Por lo tanto:
- Hoy basta con `--with httpx`; el `--with pytest` es redundante (la deuda 6 de `CLAUDE.md` es imprecisa en ese punto).
- La Fase 8 **no requiere tocar el Dockerfile**: solo `pyproject.toml`, `uv.lock` y reconstruir la imagen.
- Como `docker-compose.yml` solo monta `./app` y `./specs`, los cambios en `pyproject.toml`/`uv.lock` **no llegan al contenedor sin `docker compose build api`**. En cambio, los tests nuevos bajo `app/` sí se ven al instante (volumen montado).

## 2. Decisiones

### Confirmadas (heredadas del spec 00)
1. Sin auth: `user_id` entero; el Frontend envía `DEMO_USER_ID = 1`.
2. Un rating activo por usuario y curso; `POST` hace upsert (201 crea / 200 actualiza); `DELETE` hace soft delete (204).
3. Escrituras por `course_id`; lecturas agregadas (`average_rating` con 1 decimal o `null`, `total_ratings`) en `GET /courses` y `GET /courses/{slug}`.

### Resueltas por el usuario (antes pendientes)
- **D2. ¿Dónde corren los tests de integración?** ✅ Aceptada la recomendación. **Mantengo la recomendación del arquitecto**: base `platziflix_test` en el mismo contenedor `db`, creada si no existe y migrada con `alembic upgrade head`; nunca contra `platziflix_db`. El código la respalda:
  - `platziflix_user` es el `POSTGRES_USER` de la imagen oficial, así que es superusuario y puede ejecutar `CREATE DATABASE` sin cambiar `docker-compose.yml`.
  - Los tests corren dentro de `api`, que ya resuelve el host `db`; no hace falta un servicio nuevo ni puertos extra.
  - Usar Alembic (y no `Base.metadata.create_all`) valida la migración real `a3f9c2e1b7d4`, que es la única que tiene el CHECK y el índice parcial escritos a mano.
  - **Motivo de cautela encontrado en el código**: `app/alembic/env.py` toma la URL de `sqlalchemy.url` en `app/alembic.ini` (línea 87), que apunta **hardcodeada a `platziflix_db`** e ignora `DATABASE_URL`. Si el fixture invoca Alembic sin sobrescribir la URL, migraría la base de desarrollo. El plan lo resuelve sobrescribiendo `sqlalchemy.url` en el `Config` de Alembic desde el fixture (sin tocar `env.py`), más una guarda que aborta si el nombre de la base no termina en `_test`.
  - Trade-off: comparte instancia con la base de desarrollo (un `DROP` mal apuntado sería destructivo) a cambio de cero infraestructura nueva. La alternativa (servicio `db_test` en compose, o `tmpfs`) aísla mejor pero agrega configuración que hoy no se necesita.
- **D4. Redondeo del promedio** ✅ Aceptado: se mantiene `round(float(avg), 1)` y lo fija `test_rounding_tie_uses_round_half_to_even`. (nuevo, menor). `_get_rating_stats` usa `round(float(avg), 1)`: Python redondea al par (*banker's rounding*), así que 4.25 → `4.2`, no `4.3`. El contrato solo dice "1 decimal". Recomendación: **documentar el comportamiento con un test y no cambiarlo ahora**; si se prefiere "redondeo escolar", hacerlo en SQL (`ROUND(AVG(rating)::numeric, 1)`) en un cambio aparte. Trade-off: cambiarlo altera valores visibles en el Frontend en casos de empate exacto.

## 3. Fases

### Fase 1: Contrato ✅ completada
- **Evidencia**: `Backend/specs/00_contracts.md` en `fac28cd` define `CourseRating`, los campos `average_rating`/`total_ratings` y los 3 endpoints con sus códigos (201/200/204/404/422).
- **Dependencias con Frontend**: es el insumo del plan de Frontend. Cualquier cambio posterior de contrato (por ejemplo, D4) debe avisarse al agente de Frontend antes de implementarse.

### Fase 2: Datos ✅ completada
- **Evidencia**: `app/models/course_rating.py` (FK a `courses.id`, `SmallInteger`), importado en `app/models/__init__.py`; migración `a3f9c2e1b7d4` (`down_revision = d18a08253457`) con `ck_course_ratings_rating_range` e índice único parcial escritos a mano; `app/db/seed.py` deja un curso sin votos para probar `null`.
- **Riesgo vigente**: un autogenerate futuro puede proponer borrar el CHECK o el índice parcial.

### Fase 3: Lógica y API ✅ completada
- **Evidencia**: `app/schemas/rating.py` (int estricto), `app/services/rating_service.py` (`course_exists`, `upsert_rating` con captura de `IntegrityError` + `rollback`, `get_user_rating`, `delete_user_rating`), `app/services/course_service.py::_get_rating_stats` (una query `GROUP BY` que excluye `deleted_at`), 3 rutas en `app/main.py` con `Depends`. Verificado e2e con curl en la implementación.
- **Riesgo vigente**: la rama de reintento, el redondeo y las restricciones solo se probaron con mocks → Fase 9.

### Fase 4: Tests unitarios con mocks ✅ completada
- **Evidencia**: `app/test_main.py`, 25 casos (20 funciones, algunas parametrizadas) en verde con `uv run --with httpx --with pytest pytest app/test_main.py`.
- **Riesgo vigente**: dependen de `--with httpx` → Fase 8.

### Fase 8: `httpx` en las deps dev ✅ completada (8.1–8.5)
- **Evidencia**:
  - 8.1: `pyproject.toml` → `"httpx>=0.27"` en el extra `dev`.
  - 8.2: `docker compose run --rm --no-deps -v "C:/Users/jerog/claude-proyectos/claude-code/Backend:/app" api uv lock` (uv 0.12.21) → `Resolved 36 packages`, `Added certifi v2026.7.22, httpcore v1.0.9, httpx v0.28.1`. `anyio`, `h11`, `idna` y `sniffio` ya estaban en el lock (vía FastAPI/uvicorn), por eso no aparecen como nuevos. Formato del lock sin cambios (`version = 1`, `revision = 2`).
  - 8.3: `docker compose build api` + `docker compose up -d api` → `/health` responde `{"status":"ok",...,"database":true,"courses_count":3}` a los pocos segundos.
  - 8.4: `docker exec backend-api-1 python -c "import httpx; print(httpx.__version__)"` → `0.28.1`.
  - Criterio: `docker exec backend-api-1 bash -c "cd /app && uv run pytest app/test_main.py -v"` → `25 passed, 1 warning in 1.64s` (el warning es el `MovedIn20Warning` preexistente de `declarative_base`).
  - 8.5 ✅ (2026-09-30, sesión principal): `CLAUDE.md` sin la deuda de `httpx`; bloque de comandos con `make test` (= `docker compose exec api bash -c "cd /app && uv run pytest app -v"`), nota de rebuild tras cambiar `pyproject.toml`/`uv.lock` y nota del host Windows (sin `make`/`uv`/Node, ruta de `docker`).
- **Objetivo**: que `uv run pytest ...` funcione dentro de `api` sin flags `--with`, de forma reproducible desde la imagen.
- **Archivos**: `Backend/pyproject.toml` (`[project.optional-dependencies].dev`), `Backend/uv.lock`, `CLAUDE.md` (deuda 6 y bloque de comandos), opcionalmente `Backend/app/TESTING_README.md` (documenta `python -m pytest` sin mencionar el contenedor).
- **Tareas**:
  - **8.1** Agregar `httpx>=0.27` al extra `dev`, junto a `pytest>=7.0.0`.
  - **8.2** Regenerar `uv.lock`. No hay `uv` en el host: hacerlo en un contenedor con el directorio `Backend/` montado completo (por ejemplo `docker compose run --rm --no-deps -v "<ruta Backend>:/app" api uv lock`). Confirmar con `git diff uv.lock` que aparecen `httpx` y sus dependencias (`httpcore`, `anyio`, `h11`, `certifi`, `idna`, `sniffio`).
  - **8.3** Reconstruir y recrear el servicio: `docker compose build api` + `docker compose up -d api`. Obligatorio: `pyproject.toml` y `uv.lock` se copian en el build (no están montados) y el `uv sync --frozen` instala exactamente lo que dice el lock, así que un lock sin regenerar deja la imagen sin `httpx` en silencio.
  - **8.4** Verificar dentro del contenedor: `python -c "import httpx"` sin error.
  - **8.5** Actualizar `CLAUDE.md`: quitar la deuda 6 y dejar como comando de tests `docker compose exec api bash -c "cd /app && uv run pytest app/test_main.py -v"`. Anotar que en este host no hay `make` y que `docker` está en `C:\Program Files\Docker\Docker\resources\bin`.
- **Criterio de terminado**: `docker compose exec api bash -c "cd /app && uv run pytest app/test_main.py -v"` → 25 passed, sin `--with`.
- **Dependencias**: ninguna. Bloquea la Fase 9 (mismo runner). Sin dependencia con Frontend.
- **Riesgos / casos borde**:
  - El Dockerfile usa `ghcr.io/astral-sh/uv:latest`: un rebuild puede traer otra versión de `uv` (hoy 0.12.21). Si `uv sync --frozen` falla por formato de lock, regenerar el lock con la misma versión de la imagen.
  - `uv run` en el contenedor sincroniza sin extras; como la sincronización de `uv run` es inexacta, no desinstala `pytest`/`httpx`. Si algún día se usa `uv sync` a mano dentro del contenedor sin `--extra dev`, sí los quitaría.
  - Recrear `api` no afecta los datos (el volumen `postgres_data` es del servicio `db`).

### Fase 9: Tests de integración contra Postgres ✅ completada (9.1–9.6)
- **Evidencia**:
  - Archivos creados: `app/tests/__init__.py`, `conftest.py` (guarda `_test`, `CREATE DATABASE` con `AUTOCOMMIT`, `alembic upgrade head` con `sqlalchemy.url` sobrescrita, sesión con `join_transaction_mode="create_savepoint"` y rollback por test, helpers `make_course`/`make_teacher`/`add_ratings`), `test_rating_service_integration.py` (5), `test_course_stats_integration.py` (5), `test_constraints_integration.py` (5 casos: CHECK parametrizado con 0 y 6), `test_api_integration.py` (3).
  - `docker exec backend-api-1 bash -c "cd /app && uv run pytest app/tests -v"` → `18 passed in 2.22s`.
  - `uv run pytest app -q` → `43 passed` (25 unitarios + 18 de integración conviven en una corrida).
  - `psql -d platziflix_test -c "select version_num from alembic_version"` → `a3f9c2e1b7d4`; `courses` y `course_ratings` en `platziflix_test` quedan con 0 filas (el rollback por test funciona).
  - `platziflix_db`: `count(*)` de `course_ratings` = 8 antes y después; `alembic_version` sigue en `a3f9c2e1b7d4`.
  - Guarda verificada: con `TEST_DATABASE_URL=...platziflix_db` pytest aborta con `Refusing to run: database 'platziflix_db' does not end with '_test'` y no toca la base.
  - 9.2.4: la rama de `IntegrityError` funciona con el modo savepoint (el `rollback()` interno no rompe la transacción externa); la fila concurrente se inserta con SQL directo en la misma conexión.
  - 9.5.3: `GET /courses` ejecuta el mismo número de queries con 2 y con 6 cursos (con profesores y ratings) y exactamente 1 sobre `course_ratings`; el listado no carga profesores, así que no apareció N+1 ajeno.
  - La migración inicial `d18a08253457` corrió sin problemas sobre la base vacía.
  - El caso borde de `IntegrityError` no causado por el índice único (9.2, `AttributeError` → 500) queda documentado y sin corregir, según lo acordado.
  - 9.6 ✅ (2026-09-30, sesión principal): `CLAUDE.md` documenta la suite de integración (`app/tests/`, base `platziflix_test`, guarda `_test`, `alembic.ini` fijo a `platziflix_db`). En vez de `test-integration` se agregó `make test` (unit + integración). Criterio: el comando documentado copiado tal cual → `43 passed`.
- **Objetivo**: probar contra una BD real la agregación, el upsert, el soft delete, las restricciones y la ausencia de N+1, usando la migración real.
- **Archivos** (todos nuevos, bajo el volumen montado; no requieren rebuild):
  - `Backend/app/tests/__init__.py`
  - `Backend/app/tests/conftest.py`
  - `Backend/app/tests/test_rating_service_integration.py`
  - `Backend/app/tests/test_course_stats_integration.py`
  - `Backend/app/tests/test_constraints_integration.py`
  - `Backend/app/tests/test_api_integration.py`
  - `CLAUDE.md` (comando de la suite de integración)

#### 9.1 Infraestructura de la base de test (requiere D2)
- **Tareas**:
  1. URL de test: variable `TEST_DATABASE_URL` con valor por defecto derivado de `DATABASE_URL` cambiando el nombre de la base a `platziflix_test`.
  2. Guarda de seguridad: el fixture aborta (`pytest.exit`) si el nombre de la base no termina en `_test`.
  3. Fixture de sesión: conectarse a la base `postgres` con `AUTOCOMMIT` y crear `platziflix_test` si no existe (`CREATE DATABASE` no puede ir dentro de una transacción).
  4. Fixture de sesión: ejecutar `alembic upgrade head` de forma programática con `app/alembic.ini`, **sobrescribiendo `sqlalchemy.url`** con la URL de test (ver D2: `env.py` lee esa opción y el `.ini` apunta a `platziflix_db`).
  5. Fixture por test: conexión + transacción externa + `Session` enlazada con `join_transaction_mode="create_savepoint"` (SQLAlchemy 2), para que los `commit()` y `rollback()` que hace `RatingService` queden dentro de un savepoint y todo se revierta al final del test.
  6. Fixtures de datos mínimos por test (cursos activos y uno con `deleted_at`) en vez de reutilizar `seed.py`, para que cada test sea independiente.
- **Criterio de terminado**: `docker compose exec api bash -c "cd /app && uv run pytest app/tests -v"` corre (aunque sea con un test trivial) y, tras ejecutarlo, `docker compose exec db psql -U platziflix_user -d platziflix_test -c "select version_num from alembic_version"` devuelve `a3f9c2e1b7d4`. La base `platziflix_db` no cambia (mismo `count(*)` en `course_ratings` antes y después).
- **Riesgos**: el `rollback()` interno de la rama de `IntegrityError` puede romper la transacción externa si no se usa el modo savepoint; verificarlo con el caso 9.2.4. Si la migración inicial `d18a08253457` no es idempotente con una base vacía, aparece aquí (no verificado).

#### 9.2 `RatingService` contra la BD
- **Tareas** (un test por caso):
  1. Primer voto → `created=True`; segundo voto del mismo usuario con otro valor → `created=False`, valor actualizado y **una sola fila activa**.
  2. Votar → `delete_user_rating` → votar otra vez: crea fila nueva (`created=True`); la vieja queda con `deleted_at` no nulo. Prueba que el índice parcial permite el re-voto.
  3. `delete_user_rating` sin rating activo → `False`; `get_user_rating` tras borrar → `None`.
  4. Rama de reintento: insertar por fuera (otra sesión o SQL directo) una fila activa para el mismo `(course_id, user_id)` después de que `_get_active_rating` devolvió `None` (por ejemplo, parcheando `_get_active_rating` para que la primera llamada devuelva `None`). Esperado: `created=False`, una sola fila activa con el valor nuevo, y la sesión sigue usable.
  5. `course_exists`: `True` para curso activo, `False` para curso con soft delete y para id inexistente.
- **Criterio de terminado**: los 5 tests en verde.
- **Riesgos / casos borde**: en la rama de reintento, si el `IntegrityError` no se debe al índice único (por ejemplo, FK o CHECK con un valor que saltó la validación de Pydantic), `_get_active_rating` devuelve `None` y el código lanza `AttributeError` (500). Hoy no es alcanzable desde la API (Pydantic valida 1–5 y `course_exists` corre antes), pero conviene dejarlo documentado; no se corrige en este plan salvo que el usuario lo pida.

#### 9.3 Estadísticas agregadas (`CourseService`)
- **Tareas**:
  1. Votos 4, 5, 5 → `average_rating = 4.7`, `total_ratings = 3`.
  2. Curso sin votos → `null` y `0` tanto en `get_all_courses` como en `get_course_by_slug`.
  3. Ratings con soft delete no cuentan en promedio ni en total.
  4. Caso de empate de redondeo (4, 4, 4, 5 → 4.25): fija el comportamiento actual (`4.2`) y deja constancia de D4.
  5. Un curso con soft delete no aparece en `get_all_courses` aunque tenga ratings.
- **Criterio de terminado**: los 5 tests en verde.
- **Dependencias con Frontend**: si D4 cambia el redondeo, avisar al agente de Frontend (el spec 00 pide que el Frontend no vuelva a redondear).

#### 9.4 Restricciones de BD (validan la migración escrita a mano)
- **Tareas**:
  1. Insert directo con `rating = 0` y `rating = 6` → `IntegrityError` (CHECK `ck_course_ratings_rating_range`).
  2. Dos filas activas para el mismo `(course_id, user_id)` → `IntegrityError` (índice único parcial).
  3. Dos filas para el mismo par, una con `deleted_at` → se permite.
  4. `course_id` inexistente → `IntegrityError` (FK).
- **Criterio de terminado**: los 4 tests en verde. Si fallan, la migración y el modelo divergen.

#### 9.5 API de punta a punta sin mocks y control de N+1
- **Tareas**:
  1. `TestClient` con `app.dependency_overrides[get_db]` apuntando a la sesión de test. Flujo: `POST` → 201, `POST` otra vez → 200, `GET .../user/{id}` → 200, `DELETE` → 204, `GET` → 404, `POST` a curso con soft delete → 404.
  2. `GET /courses/{slug}` refleja `average_rating`/`total_ratings` tras los votos.
  3. N+1: con un listener `before_cursor_execute` sobre la conexión de test, contar queries de `GET /courses` con 2 cursos y con 6 cursos (con ratings y profesores); el número debe ser igual. Si las relaciones de profesores generan N+1 propio, el test lo revelará: registrarlo como deuda ajena a ratings y limitar la aserción a las queries sobre `course_ratings` (exactamente 1).
- **Criterio de terminado**: `docker compose exec api bash -c "cd /app && uv run pytest app/tests -v"` en verde **y** `uv run pytest app/test_main.py -v` sigue en 25/25. Ejecutar además `uv run pytest app -v` para confirmar que ambas suites conviven en una sola corrida.
- **Riesgos**: importar `app.main` crea el engine de `app/db/base.py` con `DATABASE_URL` (desarrollo); `create_engine` no conecta hasta el primer uso, pero **toda** ruta que toque BD debe pasar por el override de `get_db`. Un test que olvide el override escribiría en `platziflix_db`.

#### 9.6 Documentación
- **Tareas**: agregar a `CLAUDE.md` el comando de la suite de integración y la nota de que usa `platziflix_test`. Si se quiere, un target `test-integration` en el `Makefile` (útil fuera de Windows; en este host no hay `make`).
- **Criterio de terminado**: el comando documentado funciona copiado tal cual.

- **Dependencias de la Fase 9**: Fase 8 (`httpx` para `TestClient`) y decisión D2. Sin dependencia con Frontend, salvo el aviso si D4 cambia algo visible.

## 4. Riesgos y casos borde transversales
- **Borrar la base equivocada**: la base de test comparte instancia con `platziflix_db` y `alembic.ini` apunta a desarrollo. Mitigación: guarda `_test`, override de `sqlalchemy.url` y override de `get_db`; nunca usar `DROP DATABASE` en fixtures (se usa rollback por test).
- **Autogenerate de Alembic**: puede proponer eliminar el CHECK o el índice parcial. Los tests de 9.4 lo detectarían si una migración futura los quita.
- **Imagen desactualizada**: cambios en `pyproject.toml`/`uv.lock` requieren `docker compose build api`; olvidarlo da falsos "httpx no instalado".
- **Identidad falsa** (sin auth): cualquier cliente vota como cualquier `user_id`. Aceptable solo como demo.
- **Sin `make` en Windows**: todos los criterios de este plan usan `docker compose ...` directo.

## 5. Dependencias con el Frontend (lo planifica otro agente)
- El contrato de `Backend/specs/00_contracts.md` es la interfaz; este plan **no lo cambia**. Las fases 8 y 9 son internas del Backend.
- Solo requerirían coordinación: un cambio de redondeo (D4) o un eventual cambio de contrato derivado de los hallazgos de la Fase 9.
- La verificación manual en navegador (Fase 10 del spec 00) necesita el Backend levantado con `seed-fresh`; no depende de las fases 8 y 9.

## 6. Orden de ejecución
Estado: fases 1–4, 8 (8.1–8.5) y 9 (9.1–9.6) ✅.

Fases 1–4 ✅ → **Fase 8** (8.1 → 8.5) → decisión **D2** → **Fase 9** (9.1 → 9.2 ∥ 9.3 ∥ 9.4 → 9.5 → 9.6). D4 se puede decidir en cualquier momento antes de cerrar 9.3.
