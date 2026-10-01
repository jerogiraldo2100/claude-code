# Plan de implementación Frontend: ratings de cursos (1 a 5 estrellas)

> Referencia principal: [`spec/00_sistema_ratings_cursos.md`](./00_sistema_ratings_cursos.md) (análisis del arquitecto). Este documento baja a detalle solo la parte de `Frontend/`.
> Alcance: solo Frontend. El Backend lo planifica otro agente en paralelo; mobile queda fuera.
> Estado verificado contra el código en la rama `mi-curso`, commit `fac28cd` (2026-09-30), corriendo `tsc`, `next lint` y `vitest` en `docker run node:20`.

## 1. Resumen

El Frontend ya muestra `average_rating`/`total_ratings` en `/` y `/course/[slug]`, y permite votar con `RatingInput` a través de la Server Action `rateCourse` (fases F1–F3 ✅, equivalentes a las fases 5 y 6 del spec 00). Falta dejarlo desplegable y probado de verdad:

- **F4 (= Fase 7 del spec 00)**: desbloquear `yarn lint`, `yarn test --run` y `yarn build`. Hoy fallan por deuda previa en `/classes/[class_id]` y `VideoPlayer.test.tsx`, ajena a ratings.
- **F5 (= Fase 10 del spec 00)**: verificación manual en el navegador del host, con el Frontend corriendo en Docker y sin cambiar la URL hardcodeada `http://localhost:8000`.

Estado medido hoy (evidencia de este plan):

| Comando (en `node:20`) | Resultado |
|---|---|
| `yarn test --run` | 16/17 tests pasan. Falla `classes/[class_id]/page.test.tsx` (runtime: *"A component suspended while responding to synchronous input"*). Los 13 tests de ratings pasan. |
| `npx tsc --noEmit` | 7 errores, todos en `VideoPlayer.test.tsx`: `describe`/`it`/`expect` sin tipos (TS2582/TS2304). |
| `yarn lint` | 1 error: `startTransition` sin usar en `classes/[class_id]/page.test.tsx:2`. 2 warnings `no-img-element` (no bloquean). |
| `yarn build` | No ejecutado en este análisis. Según el spec 00, además falla el chequeo de tipos de Next por `params` síncrono en `classes/[class_id]/page.tsx:7,17`. |

## 2. Decisiones

### Confirmadas (heredadas del spec 00)
1. Sin auth: el Frontend envía `DEMO_USER_ID = 1` (`src/lib/demoUser.ts`).
2. Toda escritura pasa por Server Action (el backend no tiene CORS). El navegador nunca llama a `:8000`.
3. El promedio llega redondeado a 1 decimal desde el backend; el Frontend no lo vuelve a redondear.

### Tomadas por el usuario (2026-09-30)
D1 = no, D3 = arreglo mínimo, D5 = opción A. Se conserva abajo el razonamiento original.

- **D1. ¿UI para "retirar mi voto"?** ✅ Aceptado: **no**. Recomendación original: **no por ahora** (se mantiene). El código lo confirma: `RatingInput.tsx` no tiene ninguna acción de borrado y `actions.ts` solo expone `rateCourse`. Agregarlo implicaría una segunda Server Action, un estado "sin voto" en el componente y más tests, fuera del alcance mínimo. Trade-off: el usuario demo no puede deshacer su voto desde el navegador (sí con `curl -X DELETE`).
- **D3. ¿Arreglo mínimo de `/classes/[class_id]` sin migrar el tipo `Class`?** ✅ Aceptado: **arreglo mínimo**. Recomendación: **sí, arreglo mínimo** (se mantiene). El código lo respalda: los errores de `VideoPlayer.test.tsx` no tienen relación con `Class` (son tipos de globals de Vitest), y los de `/classes` se resuelven con `params` como Promise más la forma de renderizar el componente async en el test. Migrar `Class` a `name/…` exigiría el endpoint `GET /courses/:slug/classes/:id`, que no existe (deuda 2). Trade-off: la ruta compila y sus tests pasan, pero en runtime sigue fallando (llama a `/classes/{id}`, inexistente) y su botón "Regresar al curso" apunta a `/course`, que tampoco existe.
- **D5 (antes "D4"; renumerada porque el plan de backend ya usa D4). ¿Cómo exponer el Frontend al navegador del host para F5?** ✅ Aceptado: **opción A**. Ver F5.1. Recomendación: **opción A (sidecar `socat` que publica el puerto 3000)**. No toca archivos del repo ni la URL hardcodeada. Trade-off: es un comando de Docker más que recordar y depende de `host.docker.internal` (disponible en Docker Desktop para Windows). La alternativa de **instalar Node en el host** (opción C) es la más simple de operar, pero requiere que el usuario instale software; es decisión suya.

