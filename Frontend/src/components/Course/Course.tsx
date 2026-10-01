import styles from "./Course.module.scss";
import { Course as CourseType } from "@/types";
import { StarRating } from "@/components/StarRating/StarRating";

type CourseProps = Omit<CourseType, "slug">;

export const Course = ({ name, description, thumbnail, average_rating, total_ratings }: CourseProps) => {
  return (
    <article className={styles.courseCard}>
      <div className={styles.thumbnailContainer}>
        <img src={thumbnail} alt={name} className={styles.thumbnail} />
      </div>
      <div className={styles.courseInfo}>
        <h2 className={styles.courseTitle}>{name}</h2>
        <p className={styles.description}>{description}</p>
        <StarRating value={average_rating} total={total_ratings} />
      </div>
    </article>
  );
};
