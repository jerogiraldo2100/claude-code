import { renderToString } from "react-dom/server";
import ClassPage from "./page";
import { Class } from "@/types";
import { describe, it, expect, vi } from "vitest";

vi.mock("@/components/VideoPlayer/VideoPlayer", () => ({
  VideoPlayer: ({ src, title }: { src: string; title: string }) => (
    <div data-testid="mock-video-player">
      {title} - {src}
    </div>
  ),
}));

// Mock de fetch que resuelve inmediatamente
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: () =>
    Promise.resolve({
      id: 19,
      name: "Clase de Test",
      description: "Descripción de la clase de test",
      slug: "clase-test",
      video_url: "https://test.com/video.mp4",
      created_at: "2026-01-01T00:00:00",
      updated_at: "2026-01-01T00:00:00",
      deleted_at: null,
    } as Class),
});

describe("ClassPage", () => {
  it("renders class info and video", async () => {
    // Async Server Component: resolve it first, then render the returned element
    const element = await ClassPage({ params: Promise.resolve({ slug: "curso-de-react", class_id: "19" }) });
    const html = renderToString(element);

    expect(html).toContain("Clase de Test");
    expect(html).toContain("Descripción de la clase de test");
    expect(html).toContain("mock-video-player");
    expect(html).toContain("Regresar al curso");
    expect(html).toContain('href="/course/curso-de-react"');
    expect(global.fetch).toHaveBeenCalledWith("http://localhost:8000/courses/curso-de-react/classes/19", { cache: "no-store" });
  }, 10000); // Aumentamos el timeout a 10 segundos
});
