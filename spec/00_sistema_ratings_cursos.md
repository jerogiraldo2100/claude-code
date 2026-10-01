# Plan de implementación: ratings de cursos (1 a 5 estrellas)

> Alcance: solo Backend y Frontend. Mobile (Android/iOS) queda fuera por decisión del usuario.
> Estado verificado contra el código en la rama `mi-curso`, commit `fac28cd` (2026-09-30).

## 1. Resumen

Los usuarios califican un curso de 1 a 5 estrellas (un rating activo por usuario y curso, con upsert y retiro por soft delete), y los listados y el detalle muestran `average_rating` y `total_ratings`. El feature ya está implementado de punta a punta (fases 1 a 6, commit `fac28cd`). Faltan las fases 7 a 10 para dejarlo listo para producción: desbloquear `yarn build`, arreglar las deps de test del backend, agregar tests de integración contra Postgres y verificarlo a mano en el navegador.

## 2. Decisiones

### Confirmadas por el usuario
1. **Identidad**: no hay auth. `user_id` es un entero y el Frontend envía `DEMO_USER_ID = 1` (`Frontend/src/lib/demoUser.ts`). Trade-off: cualquier cliente puede votar como cualquier usuario. Es aceptable para una demo, pero no para producción con usuarios reales.
2. **Un rating activo por usuario y curso**, con upsert en `POST`. El `DELETE` hace soft delete.
3. **Escrituras por id** (`POST /courses/{course_id}/ratings`) y **lecturas agregadas** en `GET /courses` y `GET /courses/{slug}`: `average_rating` con 1 decimal (`null` sin votos) y `total_ratings`.

### Pendientes (le corresponden al usuario)
- **D1. ¿Exponer "retirar mi voto" en la UI?** El endpoint `DELETE` existe, pero ningún componente lo usa. Recomendación: no agregarlo ahora (el alcance lo marcó como opcional y la API ya lo soporta). Trade-off: el usuario demo no puede deshacer un voto desde el navegador.
- **D2. ¿Dónde corren los tests de integración?** Recomendación: una base `platziflix_test` en el mismo contenedor de Postgres del `docker-compose.yml`, creada por el fixture de pytest. Trade-off: es más simple que un servicio nuevo en compose, pero comparte instancia con la base de desarrollo, así que el fixture nunca debe apuntar a `platziflix_db`.
- **D3. ¿Arreglar `/classes/[class_id]` o excluirlo?** Bloquea `yarn build`, aunque es deuda ajena a ratings. Recomendación: el arreglo mínimo (params como Promise y quitar el import sin usar), sin implementar `GET /courses/:slug/classes/:id` ni migrar el tipo `Class`. Ese trabajo va aparte.

## 3. Fases

### Fase 1: Contrato ✅ completada
- **Objetivo**: definir la entidad, los endpoints, los campos nuevos y los errores en la fuente de verdad.
- **Archivos**: `Backend/specs/00_contracts.md`.
- **Tareas**: entidad `CourseRating`; `average_rating` y `total_ratings` en `GET /courses` y `GET /courses/{slug}`; `POST /courses/{course_id}/ratings` (201 al crear, 200 al actualizar), `GET|DELETE /courses/{course_id}/ratings/user/{user_id}`; 404 si el curso o el rating no existe; 422 si el valor está fuera de 1–5 o no es entero.
- **Criterio de terminado**: el contrato cubre los 3 endpoints y los 2 campos. Evidencia: diff de `fac28cd` (+55 líneas).
- **Dependencias**: ninguna. Bloquea todas las demás.
- **Riesgos**: los clientes mobile no se actualizan (están fuera de alcance), pero los campos nuevos son aditivos y no rompen sus DTOs si ignoran claves desconocidas. No se verificó en mobile.

### Fase 2: Datos ✅ completada
- **Objetivo**: persistir los ratings con integridad garantizada en la BD.
- **Archivos**: `Backend/app/models/course_rating.py`, `Backend/app/models/__init__.py`, `Backend/app/models/course.py`, `Backend/app/alembic/versions/a3f9c2e1b7d4_create_course_ratings_table.py`, `Backend/app/db/seed.py`.
- **Tareas**: el modelo hereda de `BaseModel`; CHECK `rating BETWEEN 1 AND 5`; índice único parcial `(course_id, user_id) WHERE deleted_at IS NULL`, escrito a mano en la migración; seed con ratings (course3 queda sin votos a propósito, para probar `null`).
- **Criterio de terminado**: `make migrate` y `make seed-fresh` corren sin errores. Evidencia: verificación e2e con curl contra Docker, reportada en la implementación.
- **Dependencias**: Fase 1.
- **Riesgos**: un `make create-migration` futuro podría proponer borrar el CHECK o el índice parcial. Hay que revisar a mano cada autogenerate.

