import { notFound } from "next/navigation";
import { Class } from "@/types";
import { VideoPlayer } from "@/components/VideoPlayer/VideoPlayer";
import Link from "next/link";
import styles from "./page.module.scss";

interface ClassPageProps {
  params: Promise<{ slug: string; class_id: string }>;
}

async function getClassData(slug: string, class_id: string): Promise<Class> {
  const res = await fetch(`http://localhost:8000/courses/${slug}/classes/${class_id}`, { cache: "no-store" });
  // The API also answers 422 for a non-numeric class_id: treat it as missing
  if (res.status === 404 || res.status === 422) notFound();
  if (!res.ok) throw new Error("No se pudo cargar la clase");
  return res.json();
}

export default async function ClassPage({ params }: ClassPageProps) {
  const { slug, class_id } = await params;
  const classData = await getClassData(slug, class_id);

  return (
    <main className={styles.container}>
      <VideoPlayer src={classData.video_url} title={classData.name} />
      <h1 className={styles.title}>{classData.name}</h1>
      <p className={styles.description}>{classData.description}</p>
      <Link href={`/course/${slug}`} className={styles.backButton}>
        ← Regresar al curso
      </Link>
    </main>
  );
}
