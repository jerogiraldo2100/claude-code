# Hallazgos de seguridad: sistema de ratings y entorno local

> Referencias: [`spec/00_sistema_ratings_cursos.md`](00_sistema_ratings_cursos.md), [`spec/01_plan_backend_ratings.md`](01_plan_backend_ratings.md), [`spec/02_plan_frontend_ratings.md`](02_plan_frontend_ratings.md).
> Alcance: `Backend/` y `Frontend/` (Mobile fuera). Recoge lo observado durante la implementación de ratings, `/doctor` y el intento de `/security-review`.
> Estado verificado contra el código en la rama `mi-curso` (commit `fac28cd` más los cambios sin commit) y contra los contenedores `backend-api-1` / `backend-db-1` en ejecución (2026-09-30).

## 1. Resumen

El feature de ratings es una **demo sin autenticación**: el riesgo principal es por diseño (cualquiera vota como cualquier `user_id`), no un bug. Además hay dos errores 500 alcanzables o casi alcanzables y configuración de desarrollo con credenciales en claro. Los dos errores 500 (S2, S3) quedaron corregidos en la Fase S-A; el resto sigue pendiente.

| # | Hallazgo | Severidad (contexto demo local) | Estado |
|---|---|---|---|
| S1 | Sin autenticación: suplantación de `user_id` | Alta si se despliega / aceptada en demo | ⏳ aceptado por diseño (D1 del spec 00) |
| S2 | `user_id` fuera de rango int32 → 500 | Media | ✅ corregido (Fase S-A) |
| S3 | `IntegrityError` no-único en `upsert_rating` → 500 | Baja | ✅ corregido (Fase S-A) |
| S4 | Credenciales de Postgres en claro y puerto 5432 publicado | Media si sale del entorno local | ⏳ pendiente (deuda 4) |
| S5 | `alembic.ini` apunta fijo a `platziflix_db` | Baja (riesgo operativo) | ✅ mitigado en tests con guarda `_test` |
| S6 | Server Action `rateCourse` es un endpoint público | Baja | ✅ validación de servidor implementada |
| S7 | URLs `http://localhost:8000` hardcodeadas | Baja | ⏳ pendiente (deuda 3) |
| S8 | `/security-review` fallaba por falta de `origin/HEAD` | — (herramienta) | ✅ corregido |

## 2. Decisiones

### Confirmadas
1. **Sin auth en esta etapa** (D1 del spec 00): el Frontend envía `DEMO_USER_ID = 1`. Se acepta S1 mientras el proyecto sea local/didáctico.
2. **Sin CORS por diseño**: el navegador nunca llama a la API; todo `fetch` ocurre en el servidor de Next.js (Server Components y Server Action).

### Pendientes del usuario
- **DS1. ¿Cuándo se agrega autenticación?** Recomendación: **antes de cualquier despliegue fuera de localhost**. Trade-off: exige rediseñar el contrato (`user_id` dejaría de venir en el body y saldría del token), tocando Backend, Frontend y el spec 00.
- **DS2. ¿Se corrigen S2 y S3 ya?** ✅ Aceptada (2026-09-30). Recomendación: **sí, en una sola fase pequeña** (cambios mínimos, cubiertos por tests). Trade-off: ninguno relevante; solo altera la respuesta de casos inválidos (500 → 422/404).

## 3. Hallazgos

### S1: Sin autenticación, cualquier cliente vota como cualquier usuario ⏳
- **Evidencia**: `POST /courses/{course_id}/ratings` recibe `user_id` en el body (`app/schemas/rating.py`); `DELETE /courses/{course_id}/ratings/user/{user_id}` borra el voto de cualquier usuario. No hay middleware ni dependencia de auth en `app/main.py`.
- **Impacto**: manipulación de promedios (votos masivos con `user_id` distintos), borrado de votos ajenos. Sin rate limiting.
- **Mitigación hoy**: la API solo escucha en el host local; el frontend fija `DEMO_USER_ID`.