## 3. Fases

### F1: Tipos, usuario demo y lectura de ratings ✅ completada
- **Objetivo**: alinear los tipos al contrato y mostrar el promedio en listado y detalle.
- **Archivos**: `Frontend/src/types/index.ts`, `Frontend/src/lib/demoUser.ts`, `Frontend/src/components/StarRating/StarRating.tsx` + `.module.scss`, `Frontend/src/components/Course/*`, `Frontend/src/components/CourseDetail/*`, `Frontend/src/app/page.tsx`, `Frontend/src/app/course/[slug]/page.tsx`.
- **Criterio de terminado**: listado y detalle renderizan estrellas y conteo; `params` del detalle ya es Promise. Evidencia: `fac28cd` (16 archivos del Frontend, +419/−59).
- **Dependencias**: contrato (`Backend/specs/00_contracts.md`, fase 1 del spec 00) ✅.

### F2: Votar con Server Action ✅ completada
- **Objetivo**: permitir votar sin CORS, con actualización optimista.
- **Archivos**: `Frontend/src/components/RatingInput/*`, `Frontend/src/app/course/[slug]/actions.ts`.
- **Criterio de terminado**: `rateCourse` valida 1–5, hace `POST /courses/{id}/ratings` con `DEMO_USER_ID`, devuelve errores en español y revalida `/course/{slug}`; `RatingInput` usa botones con `aria-label`/`aria-pressed` y `role="status"`/`role="alert"`. Evidencia: `fac28cd`; Server Action verificada e2e según el spec 00.
- **Dependencias**: endpoint `POST /courses/{course_id}/ratings` del Backend ✅.

### F3: Tests de ratings ✅ completada
- **Archivos**: `StarRating.test.tsx` (4), `RatingInput.test.tsx` (4), `Course/__test__/Course.test.tsx` (5).
- **Criterio de terminado**: los 13 pasan. Evidencia: `yarn test --run` de hoy, 4 archivos verdes.

### F4: Desbloquear lint, tests y build ✅ completada (= Fase 7 del spec 00)
- **Evidencia (2026-09-30, sin commit)**: en `docker run node:20` con los volúmenes de F4.4, `yarn install --frozen-lockfile && npx tsc --noEmit --incremental false && yarn lint && yarn test --run && yarn build` terminó con **exit 0**:
  - `tsc`: 0 errores. `yarn lint`: 0 errores, solo los 2 warnings `no-img-element` conocidos.
  - `yarn test --run`: **5 archivos, 17/17 tests** (VideoPlayer 3, classes page 1, StarRating 4, Course 5, RatingInput 4).
  - `next build`: compila y chequea tipos; `/`, `/course/[slug]` y `/classes/[class_id]` salen como dinámicas (ƒ), `/_not-found` estática. El build no necesitó backend.
  - Archivos: `VideoPlayer.test.tsx` (import explícito de `vitest`), `classes/[class_id]/page.tsx` (`params` Promise + `await`), `classes/[class_id]/page.test.tsx` (sin `startTransition`; `await ClassPage({ params: Promise.resolve(...) })` y luego `renderToString`). Sin cambios en código de ratings.