### Fase 3: Lógica y API ✅ completada
- **Objetivo**: exponer el upsert, la consulta y el retiro, y agregar las estadísticas sin N+1.
- **Archivos**: `Backend/app/schemas/rating.py` (strict int), `Backend/app/services/rating_service.py`, `Backend/app/services/course_service.py` (`_get_rating_stats`), `Backend/app/main.py` (3 rutas con `Depends`).
- **Tareas**: upsert con captura de `IntegrityError` y `rollback` para la carrera de dos votos simultáneos; 404 para un curso con soft delete; `_get_rating_stats` resuelve todos los cursos en una sola query `GROUP BY` que excluye los ratings con `deleted_at`.
- **Criterio de terminado**: los endpoints responden según el contrato. Evidencia: curl e2e.
- **Dependencias**: Fase 2.
- **Riesgos**: la rama de reintento tras un `IntegrityError` y el redondeo del promedio solo se probaron con mocks. Los cubre la Fase 9.

### Fase 4: Tests del backend (unitarios con mocks) ✅ completada
- **Objetivo**: validar los campos exactos del contrato y los códigos HTTP.
- **Archivos**: `Backend/app/test_main.py`.
- **Tareas**: conjunto exacto de campos, 201/200 del upsert, 422 (fuera de rango, float, string), 404 para curso o rating inexistente, 204 del DELETE.
- **Criterio de terminado**: `uv run --with httpx --with pytest pytest app/test_main.py -v` da 25/25. Evidencia: reportado en la implementación.
- **Dependencias**: Fase 3.
- **Riesgos**: los tests solo corren con `--with httpx` (Fase 8).

### Fase 5: Frontend ✅ completada
- **Objetivo**: mostrar el promedio y permitir votar sin CORS.
- **Archivos**: `Frontend/src/types/index.ts`, `Frontend/src/lib/demoUser.ts`, `Frontend/src/components/StarRating/*`, `Frontend/src/components/RatingInput/*`, `Frontend/src/components/Course/*`, `Frontend/src/components/CourseDetail/*`, `Frontend/src/app/page.tsx`, `Frontend/src/app/course/[slug]/page.tsx` (params como Promise, trae el voto del usuario demo), `Frontend/src/app/course/[slug]/actions.ts` (Server Action `rateCourse` + `revalidatePath`).
- **Tareas**: tipos alineados al contrato (`name/description`); `StarRating` de solo lectura; `RatingInput` como client component con actualización optimista que restaura el voto anterior si falla; textos de UI en español.
- **Criterio de terminado**: las páginas renderizan los ratings y la Server Action persiste el voto. Evidencia: Server Action verificada e2e.
- **Dependencias**: Fase 1 (contrato). Se pudo hacer en paralelo con las fases 2 a 4 usando el contrato como mock.
- **Riesgos**: `rateCourse` solo revalida `/course/{slug}`. `/` usa `no-store`, así que no queda desactualizado. Clics en navegador real verificados en la Fase 10.

### Fase 6: Tests del frontend ✅ completada
- **Objetivo**: cubrir los componentes nuevos y los modificados.
- **Archivos**: `Frontend/src/components/StarRating/StarRating.test.tsx`, `Frontend/src/components/RatingInput/RatingInput.test.tsx`, `Frontend/src/components/Course/__test__/Course.test.tsx`.
- **Criterio de terminado**: `yarn test` pasa los 13 tests nuevos (ejecutados con `docker run node:20` porque no hay Node en el host).
- **Dependencias**: Fase 5.
- **Riesgos**: la suite completa no está verde por deuda previa (`VideoPlayer.test.tsx`, test de `/classes`). Se corrige en la Fase 7.

### Fase 7: Desbloquear `yarn build` ✅ completada (detalle en `spec/02_plan_frontend_ratings.md`, F4)
- **Evidencia (2026-09-30)**: en `docker run node:20`, `yarn lint` → exit 0 (solo 2 warnings `no-img-element`), `yarn test --run` → 5 archivos, 17/17, `yarn build` → exit 0 (`/`, `/course/[slug]` y `/classes/[class_id]` dinámicas). Cambios: `params` como Promise en `classes/[class_id]/page.tsx`, su test sin `startTransition` y con `await`, e imports de Vitest en `VideoPlayer.test.tsx`.
- **Objetivo**: que `yarn build`, `yarn lint` y `yarn test` pasen completos, para poder desplegar el Frontend.
- **Archivos**: `Frontend/src/app/classes/[class_id]/page.tsx`, `Frontend/src/app/classes/[class_id]/page.test.tsx`, `Frontend/src/components/VideoPlayer/VideoPlayer.test.tsx`.
- **Tareas**:
  1. En `page.tsx`, tipar `params: Promise<{ class_id: string }>` y hacer `const { class_id } = await params`. Hoy hace `params.class_id` en forma síncrona (línea 17).
  2. En `page.test.tsx`, quitar el import sin usar (`startTransition` en la línea 2) y pasar `params` como `Promise.resolve(...)`.
  3. Corregir los errores de tipos de `VideoPlayer.test.tsx` sin cambiar el tipo `Class` (D3).