### S2: `user_id` mayor que int32 provoca 500 ✅ corregido
- **Evidencia (verificada 2026-09-30 en el contenedor `api`)**: `POST /courses/1/ratings` con `{"user_id": 3000000000, "rating": 4}` → **500**; log: `sqlalchemy.exc.DataError: (psycopg2.errors.NumericValueOutOfRange) integer out of range`.
- **Causa**: `RatingCreate.user_id` valida `gt=0` pero no tiene tope; la columna `course_ratings.user_id` es `Integer` (int4). El `DataError` no se captura.
- **Nota**: `GET /courses/3000000000/ratings/user/1` responde 404 (no 500), así que el `course_id` de la ruta no reproduce el problema en esa ruta. No se probaron todas las combinaciones.
- **Corrección propuesta**: `Field(gt=0, le=2_147_483_647, strict=True)` en el schema → 422; test unitario en `app/test_main.py`.

### S3: `IntegrityError` que no viene del índice único → `AttributeError` → 500 ✅ corregido
- **Evidencia**: `app/services/rating_service.py:48-55`. Tras el `rollback`, `_get_active_rating` devuelve `None` si el error fue de FK o CHECK, y `existing.rating = rating` lanza `AttributeError`.
- **Alcanzable hoy**: no desde la API (el endpoint valida existencia del curso y el rango 1–5 antes), salvo carrera con un borrado de curso. Documentado en `spec/01_plan_backend_ratings.md` (Fase 9).
- **Corrección propuesta**: si `existing is None` tras el rollback, relanzar el error original (`raise`).

### S4: Credenciales de Postgres en claro y puerto publicado ⏳
- **Evidencia**: `Backend/docker-compose.yml` líneas 7-9 y 23 (`platziflix_user` / `platziflix_password`), repetidas en `Backend/app/alembic.ini:87`; `ports: "5432:5432"` expone la base a la red del host.
- **Impacto**: aceptable en local; inaceptable si el compose se usa en un servidor o si el puerto queda accesible en la LAN.
- **Corrección propuesta**: mover a `.env` (no versionado) con `.env.example`; publicar `127.0.0.1:5432:5432` o quitar el puerto; que `alembic/env.py` lea `DATABASE_URL`.

### S5: `alembic.ini` hardcodeado a la base de desarrollo ✅ mitigado
- **Evidencia**: `app/alembic/env.py:49` usa `sqlalchemy.url` de `alembic.ini` e ignora `DATABASE_URL`.
- **Riesgo**: una herramienta o test que invoque Alembic sin sobrescribir la URL migraría (o degradaría) `platziflix_db`.
- **Mitigación**: `app/tests/conftest.py` sobrescribe `sqlalchemy.url` y aborta si la base no termina en `_test` (líneas 30-31). El arreglo de fondo va junto con S4.

### S6: La Server Action `rateCourse` es un endpoint público ✅
- **Evidencia**: `Frontend/src/app/course/[slug]/actions.ts`. Next.js expone toda Server Action como POST invocable por cualquiera, no solo desde `RatingInput`.
- **Mitigación implementada**: valida en servidor `Number.isInteger(rating)` y rango 1–5; el `user_id` no viaja desde el navegador (lo fija el servidor con `DEMO_USER_ID`), así que no se puede suplantar por esta vía. El Backend vuelve a validar (defensa en profundidad).
- **Residual**: `courseId` y `slug` no se validan en la acción; un `courseId` inválido lo rechaza el Backend (404/422) y `slug` solo se usa en `revalidatePath`.

