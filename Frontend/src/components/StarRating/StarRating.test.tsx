import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StarRating } from "./StarRating";

describe("StarRating Component", () => {
  it("renders the average with one decimal and an accessible label", () => {
    render(<StarRating value={4} total={3} />);

    expect(screen.getByRole("img", { name: "4 de 5 estrellas" })).toBeInTheDocument();
    expect(screen.getByText("4.0")).toBeInTheDocument();
    expect(screen.getByText("(3 calificaciones)")).toBeInTheDocument();
  });

  it("uses singular text for a single rating", () => {
    render(<StarRating value={5} total={1} />);

    expect(screen.getByText("(1 calificación)")).toBeInTheDocument();
  });

  it("fills stars proportionally to the average", () => {
    const { container } = render(<StarRating value={3.5} total={2} />);

    const fills = Array.from(container.querySelectorAll<HTMLElement>("span[style]")).map(
      (element) => element.style.width
    );
    expect(fills).toEqual(["100%", "100%", "100%", "50%", "0%"]);
  });

  it("renders a placeholder when there are no ratings", () => {
    render(<StarRating value={null} total={0} />);

    expect(screen.getByText("Sin calificaciones")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
