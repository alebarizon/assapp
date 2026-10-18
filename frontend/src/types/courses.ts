export type CourseStatus = "draft" | "published" | "archived";
export type CourseVisibility = "public" | "unlisted";
export type ProgressionMode = "sequential" | "free";
export type CourseLevel = "beginner" | "intermediate" | "advanced";
export type LessonType = "text" | "video" | "quiz";
export type QuestionType = "single" | "multiple" | "true_false";
export type EnrollmentStatus = "active" | "completed" | "revoked";

export interface CatalogItemInfo {
  id: string;
  slug: string;
  name: string;
  price: string;
  member_price?: string | null;
  currency: string;
  is_active: boolean;
}

export interface QuizOption {
  id?: string;
  text: string;
  is_correct?: boolean;
  position?: number;
}

export interface QuizQuestion {
  id?: string;
  prompt: string;
  question_type: QuestionType;
  explanation?: string;
  position?: number;
  options: QuizOption[];
}

export interface LessonAttachment {
  id: string;
  title: string;
  file_url: string | null;
  file_type: string;
  size_bytes: number;
}

export interface Lesson {
  id: string;
  section: string;
  title: string;
  lesson_type: LessonType;
  content: string;
  video_url: string;
  youtube_id: string | null;
  duration_minutes: number | null;
  is_preview: boolean;
  position: number;
  attachments: LessonAttachment[];
  questions: QuizQuestion[];
}

export interface CourseSection {
  id: string;
  course: string;
  title: string;
  position: number;
  lessons: Lesson[];
}

export interface CourseSummary {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  cover_image_url: string | null;
  level: CourseLevel;
  status: CourseStatus;
  status_display: string;
  visibility: CourseVisibility;
  progression_mode: ProgressionMode;
  catalog_item: string | null;
  catalog_item_info: CatalogItemInfo | null;
  lessons_count: number;
  students_count: number;
  unanswered_questions_count: number;
}

export interface Course {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  description: string;
  cover_image_url: string | null;
  instructor_name: string;
  workload_hours: number | null;
  level: CourseLevel;
  progression_mode: ProgressionMode;
  status: CourseStatus;
  status_display: string;
  visibility: CourseVisibility;
  catalog_item: string | null;
  catalog_item_info: CatalogItemInfo | null;
  certificate_enabled: boolean;
  sections: CourseSection[];
}

export interface ProgressSummary {
  total_lessons: number;
  completed_lessons: number;
  percent_complete: number;
  next_lesson_id: string | null;
  next_lesson_title: string | null;
}

export interface StudentEnrollment {
  id: string;
  membro: string;
  membro_nome: string;
  membro_email: string;
  status: EnrollmentStatus;
  status_display: string;
  enrolled_at: string;
  completed_at: string | null;
  last_accessed_at: string | null;
  certificate_code: string;
  progress: ProgressSummary;
  average_quiz_score: number | null;
}

export interface QuestionReply {
  id: string;
  author_name: string;
  is_instructor: boolean;
  body: string;
  created_at: string;
}

export interface StudentQuestion {
  id: string;
  lesson: string;
  lesson_title: string;
  course_id: string;
  course_title: string;
  author_name: string;
  is_mine: boolean;
  body: string;
  is_answered: boolean;
  replies: QuestionReply[];
  created_at: string;
}

export interface OutlineLesson {
  id: string;
  title: string;
  lesson_type: LessonType;
  duration_minutes: number | null;
  completed: boolean;
  locked: boolean;
}

export interface PortalEnrollment {
  id: string;
  status: EnrollmentStatus;
  enrolled_at: string;
  completed_at: string | null;
  last_lesson: string | null;
  certificate_available: boolean;
  progress: ProgressSummary;
  course: {
    id: string;
    title: string;
    slug: string;
    short_description: string;
    cover_image_url: string | null;
    instructor_name: string;
    workload_hours: number | null;
    level: CourseLevel;
    progression_mode: ProgressionMode;
    description?: string;
    sections?: { id: string; title: string; lessons: OutlineLesson[] }[];
  };
}

export interface QuizResult {
  question_id: string;
  selected_option_ids: string[];
  correct_option_ids: string[];
  is_correct: boolean;
  explanation: string;
}

export interface PortalLesson {
  id: string;
  section_id: string;
  title: string;
  lesson_type: LessonType;
  content: string;
  youtube_id: string | null;
  duration_minutes: number | null;
  attachments: LessonAttachment[];
  questions?: {
    id: string;
    prompt: string;
    question_type: QuestionType;
    options: { id: string; text: string }[];
  }[];
  completed?: boolean;
  previous_lesson_id?: string | null;
  next_lesson_id?: string | null;
  last_attempt?: {
    id: string;
    created_at: string;
    score_percent: number;
    correct_count: number;
    total_count: number;
    results: QuizResult[];
  } | null;
}

export interface PublicCourse {
  id: string;
  slug: string;
  title: string;
  short_description: string;
  cover_image_url: string | null;
  instructor_name: string;
  workload_hours: number | null;
  level: CourseLevel;
  progression_mode: ProgressionMode;
  certificate_enabled: boolean;
  catalog_item_info: CatalogItemInfo | null;
  lessons_count: number;
  total_duration_minutes: number;
  description?: string;
  sections?: {
    id: string;
    title: string;
    lessons: {
      id: string;
      title: string;
      lesson_type: LessonType;
      duration_minutes: number | null;
      is_preview: boolean;
    }[];
  }[];
}

export interface CertificateVerification {
  valid: boolean;
  kind: "curso" | "evento";
  code: string;
  participant_name: string;
  title: string;
  action: string;
  workload_hours: number | null;
  issued_at: string | null;
  issuer: string;
}

export type LessonPayload = Partial<Omit<Lesson, "id" | "attachments" | "youtube_id">>;

export const COURSE_LEVELS: { value: CourseLevel; label: string }[] = [
  { value: "beginner", label: "Iniciante" },
  { value: "intermediate", label: "Intermediário" },
  { value: "advanced", label: "Avançado" },
];

export const LESSON_TYPE_LABELS: Record<LessonType, string> = {
  text: "Texto",
  video: "Vídeo",
  quiz: "Quiz",
};

export const COURSE_STATUS_BADGE: Record<CourseStatus, string> = {
  draft: "rascunho",
  published: "ativo",
  archived: "arquivado",
};

export const ENROLLMENT_STATUS_BADGE: Record<EnrollmentStatus, string> = {
  active: "ativo",
  completed: "aceito",
  revoked: "inativa",
};
