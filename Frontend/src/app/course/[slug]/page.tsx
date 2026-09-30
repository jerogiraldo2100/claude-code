import { notFound } from "next/navigation";
import { CourseDetail, Rating } from "@/types";
import { CourseDetailComponent } from "@/components/CourseDetail/CourseDetail";
import { DEMO_USER_ID } from "@/lib/demoUser";

interface CoursePageProps {
  params: Promise<{
    slug: string;
  }>;
}

async function getCourseData(slug: string): Promise<CourseDetail> {
  const response = await fetch(`http://localhost:8000/courses/${slug}`, {
    cache: "no-store", // Ensures fresh data on each request
  });

  if (response.status === 404) {
    notFound();
  }

  if (!response.ok) {
    throw new Error("Failed to fetch course data");
  }

  return response.json();
}

// Returns null when the user hasn't rated the course (API responds 404)
async function getUserRating(courseId: number): Promise<number | null> {
  const response = await fetch(`http://localhost:8000/courses/${courseId}/ratings/user/${DEMO_USER_ID}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }

  const rating: Rating = await response.json();
  return rating.rating;
}

export default async function CoursePage({ params }: CoursePageProps) {
  const { slug } = await params;
  const courseData = await getCourseData(slug);
  const userRating = await getUserRating(courseData.id);

  return <CourseDetailComponent course={courseData} userRating={userRating} />;
}

export async function generateMetadata({ params }: CoursePageProps) {
  const { slug } = await params;
  const courseData = await getCourseData(slug);

  return {
    title: `${courseData.name} - Curso Online`,
    description: courseData.description,
  };
}
