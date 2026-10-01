# Frontend en Docker

- Sin Node en el host: correr yarn con `docker run node:20` montando `Frontend/` y los volúmenes `platziflix_frontend_node_modules` / `platziflix_frontend_next`.
- Para abrir `localhost:3000` desde el host sin tocar la URL hardcodeada: contenedor `platziflix-fe-net` (`alpine/socat`, publica 3000 y reenvía su `localhost:8000` a `host.docker.internal:8000`) + `platziflix-fe-dev` (`node:20 yarn dev -H 0.0.0.0` con `--network container:platziflix-fe-net`). Comandos exactos en `spec/02_plan_frontend_ratings.md` (F5.1).
