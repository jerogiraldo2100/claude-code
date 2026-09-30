"use server";

import { revalidatePath } from "next/cache";
import { DEMO_USER_ID } from "@/lib/demoUser";

export interface RateCourseResult {
  ok: boolean;
  error?: string;
}

// Runs on the server, so the browser never calls the API directly (the backend has no CORS)
export async function rateCourse(courseId: number, slug: string, rating: number): Promise<RateCourseResult> {
  if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
    return { ok: false, error: "La calificación debe ser un número entero entre 1 y 5" };
  }

  try {
    const response = await fetch(`http://localhost:8000/courses/${courseId}/ratings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: DEMO_USER_ID, rating }),
      cache: "no-store",
    });

    if (!response.ok) {
      return { ok: false, error: "No se pudo guardar tu calificación" };
    }
  } catch {
    return { ok: false, error: "No se pudo conectar con el servidor" };
  }

  revalidatePath(`/course/${slug}`);
  return { ok: true };
}
