// Course types (GET /courses, see Backend/specs/00_contracts.md)
export interface Course {
  id: number;
  name: string;
  description: string;
  thumbnail: string;
  slug: string;
  average_rating: number | null; // null when the course has no ratings
  total_ratings: number;
}

// Class summary as returned inside GET /courses/:slug
export interface ClassSummary {
  id: number;
  name: string;
  description: string;
  slug: string;
}

// Class as returned by GET /courses/:slug/classes/:id
export interface Class {
  id: number;
  name: string;
  description: string;
  slug: string;
  video_url: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

// Course Detail type (GET /courses/:slug)
export interface CourseDetail extends Course {
  teacher_id: number[];
  classes: ClassSummary[];
}

// Rating types (POST /courses/:course_id/ratings)
export interface Rating {
  id: number;
  course_id: number;
  user_id: number;
  rating: number; // 1 to 5
  created_at: string;
  updated_at: string;
}

// Progress types
export interface Progress {
  progress: number; // seconds
  user_id: number;
}

// Quiz types
export interface QuizOption {
  id: number;
  answer: string;
  correct: boolean;
}

export interface Quiz {
  id: number;
  question: string;
  options: QuizOption[];
}

// Favorite types
export interface FavoriteToggle {
  course_id: number;
}