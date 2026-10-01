"use client";

import { useState, useTransition } from "react";
import { rateCourse } from "@/app/course/[slug]/actions";
import styles from "./RatingInput.module.scss";

interface RatingInputProps {
  courseId: number;
  slug: string;
  initialRating: number | null;
}

export const RatingInput = ({ courseId, slug, initialRating }: RatingInputProps) => {
  const [selected, setSelected] = useState<number | null>(initialRating);
  const [hovered, setHovered] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleRate = (rating: number) => {
    const previous = selected;
    setSelected(rating);
    setError(null);

    startTransition(async () => {
      const result = await rateCourse(courseId, slug, rating);
      if (!result.ok) {
        setSelected(previous);
        setError(result.error ?? "No se pudo guardar tu calificación");
      }
    });
  };

  const highlighted = hovered ?? selected ?? 0;

  return (
    <div className={styles.ratingInput}>
      <div className={styles.stars} onMouseLeave={() => setHovered(null)}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`${styles.star} ${star <= highlighted ? styles.active : ""}`}
            aria-label={`Calificar con ${star} ${star === 1 ? "estrella" : "estrellas"}`}
            aria-pressed={selected === star}
            disabled={isPending}
            onMouseEnter={() => setHovered(star)}
            onClick={() => handleRate(star)}
          >
            ★
          </button>
        ))}
      </div>
      <p className={styles.status} role="status">
        {isPending
          ? "Guardando..."
          : selected
            ? `Tu calificación: ${selected} de 5`
            : "Aún no has calificado este curso"}
      </p>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </div>
  );
};
