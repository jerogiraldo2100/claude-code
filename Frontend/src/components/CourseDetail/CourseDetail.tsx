import { FC } from "react";
import Link from "next/link";
import { CourseDetail } from "@/types";
import { StarRating } from "@/components/StarRating/StarRating";
import { RatingInput } from "@/components/RatingInput/RatingInput";
import styles from "./CourseDetail.module.scss";

interface CourseDetailComponentProps {
  course: CourseDetail;
  userRating: number | null;
}

export const CourseDetailComponent: FC<CourseDetailComponentProps> = ({ course, userRating }) => {
  return (
    <div className={styles.container}>
      <div className={styles.navigation}>
        <Link href="/" className={styles.backButton}>
          ← Volver a cursos
        </Link>
      </div>
      <div className={styles.header}>
        <div className={styles.thumbnailContainer}>
          <img src={course.thumbnail} alt={course.name} className={styles.thumbnail} />
        </div>
        <div className={styles.courseInfo}>
          <h1 className={styles.title}>{course.name}</h1>
          <StarRating value={course.average_rating} total={course.total_ratings} />
          <p className={styles.description}>{course.description}</p>
          <div className={styles.stats}>
            <span className={styles.classCount}>{course.classes.length} clases</span>
          </div>
          <div className={styles.rateSection}>
            <h2 className={styles.rateTitle}>Califica este curso</h2>
            <RatingInput courseId={course.id} slug={course.slug} initialRating={userRating} />
          </div>
        </div>
      </div>

      <div className={styles.classesSection}>
        <h2 className={styles.sectionTitle}>Contenido del curso</h2>
        <div className={styles.classesList}>
          {course.classes.map((cls, index) => (
            <Link href={`/course/${course.slug}/classes/${cls.id}`} key={cls.id} className={styles.classItem}>
              <div className={styles.classNumber}>{(index + 1).toString().padStart(2, "0")}</div>
              <div className={styles.classInfo}>
                <h3 className={styles.classTitle}>{cls.name}</h3>
                <p className={styles.classDescription}>{cls.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};