- **Criterio de terminado**: `docker run --rm -v "$PWD/Frontend:/app" -w /app node:20 sh -c "yarn install --frozen-lockfile && yarn lint && yarn test --run && yarn build"` termina con exit 0.
- **Dependencias**: ninguna. Se puede hacer en paralelo con las fases 8 y 9.
- **Riesgos**: `/classes/{id}` sigue sin backend (deuda 2). El build pasa, pero la ruta falla en runtime. Queda fuera de alcance.

### Fase 8: `httpx` en las deps dev del Backend ✅ completada (detalle en `spec/01_plan_backend_ratings.md`)
- **Evidencia (2026-09-30)**: `httpx>=0.27` en el extra `dev`, `uv.lock` regenerado, imagen reconstruida. El Dockerfile ya instalaba el extra `dev` (el supuesto de este spec era incorrecto). `docker compose exec api bash -c "cd /app && uv run pytest app/test_main.py -v"` → 25 passed, sin `--with`. Deuda 6 eliminada de `CLAUDE.md` y nuevo `make test`.
- **Objetivo**: que los tests corran con el comando documentado, sin `--with`.
- **Archivos**: `Backend/pyproject.toml` (`[project.optional-dependencies].dev`), `Backend/uv.lock` si existe, y `CLAUDE.md` (quitar la deuda 6 una vez resuelta).
- **Tareas**: agregar `httpx>=0.27` junto a `pytest`; regenerar el lock con `uv lock`; confirmar que la imagen de Docker instala el extra `dev` (si no, ajustar el `uv sync` del Dockerfile o usar `uv run --extra dev`).
- **Criterio de terminado**: `docker-compose exec api bash -c "cd /app && uv run pytest app/test_main.py -v"` da 25/25.
- **Dependencias**: ninguna. Bloquea la Fase 9 (comparten el runner).
- **Riesgos**: no verifiqué si el Dockerfile instala los extras `dev`.

### Fase 9: Tests de integración del servicio contra Postgres ✅ completada (detalle en `spec/01_plan_backend_ratings.md`)
- **Evidencia (2026-09-30)**: 18 tests en `Backend/app/tests/` contra `platziflix_test` (creada y migrada con `alembic upgrade head`, guarda `_test`, rollback por test). `uv run pytest app -v` dentro de `api` → 43 passed (25 unit + 18 integración). `platziflix_db` intacta. D2 resuelta como se recomendó.
- **Objetivo**: probar contra una BD real lo que los mocks no cubren: agregación, upsert, soft delete y restricciones.
- **Archivos**: crear `Backend/app/tests/conftest.py` (engine hacia `platziflix_test`, `Base.metadata` o `alembic upgrade head`, transacción con rollback por test) y `Backend/app/tests/test_rating_integration.py`.
- **Tareas** (un test por caso):
  1. El primer voto crea (`created=True`); el segundo del mismo usuario actualiza (`created=False`) y sigue habiendo una sola fila activa.
  2. Votar, retirar el voto y volver a votar crea una fila nueva. La vieja queda con `deleted_at` y el índice parcial lo permite.
  3. `_get_rating_stats` con votos 4, 5 y 5 devuelve `4.7` y `3`. Un curso sin votos devuelve `null` y `0`. Los ratings borrados no cuentan.
  4. Un curso con soft delete: `course_exists` da `False` (404 en la API).
  5. Un insert directo con `rating=6` lanza `IntegrityError` por el CHECK. Un segundo insert activo duplicado lanza `IntegrityError` por el índice único.
  6. `GET /courses` con N cursos ejecuta un número de queries constante (contar con un event listener `before_cursor_execute`) para descartar el N+1.
- **Criterio de terminado**: `docker-compose exec api bash -c "cd /app && uv run pytest app/tests -v"` en verde, y la suite de la Fase 4 sigue en 25/25.
- **Dependencias**: Fase 8 y decisión D2.
- **Riesgos**: si `conftest.py` usa `create_all` en vez de Alembic, no crea el índice parcial ni valida la migración. Recomiendo `alembic upgrade head` sobre la base de test. La carrera real entre dos transacciones concurrentes es difícil de reproducir de forma determinista. Basta con cubrir la rama de `IntegrityError` forzando el duplicado (caso 5) y un test del reintento con una fila insertada entre la lectura y el insert.