- **Objetivo**: que `yarn lint`, `yarn test --run` y `yarn build` terminen con exit 0, sin tocar código de ratings.
- **Dependencias**: ninguna con el Backend (el build no llama a la API porque las páginas usan `no-store` y son dinámicas; ver riesgos). Se puede hacer en paralelo con las fases 8 y 9 del Backend. Requiere D3.

#### F4.1: `VideoPlayer.test.tsx` sin errores de tipos
- **Archivos**: `Frontend/src/components/VideoPlayer/VideoPlayer.test.tsx`.
- **Tareas**:
  1. Importar `describe`, `it`, `expect` desde `vitest` de forma explícita, igual que los tests nuevos (`StarRating.test.tsx:1`), y quitar el comentario "Si usas Vitest, descomenta…".
  2. No tocar `tsconfig.json` (agregar `"types": ["vitest/globals"]` también funcionaría, pero afecta a todo el proyecto; el import explícito es el cambio mínimo y coherente con el resto).
- **Criterio de terminado**: `npx tsc --noEmit --incremental false` sin errores en ese archivo; sus 3 tests siguen verdes.
- **Riesgos**: `toBeInTheDocument` hoy tipa bien gracias a `src/test/setup.ts` (importa `@testing-library/jest-dom`); si `tsc` lo marca tras el cambio, revisar ese setup antes de tocar tipos.

#### F4.2: `/classes/[class_id]/page.tsx` con `params` como Promise
- **Archivos**: `Frontend/src/app/classes/[class_id]/page.tsx`.
- **Tareas**:
  1. Tipar `params` como `Promise<{ class_id: string }>` (línea 7).
  2. Resolverlo con `await` antes de `getClassData` (línea 17), igual que `course/[slug]/page.tsx`.
  3. No cambiar el tipo `Class`, la URL `/classes/{id}` ni el `Link` a `/course` (D3).
- **Criterio de terminado**: `yarn build` ya no reporta el error de tipos de `PageProps` en esta ruta.

#### F4.3: `/classes/[class_id]/page.test.tsx` en verde
- **Archivos**: `Frontend/src/app/classes/[class_id]/page.test.tsx`.
- **Tareas**:
  1. Quitar el import `startTransition` sin usar (línea 2): resuelve el error de lint.
  2. Pasar `params` como `Promise.resolve({ class_id: "19" })`.
  3. Corregir el fallo en runtime (verificado hoy): `renderToString(<ClassPage …/>)` con un componente async hace que React suspenda. Hay que invocar primero el Server Component como función asíncrona (await) y renderizar el elemento que devuelve.
  4. Mantener las 4 aserciones actuales.
- **Criterio de terminado**: `yarn test --run` da 17/17 y `yarn lint` sin errores.
- **Riesgos**: el `global.fetch` mockeado a nivel de módulo no se restaura; hoy no afecta a otros archivos (Vitest aísla por archivo), no hace falta tocarlo.

#### F4.4: Verificación completa
- **Tareas**: correr en un solo contenedor, desde el host (Git Bash con `MSYS_NO_PATHCONV=1`, o PowerShell):
  `docker run --rm -v "<ruta>\Frontend:/app" -v platziflix_frontend_node_modules:/app/node_modules -v platziflix_frontend_next:/app/.next -w /app node:20 sh -c "yarn install --frozen-lockfile && yarn lint && yarn test --run && yarn build"`
- **Criterio de terminado**: exit 0; la salida de `next build` lista `/`, `/course/[slug]` y `/classes/[class_id]` como rutas dinámicas (ƒ).
- **Riesgos**:
  - `yarn test` sin `--run` entra en modo watch; en CI/Docker siempre usar `--run`.
  - Si `next build` intenta prerenderizar `/` y llamar a `localhost:8000`, fallaría sin backend alcanzable. No debería (usa `no-store`), pero no está verificado: si pasa, correr el build con `--network container:backend-api-1`.
  - Los warnings `no-img-element` no bloquean; no se corrigen aquí.

