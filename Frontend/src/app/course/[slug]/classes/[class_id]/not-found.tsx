import Link from "next/link";
import styles from "../../not-found.module.scss";

export default function NotFound() {
  return (
    <div className={styles.container}>
      <div className={styles.notFoundCard}>
        <h1 className={styles.title}>Clase no encontrada</h1>
        <p className={styles.message}>Lo sentimos, la clase que buscas no existe o ha sido removida.</p>
        <Link href="/" className={styles.homeButton}>
          Volver a cursos
        </Link>
      </div>
    </div>
  );
}