### Fase 10: Verificación manual de punta a punta en el navegador ✅ completada (2026-10-01, 7/7 OK; evidencia en `spec/02_plan_frontend_ratings.md` F5.2 y `spec/capturas_f52/`)
- **Objetivo**: confirmar el flujo real de clics, que nunca se probó.
- **Archivos**: ninguno (solo verificación). Documentar el resultado en el PR.
- **Tareas**, con `make start`, `make seed-fresh` y `yarn dev` (o el build de la Fase 7 con `yarn start`):
  1. `/` muestra estrellas y conteo; el curso sin votos muestra el estado vacío en español.
  2. En `/course/{slug}`, al hacer clic en 4 estrellas el promedio y el conteo cambian tras la revalidación; al recargar se conserva el voto.
  3. Votar de nuevo con otro valor: el conteo no sube y el promedio cambia.
  4. Con la API apagada (`make stop`), votar muestra el error en español y restaura el voto anterior.
  5. Navegación con teclado y `aria-label` en las estrellas de `RatingInput`.
  6. La consola del navegador no muestra errores de hidratación.
- **Criterio de terminado**: los 6 puntos quedan registrados como OK (con capturas opcionales) en la descripción del PR.
- **Dependencias**: Fase 7 (para probar sobre el build de producción). Se puede adelantar con `yarn dev`.
- **Riesgos**: el Frontend debe correr en un contenedor Node con acceso a `localhost:8000` del host (`--network host` no funciona igual en Docker Desktop para Windows; puede hacer falta `host.docker.internal`, que choca con la URL hardcodeada, deuda 4).

## 4. Riesgos y casos borde transversales
- **Identidad falsa**: sin auth, cualquiera puede escribir como cualquier `user_id`. Es aceptable solo como demo.
- **Autogenerate de Alembic**: puede intentar eliminar el CHECK o el índice parcial. Revisar cada migración nueva.
- **Redondeo**: el promedio se redondea a 1 decimal en el servicio. El Frontend no debe volver a redondearlo de otra forma.
- **Soft delete en cascada**: si un curso se borra con soft delete, sus ratings quedan en la tabla; sus estadísticas no se exponen porque el curso no se lista. No hace falta borrarlos.
- **URL hardcodeada** `http://localhost:8000` en `page.tsx` y `actions.ts` (deuda 4). Limita el despliegue fuera de local, pero no se toca en este alcance.
- **Mobile desactualizado** respecto del contrato (fuera de alcance, cambios aditivos).

## 5. Fuera de alcance / siguientes pasos
- Autenticación real para reemplazar `DEMO_USER_ID`.
- UI para retirar el voto (D1).
- Ratings en Android e iOS.
- Reseñas o comentarios de texto junto al rating.
- Endpoint `GET /courses/:slug/classes/:id` y migración del tipo `Class`.
- Base URL configurable por entorno en los clientes.

## 6. Orden de ejecución sugerido
Fases 1–6 ✅ → Fase 7 ∥ Fase 8 → Fase 9 (requiere D2) → Fase 10 → PR de `mi-curso` a `main`.

## Anexo: ¿cómo funciona un LLM?
Este plan lo redactó un LLM (*Large Language Model*, modelo de lenguaje grande): el agente `architect` de Claude Code. Un LLM no "busca" respuestas ni ejecuta reglas escritas a mano; hace una sola cosa, repetida muchas veces: **predecir el siguiente fragmento de texto (token) más probable** a partir de todo el texto anterior.

**Ejemplo corto.** Ante la frase:

> El Curso de React tiene un promedio de 4.7 ___

el modelo calcula una probabilidad para cada token posible, aprendida de enormes cantidades de texto durante su entrenamiento:

| Siguiente token | Probabilidad (ilustrativa) |
|---|---|
| `estrellas` | 0.82 |
| `de` (→ "de 5") | 0.12 |
| `puntos` | 0.04 |
| `kilómetros` | 0.0001 |

Elige uno (normalmente de los más probables), lo agrega al texto y repite el proceso con la frase ya extendida: "…4.7 estrellas" → "…4.7 estrellas con" → "…4.7 estrellas con 3 calificaciones". Así, token a token, se construye cualquier respuesta, incluido este documento.

Por eso "kilómetros" casi nunca aparece: no porque exista una regla que lo prohíba, sino porque en el contexto de "promedio de 4.7" el modelo aprendió que es muy improbable. Esa misma mecánica explica sus límites: el modelo produce texto **plausible**, no necesariamente **verdadero**. Por eso el agente verifica contra el código real (archivos, tests, `git log`) antes de afirmar el estado de una fase.
