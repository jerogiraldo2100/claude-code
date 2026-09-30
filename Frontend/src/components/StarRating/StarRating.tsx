import styles from "./StarRating.module.scss";

interface StarRatingProps {
  value: number | null;
  total: number;
}

export const StarRating = ({ value, total }: StarRatingProps) => {
  if (value === null || total === 0) {
    return <p className={styles.empty}>Sin calificaciones</p>;
  }

  return (
    <div className={styles.starRating}>
      <span className={styles.stars} role="img" aria-label={`${value} de 5 estrellas`}>
        {[0, 1, 2, 3, 4].map((index) => {
          // Portion of this star that is filled (0 to 100%)
          const fill = Math.min(Math.max(value - index, 0), 1) * 100;
          return (
            <span key={index} className={styles.star} aria-hidden="true">
              ★
              <span className={styles.starFill} style={{ width: `${fill}%` }}>
                ★
              </span>
            </span>
          );
        })}
      </span>
      <span className={styles.value}>{value.toFixed(1)}</span>
      <span className={styles.total}>
        ({total} {total === 1 ? "calificación" : "calificaciones"})
      </span>
    </div>
  );
};
