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
Python 3.11 · FastAPI · SQLAlchemy 2 · Alembic · uv · Docker Compose

- Capas: `app/main.py` (rutas + DI con `Depends`) → `app/services/course_service.py` (lógica, arma dicts de respuesta) → `app/models/` (ORM) → `app/db/base.py` (engine, `get_db`).
- `BaseModel` (`models/base.py`): `id`, `created_at`, `updated_at`, `deleted_at` (soft delete: filtrar siempre `deleted_at IS NULL`).
- Tablas: `courses`, `teachers`, `lessons`, `course_teachers` (N:M). Nuevos modelos deben importarse en `models/__init__.py` para que Alembic los detecte.
- Config: `app/core/config.py` (pydantic-settings, `DATABASE_URL`).
- Endpoints: `GET /`, `GET /health`, `GET /courses`, `GET /courses/{slug}`.

Comandos (desde `Backend/`):
```
make start | stop | logs | build
make migrate                 # alembic upgrade head
make create-migration        # autogenerate
make seed | seed-fresh
docker-compose exec api bash -c "cd /app && uv run pytest app/test_main.py -v"
```
Tests: `app/test_main.py` mockea `CourseService` y valida campos contra el contrato.

## Frontend — `Frontend/`
Next.js 15 (App Router, Turbopack) · React 19 · TypeScript · SCSS Modules · Vitest + Testing Library · yarn

- Server Components con `fetch(..., { cache: "no-store" })` directo en cada `page.tsx` (URL `http://localhost:8000` hardcodeada, sin capa de API).
- Rutas: `/` (lista), `/course/[slug]` (detalle + loading/error/not-found), `/classes/[class_id]` (VideoPlayer).
- Componentes en `src/components/<Nombre>/<Nombre>.tsx` + `.module.scss` + test al lado. Tipos en `src/types/index.ts`. Alias `@/` → `src/`.
- `vars.scss` se inyecta globalmente vía `next.config.ts` (no importarlo manualmente).

Comandos: `yarn dev` · `yarn build` · `yarn lint` · `yarn test`

## Mobile — `Mobile/`
Ambas apps usan Clean Architecture: `Data` (DTO → Mapper → Repository) / `Domain` (modelos + interfaz repo) / `Presentation` (ViewModel + UI). Guías en `.cursor/context/` de cada app.

**Android** `Mobile/PlatziFlixAndroid/` — Kotlin · Jetpack Compose · Material3 · Retrofit/OkHttp/Gson · Coil · Coroutines
- MVI: `StateFlow<UiState>` + `handleEvent(UiEvent)`.
- DI manual en `di/AppModule.kt` (`USE_MOCK_DATA` alterna `MockCourseRepository`/`RemoteCourseRepository`).
- Base URL en `data/network/NetworkModule.kt`. Build/test: `./gradlew assembleDebug`, `./gradlew test`.
- Feature actual: solo lista de cursos.

**iOS** `Mobile/PlatziFlixiOS/` — Swift · SwiftUI · async/await · URLSession
- MVVM: `@MainActor ObservableObject` + `@Published`; DI por inicializador.
- Red: `Services/NetworkManager` + protocolo `APIEndpoint`; endpoints en `Data/Repositories/CourseAPIEndpoints.swift`.
- Feature actual: lista + búsqueda local; navegación a detalle es TODO. Se abre con Xcode.

## Convenciones
- JSON en snake_case; los clientes mapean a camelCase en DTOs (`teacher_id` → `teacherIds`/`teacherId`).
- Mantener la separación de capas en cada proyecto; no llamar a la red desde vistas en mobile.
- Código y comentarios en inglés; textos de UI y documentación en español.

## Deuda conocida (verificar antes de asumir que sigue vigente)
1. Frontend desalineado con el contrato: espera `data.data` en `/courses` (backend devuelve lista plana) y campos `title/teacher/duration/video` en vez de `name/teacher_id/video_url`.
2. Frontend llama a `/classes/{id}`, que no existe; el contrato define `GET /courses/:slug/classes/:id`, aún no implementado.
3. `Backend/app/models/class.py` duplica `Lesson` y referencia `Course.classes` (inexistente); no se importa. No usarlo.
4. Base URLs hardcodeadas en los 3 clientes (iOS `localhost` solo sirve en simulador; Android `10.0.2.2` solo en emulador).
5. Credenciales de Postgres en claro en `docker-compose.yml`.