### S7: URLs de la API hardcodeadas ⏳
- **Evidencia**: `http://localhost:8000` en `Frontend/src/app/page.tsx`, `course/[slug]/page.tsx`, `course/[slug]/actions.ts`, `classes/[class_id]/page.tsx`.
- **Impacto en seguridad**: HTTP sin TLS e imposibilidad de configurar la URL por entorno; obligó al sidecar `socat` (D5) en desarrollo.
- **Corrección propuesta**: variable de entorno de servidor (`API_URL`, sin prefijo `NEXT_PUBLIC_`).

### S8: `/security-review` no corría ✅ corregido
- **Causa**: el comando compara contra `origin/HEAD...`; al reapuntar `origin` al fork solo se publicó `mi-curso`, y `refs/remotes/origin/HEAD` no existía (`ambiguous argument 'origin/HEAD...': unknown revision`).
- **Corrección**: `git fetch origin` + `git remote set-head origin -a` → `origin/HEAD` = `origin/master`.
- **Advertencias**: la revisión solo cubre **cambios commiteados** (hoy 29 archivos contra el merge-base); los tests de integración, specs, agentes y fixes del Frontend sin commit quedan fuera. Además el `master` del fork ya trae la implementación oficial del curso (commits divergentes de `mi-curso`).

### Notas de `/doctor` (sin acción)
- Los settings se leyeron solo por claves (sin leer secretos). `permissions.defaultMode` del usuario es `"auto"`, sin hooks ni reglas allow/deny. El usuario decidió no cambiar nada.

## 4. Fases

### Fase S-A: Errores 500 por entrada inválida ✅ completada (DS2 aceptada 2026-09-30)
- **Archivos**: `Backend/app/schemas/rating.py`, `Backend/app/services/rating_service.py`, `Backend/app/test_main.py`, `Backend/app/tests/test_rating_service_integration.py`.
- **Tareas**: tope int32 en `user_id` (S2); relanzar el `IntegrityError` si no hay rating activo tras el rollback (S3); un test por caso.
- **Criterio de terminado**: `make test` en verde dentro del contenedor `api`; el POST con `user_id = 3000000000` responde 422.
- **Evidencia (2026-09-30)**:
  - S2: `RatingCreate.user_id` con `le=2_147_483_647`; test `test_out_of_range_user_id_returns_422` (0, 2147483648, 3000000000).
  - S3: `upsert_rating` hace `raise` si tras el rollback no hay rating activo; test de integración `test_upsert_non_duplicate_integrity_error_is_reraised` (FK inexistente → `IntegrityError`, sesión sigue usable).
  - `make test` (equivalente en el contenedor `api`): **47 passed**. Contra la API real: POST con `user_id = 3000000000` → **422** (antes 500); GET/DELETE `/courses/1/ratings/user/3000000000` → 404; `/health` 200.

### Fase S-B: Secretos y configuración ⏳
- **Archivos**: `Backend/docker-compose.yml`, `Backend/.env.example`, `Backend/app/alembic/env.py`, `Backend/app/alembic.ini`, `.gitignore`.
- **Tareas**: credenciales en `.env`; puerto 5432 ligado a `127.0.0.1`; Alembic lee `DATABASE_URL`.
- **Criterio de terminado**: `make stop && make start`, `/health` con `database: true`, `make migrate` y `make test` en verde; `git grep platziflix_password` sin resultados fuera de `.env.example`.

### Fase S-C: URL de API configurable ⏳
- **Archivos**: las 4 rutas del Frontend listadas en S7, `CLAUDE.md`.
- **Criterio de terminado**: `yarn lint`, `yarn test --run` y `yarn build` en Docker en verde; el sidecar `socat` deja de ser necesario.

### Fase S-D: Autenticación ⏳ (depende de DS1; fuera del alcance actual)
- Requiere un spec propio (`04_...`) con el arquitecto: cambia el contrato de ratings en el spec 00 y `Backend/specs/00_contracts.md`.

## 5. Fuera de alcance
- Mobile (Android/iOS).
- Rate limiting, auditoría de dependencias y cabeceras HTTP de seguridad: no se analizaron.
