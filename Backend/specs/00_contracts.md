# Platziflix

plataforma online de cursos, cada cursos tiene clases, descripciones y no hay mucho mas, eso es el inicio.

## Stacks

### Frontend
- Typescript
- CSS modules
- SASS

### Mobile
- iOS:
    - Swift
    - SwiftUI
- Android:
    - Kotlin
    - Jetpack Compose

### Backend
- Python
- FastAPI
- PostgreSQl

## Contratos

### Entidades
1. Curso
2. Clases
3. Profesor
4. Rating (calificación de un curso, de 1 a 5 estrellas)

### Contratos


- Course
```json
{
    "id": 1,
    "name": "Curso de React",
    "description": "Curso de React",
    "thumbnail": "https://via.placeholder.com/150", 
    "slug": "curso-de-react",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01",
    "teacher_id": [1, 2, 3]
}
```

- Clases:
```json
{
    "id": 1, 
    "course_id": 1, 
    "name": "Clase 1",
    "description": "Clase 1",
    "slug": "clase-1",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```

- Teacher
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```

- Rating:
```json
{
    "id": 1,
    "course_id": 1,
    "user_id": 1,
    "rating": 5,
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```
Reglas:
- `rating` es un entero entre 1 y 5.
- Un usuario tiene como máximo un rating activo por curso; volver a calificar actualiza el existente.
- No hay autenticación: `user_id` lo envía el cliente (por ahora un usuario demo fijo).

### Endpoints

- GET /courses -> Listar todos los cursos
```json
[
    {
        "id": 1,
        "name": "Curso de React",
        "description": "Curso de React",
        "thumbnail": "https://via.placeholder.com/150", 
        "slug": "curso-de-react",
        "average_rating": 4.5,
        "total_ratings": 2
    }
]
```
`average_rating` se redondea a 1 decimal y es `null` cuando el curso no tiene ratings (`total_ratings: 0`).

- GET /courses/:slug -> Obtener un curso
```json
{
    "id": 1,
    "name": "Curso de React",
    "description": "Curso de React",
    "thumbnail": "https://via.placeholder.com/150", 
    "slug": "curso-de-react",
    "teacher_id": [1, 2, 3],
    "average_rating": 4.5,
    "total_ratings": 2,
    "classes": [
        {
            "id": 1,
            "name": "Clase 1",
            "description": "Clase 1",
            "slug": "clase-1",
        }
    ]
}
```
- GET /courses/:slug/classes/:id -> Obtener una clase
```json
{
    "id": 1,
    "name": "Clase 1",
    "description": "Clase 1",
    "slug": "clase-1",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "created_at": "2021-01-01",
    "updated_at": "2021-01-01",
    "deleted_at": "2021-01-01"
}
```

- POST /courses/:course_id/ratings -> Calificar un curso (crea o actualiza el rating del usuario)

Request:
```json
{
    "user_id": 1,
    "rating": 5
}
```
Response `201` (rating nuevo) o `200` (rating actualizado):
```json
{
    "id": 1,
    "course_id": 1,
    "user_id": 1,
    "rating": 5,
    "created_at": "2021-01-01T00:00:00",
    "updated_at": "2021-01-01T00:00:00"
}
```
Errores: `404` si el curso no existe, `422` si `rating` no es un entero entre 1 y 5.

- GET /courses/:course_id/ratings/user/:user_id -> Obtener el rating de un usuario para un curso

Response `200`: mismo formato que la respuesta del POST. `404` si el curso no existe o el usuario no lo ha calificado.

- DELETE /courses/:course_id/ratings/user/:user_id -> Eliminar (soft delete) el rating de un usuario

Response `204` sin cuerpo. `404` si el curso no existe o el usuario no lo ha calificado.