### F5: Verificación manual en el navegador ⏳ en curso: F5.1 ✅, F5.2 ⏳ (usuario) (= Fase 10 del spec 00)
- **Objetivo**: probar los clics reales del flujo de ratings desde el navegador del host.
- **Dependencias**: Backend levantado con datos (`make start`, `make migrate`, `make seed-fresh`; hoy `backend-api-1` publica `8000` y `backend-db-1` publica `5432`). F4 para probar sobre el build de producción; se puede adelantar con `yarn dev`. Decisión D5.

#### F5.1: Exponer el Frontend al host sin tocar la URL hardcodeada ✅ completada (opción A, `yarn dev`)
- **Comandos usados** (Git Bash con `MSYS_NO_PATHCONV=1`; en PowerShell son iguales sin esa variable):
  ```
  docker run -d --name platziflix-fe-net -p 3000:3000 alpine/socat tcp-listen:8000,fork,reuseaddr,bind=127.0.0.1 tcp-connect:host.docker.internal:8000
  docker run -d --name platziflix-fe-dev --network container:platziflix-fe-net -v "C:\Users\jerog\claude-proyectos\claude-code\Frontend:/app" -v platziflix_frontend_node_modules:/app/node_modules -v platziflix_frontend_next:/app/.next -w /app node:20 yarn dev -H 0.0.0.0
  ```
  Detener: `docker rm -f platziflix-fe-dev platziflix-fe-net`. Logs: `docker logs -f platziflix-fe-dev`.
- **Evidencia (2026-09-30)**, con `curl` desde el host:
  - `GET http://localhost:3000/` → 200; muestra `aria-label="4.7 de 5 estrellas"` (React), `"3.5 de 5 estrellas"` (Python) y "Sin calificaciones" (JavaScript).
  - `GET http://localhost:3000/course/curso-de-react` → 200; promedio 4.7, los 5 botones "Calificar con N estrella(s)" y `aria-pressed="true"` en el voto 5 del usuario demo.
  - Server Action: `POST http://localhost:3000/course/curso-de-javascript` con `Next-Action: <id de rateCourse>` y cuerpo `[3,"curso-de-javascript",4]` → 200; la API pasó a tener el rating (id 9, user 1, 4★) y el curso `4.0 / 1`. Se limpió con `DELETE /courses/3/ratings/user/1` → 204; estado final igual al seed (React 4.7/3, Python 3.5/2, JavaScript null/0; user 1 sigue con 5★ en React). Nota: el DELETE es soft delete, así que queda una fila con `deleted_at` en `course_ratings`.
El problema: el servidor Next (SSR y Server Action) necesita alcanzar `localhost:8000` **desde dentro de su contenedor**, y el navegador del host necesita alcanzar el puerto 3000. `--network container:backend-api-1` resuelve lo primero, pero no permite publicar puertos (Docker solo publica puertos en el contenedor dueño de la red, y `backend-api-1` solo publica el 8000).

- **Opción A (recomendada): sidecar dueño de la red.**
  1. Levantar un contenedor liviano `alpine/socat` (nombre sugerido `platziflix-fe-net`) que **publique `-p 3000:3000`** y reenvíe su `localhost:8000` hacia `host.docker.internal:8000` (el puerto que ya publica la API).
  2. Correr `node:20` con `--network container:platziflix-fe-net` y los mismos volúmenes de F4.4, ejecutando `yarn dev -H 0.0.0.0` (o `yarn start -H 0.0.0.0` después de `yarn build`).
  3. Abrir `http://localhost:3000` en el navegador del host.
  4. Al terminar, `docker rm -f platziflix-fe-net`.
  - Ventajas: cero cambios en el repo; Next ve `localhost:8000` como siempre. Contras: dos contenedores; depende de `host.docker.internal`.
