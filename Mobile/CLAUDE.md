# Mobile

Ambas apps usan Clean Architecture: `Data` (DTO → Mapper → Repository) / `Domain` (modelos + interfaz repo) / `Presentation` (ViewModel + UI). Guías en `.cursor/context/` de cada app.

**Android** `Mobile/PlatziFlixAndroid/` — Kotlin · Jetpack Compose
- MVI: `StateFlow<UiState>` + `handleEvent(UiEvent)`.
- DI manual en `di/AppModule.kt` (`USE_MOCK_DATA` alterna `MockCourseRepository`/`RemoteCourseRepository`).
- Base URL en `data/network/NetworkModule.kt`. Build/test: `./gradlew assembleDebug`, `./gradlew test`.
- Feature actual: solo lista de cursos.

**iOS** `Mobile/PlatziFlixiOS/` — Swift · SwiftUI
- MVVM: `@MainActor ObservableObject` + `@Published`; DI por inicializador.
- Red: `Services/NetworkManager` + protocolo `APIEndpoint`; endpoints en `Data/Repositories/CourseAPIEndpoints.swift`.
- Feature actual: lista + búsqueda local; navegación a detalle es TODO. Se abre con Xcode.
