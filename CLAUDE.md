# Platziflix — Monorepo

Plataforma de cursos online (cursos → clases/lecciones, profesores). Un backend REST y cuatro clientes.

```
PostgreSQL 15 ◄── Backend FastAPI (:8000) ◄── Frontend Next.js (SSR, localhost:8000)
                                          ◄── Android Kotlin/Compose (10.0.2.2:8000)
                                          ◄── iOS Swift/SwiftUI (localhost:8000)
```

- Fuente de verdad de contratos: `Backend/specs/00_contracts.md`. Todo cambio de API empieza ahí y se refleja en los 3 clientes.
- Sin autenticación, sin CORS (el Frontend hace fetch server-side).

## Backend — `Backend/`
- Capas: `app/main.py` (rutas + DI con `Depends`) → `app/services/course_service.py` (lógica, arma dicts de respuesta) → `app/models/` (ORM) → `app/db/base.py` (engine, `get_db`).
- `BaseModel` (`models/base.py`): `id`, `created_at`, `updated_at`, `deleted_at` (soft delete: filtrar siempre `deleted_at IS NULL`).
- Tablas: `courses`, `teachers`, `lessons`, `course_teachers` (N:M). Nuevos modelos deben importarse en `models/__init__.py` para que Alembic los detecte.
- Config: `app/core/config.py` (pydantic-settings, `DATABASE_URL`).
- Endpoints: `GET /`, `GET /health`, `GET /courses`, `GET /courses/{slug}`, `GET /courses/{slug}/classes/{class_id}` (una clase/lesson con `video_url`), ratings (`POST /courses/{course_id}/ratings`, `GET|DELETE /courses/{course_id}/ratings/user/{user_id}`).
- Ratings (`course_ratings`): un rating activo por usuario/curso vía índice único parcial `WHERE deleted_at IS NULL`; el CHECK 1–5 y ese índice no los detecta el autogenerate de Alembic (escribirlos a mano). Sin auth: el Frontend usa `DEMO_USER_ID` (`src/lib/demoUser.ts`).

Comandos (desde `Backend/`):
```
make start | stop | logs | build
make migrate                 # alembic upgrade head
make create-migration        # autogenerate
make seed | seed-fresh
make test                    # unit + integration (= docker compose exec api bash -c "cd /app && uv run pytest app -v")
```
Tests: `app/test_main.py` mockea los servicios y valida campos contra el contrato. `app/tests/` son de integración contra la base `platziflix_test` (mismo contenedor `db`; el fixture la crea y migra con Alembic, rollback por test; `TEST_DATABASE_URL` debe terminar en `_test` o aborta). Ojo: `app/alembic.ini` apunta fijo a `platziflix_db`.
- Cambiar `pyproject.toml`/`uv.lock` exige `docker compose build api` (no están montados en el contenedor).
- Host Windows: sin `make`, `uv` ni Node; `docker` en `C:\Program Files\Docker\Docker\resources\bin` (usar `docker compose ...` directo).

## Frontend — `Frontend/`
- Server Components con `fetch(..., { cache: "no-store" })` directo en cada `page.tsx` (URL `http://localhost:8000` hardcodeada, sin capa de API).
- Rutas: `/` (lista), `/course/[slug]` (detalle + loading/error/not-found), `/course/[slug]/classes/[class_id]` (VideoPlayer; incrusta YouTube con iframe, otros `video_url` con `<video>`).
- Componentes en `src/components/<Nombre>/<Nombre>.tsx` + `.module.scss` + test al lado. Tipos en `src/types/index.ts`. Alias `@/` → `src/`.
- `vars.scss` se inyecta globalmente vía `next.config.ts` (no importarlo manualmente).

Tests: en Docker/CI usar `yarn test --run` (sin `--run` queda en watch). Sin Node en el host: ver `Frontend/CLAUDE.md`.

## Mobile — `Mobile/`
Android (Kotlin/Compose, MVI) e iOS (SwiftUI, MVVM), ambas con Clean Architecture. Detalles en `Mobile/CLAUDE.md`.

## Convenciones
- JSON en snake_case; los clientes mapean a camelCase en DTOs (`teacher_id` → `teacherIds`/`teacherId`).
- Mantener la separación de capas en cada proyecto; no llamar a la red desde vistas en mobile.
- Código y comentarios en inglés; textos de UI y documentación en español.
- Planes de implementación en `spec/` (raíz) como `NN_nombre_del_spec.md`, numeración incremental desde `00`, con el formato del agente `architect` (`.claude/agents/architect.md`).

## Deuda conocida (verificar antes de asumir que sigue vigente)
1. `Backend/app/models/class.py` duplica `Lesson` y referencia `Course.classes` (inexistente); no se importa. No usarlo.
2. Base URLs hardcodeadas en los 3 clientes (iOS `localhost` solo sirve en simulador; Android `10.0.2.2` solo en emulador).
3. Credenciales de Postgres en claro en `docker-compose.yml`.
4. Ratings sin autenticación (cualquier cliente vota/borra como cualquier `user_id`). Hallazgos de seguridad y su estado en `spec/03_hallazgos_seguridad_ratings.md`.