- **Opción B: publicar el 3000 en el propio contenedor Node** (`-p 3000:3000`, red por defecto) e instalar `socat` dentro con `apt-get` antes de `yarn dev`, reenviando `localhost:8000` → `host.docker.internal:8000`. Un solo contenedor, pero instala paquetes en cada arranque.
- **Opción C (decisión del usuario): instalar Node 20 + yarn en el host.** `yarn dev` alcanza `localhost:8000` directamente. Es lo más simple de operar, pero instala software en su máquina.
- **Descartado**: cambiar la URL a `host.docker.internal` o agregar el puerto 3000 al servicio `api` de `Backend/docker-compose.yml` (toca archivos del repo y del Backend por una necesidad local).
- **Criterio de terminado**: `http://localhost:3000/` abre en el navegador del host y muestra cursos con datos del seed.
- **Riesgos**: con la opción A/B, `make stop` corta la API; el sidecar queda vivo y reenvía a un puerto cerrado (lo que F5.2 caso 4 necesita). Hot reload de `yarn dev` sobre un bind mount de Windows puede no detectar cambios; no importa para esta verificación.

#### F5.2: Checklist de verificación ⏳ pendiente (la hace el usuario en `http://localhost:3000`)
Registrar cada punto como OK/KO en la descripción del PR (capturas opcionales):
1. `/`: cada curso muestra estrellas y conteo; el curso sin votos del seed (course3) muestra el estado vacío en español.
2. `/course/{slug}`: clic en 4 estrellas → feedback optimista inmediato; tras la revalidación cambian promedio y conteo; al recargar, el voto (4) sigue seleccionado.
3. Votar de nuevo con otro valor: el conteo **no** sube y el promedio cambia (upsert).
4. Con la API apagada (`make stop`) y la página ya cargada: votar muestra "No se pudo conectar con el servidor" y la selección vuelve al voto anterior. Luego `make start`.
5. Teclado: `Tab` recorre las 5 estrellas, `Enter`/`Espacio` vota; los lectores leen "Calificar con N estrellas" y `aria-pressed` refleja el voto actual.
6. Consola del navegador sin errores de hidratación ni de red hacia `:8000` (confirma que el navegador nunca llama a la API directo).
7. Volver a `/`: el promedio del curso votado refleja el cambio (`no-store`, sin revalidación explícita).
- **Criterio de terminado**: 7/7 OK registrados.
- **Riesgos**: el voto del usuario demo persiste entre pruebas; para repetir el caso "primer voto" correr `make seed-fresh` (o `DELETE /courses/{id}/ratings/user/1`, dado D1).

## 4. Riesgos y casos borde transversales
- **URL hardcodeada** `http://localhost:8000` en `page.tsx` y `actions.ts` (deuda 4): condiciona toda la estrategia de F5.1. No se cambia en este alcance.
- **Dependencia de contrato con el Backend**: el Frontend asume los campos `average_rating` (1 decimal o `null`) y `total_ratings`, y los códigos de `POST` (201/200, 404, 422) del contrato. Si el agente de Backend cambia algo en las fases 8–9 (no debería: son deps y tests), hay que revisar `src/types/index.ts` y `actions.ts`.
- **`/classes/[class_id]` sigue roto en runtime** tras F4 (endpoint inexistente, link a `/course`). Solo se arregla el build.
- **`rateCourse` solo revalida `/course/{slug}`**: `/` no queda desactualizado porque usa `no-store` (se valida en F5.2 caso 7).
- **Identidad compartida**: todos los navegadores votan como `user_id = 1`.

## 5. Fuera de alcance
- UI para retirar el voto (D1), auth real, base URL configurable, endpoint de clases y migración del tipo `Class`, reemplazar `<img>` por `next/image`, mobile.

## 6. Orden de ejecución sugerido
F1–F4 ✅ → D5 ✅ → F5.1 ✅ → F5.2 ⏳ (usuario) → PR `mi-curso` → `main` junto con las fases del Backend.
