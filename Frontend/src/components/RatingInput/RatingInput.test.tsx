import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { RatingInput } from "./RatingInput";
import { rateCourse } from "@/app/course/[slug]/actions";

vi.mock("@/app/course/[slug]/actions", () => ({
  rateCourse: vi.fn(),
}));

const mockedRateCourse = vi.mocked(rateCourse);

describe("RatingInput Component", () => {
  beforeEach(() => {
    mockedRateCourse.mockReset();
  });

  it("renders 5 star buttons", () => {
    render(<RatingInput courseId={1} slug="curso-de-react" initialRating={null} />);

    expect(screen.getAllByRole("button")).toHaveLength(5);
    expect(screen.getByText("Aún no has calificado este curso")).toBeInTheDocument();
  });

  it("shows the user's current rating", () => {
    render(<RatingInput courseId={1} slug="curso-de-react" initialRating={4} />);

    expect(screen.getByRole("button", { name: "Calificar con 4 estrellas" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Tu calificación: 4 de 5")).toBeInTheDocument();
  });

  it("sends the selected rating to the server action", async () => {
    mockedRateCourse.mockResolvedValue({ ok: true });
    render(<RatingInput courseId={1} slug="curso-de-react" initialRating={null} />);

    fireEvent.click(screen.getByRole("button", { name: "Calificar con 3 estrellas" }));

    expect(mockedRateCourse).toHaveBeenCalledWith(1, "curso-de-react", 3);
    await waitFor(() => expect(screen.getByText("Tu calificación: 3 de 5")).toBeInTheDocument());
  });

  it("restores the previous rating and shows an error when saving fails", async () => {
    mockedRateCourse.mockResolvedValue({ ok: false, error: "No se pudo guardar tu calificación" });
    render(<RatingInput courseId={1} slug="curso-de-react" initialRating={2} />);

    fireEvent.click(screen.getByRole("button", { name: "Calificar con 5 estrellas" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo guardar tu calificación");
    expect(screen.getByText("Tu calificación: 2 de 5")).toBeInTheDocument();
  });
});
