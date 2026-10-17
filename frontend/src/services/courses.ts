import type {
  CertificateVerification,
  Course,
  CourseSection,
  CourseSummary,
  Lesson,
  LessonAttachment,
  LessonPayload,
  PortalEnrollment,
  PortalLesson,
  PublicCourse,
  StudentEnrollment,
  StudentQuestion,
} from "@/types/courses";
import { downloadBlob } from "@/utils/download";
import { api } from "./api";

const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };

function unwrapList<T>(data: { results?: T[] } | T[]): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

export { apiErrorMessage } from "@/utils/apiError";

// ---------------------------------------------------------------- Diretoria

export async function listCourses(params?: { status?: string; search?: string }): Promise<CourseSummary[]> {
  const { data } = await api.get("/api/courses/", { params });
  return unwrapList(data);
}

export async function getCourse(id: string): Promise<Course> {
  const { data } = await api.get<Course>(`/api/courses/${id}/`);
  return data;
}

export async function createCourse(payload: Partial<Course> | FormData): Promise<Course> {
  const config = payload instanceof FormData ? MULTIPART : undefined;
  const { data } = await api.post<Course>("/api/courses/", payload, config);
  return data;
}

export async function updateCourse(id: string, payload: Partial<Course> | FormData): Promise<Course> {
  const config = payload instanceof FormData ? MULTIPART : undefined;
  const { data } = await api.patch<Course>(`/api/courses/${id}/`, payload, config);
  return data;
}

export async function deleteCourse(id: string): Promise<void> {
  await api.delete(`/api/courses/${id}/`);
}

export async function duplicateCourse(id: string): Promise<Course> {
  const { data } = await api.post<Course>(`/api/courses/${id}/duplicate/`, {});
  return data;
}

export async function createCourseCatalogItem(id: string, price: string): Promise<Course> {
  const { data } = await api.post<Course>(`/api/courses/${id}/create-catalog-item/`, { price });
  return data;
}

export async function reorderCourse(
  id: string,
  sections: { id: string; lesson_ids: string[] }[]
): Promise<Course> {
  const { data } = await api.post<Course>(`/api/courses/${id}/reorder/`, { sections });
  return data;
}

export async function listStudents(id: string): Promise<StudentEnrollment[]> {
  const { data } = await api.get(`/api/courses/${id}/students/`);
  return unwrapList(data);
}

export async function enrollStudent(id: string, membroId: string): Promise<StudentEnrollment> {
  const { data } = await api.post<StudentEnrollment>(`/api/courses/${id}/students/`, { membro: membroId });
  return data;
}

export async function setStudentStatus(
  id: string,
  enrollmentId: string,
  status: "active" | "revoked"
): Promise<StudentEnrollment> {
  const { data } = await api.patch<StudentEnrollment>(`/api/courses/${id}/students/${enrollmentId}/`, { status });
  return data;
}

export async function createSection(course: string, title: string): Promise<CourseSection> {
  const { data } = await api.post<CourseSection>("/api/courses/sections/", { course, title });
  return data;
}

export async function updateSection(id: string, title: string): Promise<CourseSection> {
  const { data } = await api.patch<CourseSection>(`/api/courses/sections/${id}/`, { title });
  return data;
}

export async function deleteSection(id: string): Promise<void> {
  await api.delete(`/api/courses/sections/${id}/`);
}

export async function createLesson(payload: LessonPayload): Promise<Lesson> {
  const { data } = await api.post<Lesson>("/api/courses/lessons/", payload);
  return data;
}

export async function updateLesson(id: string, payload: LessonPayload): Promise<Lesson> {
  const { data } = await api.patch<Lesson>(`/api/courses/lessons/${id}/`, payload);
  return data;
}

export async function deleteLesson(id: string): Promise<void> {
  await api.delete(`/api/courses/lessons/${id}/`);
}

export async function uploadAttachment(lessonId: string, file: File, title: string): Promise<LessonAttachment> {
  const form = new FormData();
  form.append("lesson", lessonId);
  form.append("title", title);
  form.append("file", file);
  const { data } = await api.post<LessonAttachment>("/api/courses/attachments/", form, MULTIPART);
  return data;
}

export async function deleteAttachment(id: string): Promise<void> {
  await api.delete(`/api/courses/attachments/${id}/`);
}

export async function uploadContentImage(file: File): Promise<string> {
  const form = new FormData();
  form.append("image", file);
  const { data } = await api.post<{ url: string }>("/api/courses/uploads/image/", form, MULTIPART);
  return data.url;
}

export async function listInstructorQuestions(params?: {
  course?: string;
  answered?: "true" | "false";
}): Promise<StudentQuestion[]> {
  const { data } = await api.get("/api/courses/questions/", { params });
  return unwrapList(data);
}

export async function replyInstructorQuestion(id: string, body: string): Promise<StudentQuestion> {
  const { data } = await api.post<StudentQuestion>(`/api/courses/questions/${id}/reply/`, { body });
  return data;
}

export async function deleteInstructorQuestion(id: string): Promise<void> {
  await api.delete(`/api/courses/questions/${id}/`);
}

// ---------------------------------------------------------------- Portal do associado

export async function listMyCourses(): Promise<PortalEnrollment[]> {
  const { data } = await api.get("/api/courses/my/");
  return unwrapList(data);
}

export async function getMyCourse(enrollmentId: string): Promise<PortalEnrollment> {
  const { data } = await api.get<PortalEnrollment>(`/api/courses/my/${enrollmentId}/`);
  return data;
}

export async function getMyLesson(enrollmentId: string, lessonId: string): Promise<PortalLesson> {
  const { data } = await api.get<PortalLesson>(`/api/courses/my/${enrollmentId}/lessons/${lessonId}/`);
  return data;
}

type LessonAndEnrollment = { lesson: PortalLesson; enrollment: PortalEnrollment };

export async function completeMyLesson(enrollmentId: string, lessonId: string): Promise<LessonAndEnrollment> {
  const { data } = await api.post<LessonAndEnrollment>(
    `/api/courses/my/${enrollmentId}/lessons/${lessonId}/complete/`,
    {}
  );
  return data;
}

export async function submitMyQuiz(
  enrollmentId: string,
  lessonId: string,
  answers: Record<string, string[]>
): Promise<LessonAndEnrollment> {
  const { data } = await api.post<LessonAndEnrollment>(
    `/api/courses/my/${enrollmentId}/lessons/${lessonId}/quiz/`,
    { answers }
  );
  return data;
}

export async function listLessonQuestions(enrollmentId: string, lessonId: string): Promise<StudentQuestion[]> {
  const { data } = await api.get(`/api/courses/my/${enrollmentId}/lessons/${lessonId}/questions/`);
  return unwrapList(data);
}

export async function askLessonQuestion(enrollmentId: string, lessonId: string, body: string): Promise<StudentQuestion> {
  const { data } = await api.post<StudentQuestion>(
    `/api/courses/my/${enrollmentId}/lessons/${lessonId}/questions/`,
    { body }
  );
  return data;
}

export async function replyLessonQuestion(
  enrollmentId: string,
  questionId: string,
  body: string
): Promise<StudentQuestion> {
  const { data } = await api.post<StudentQuestion>(
    `/api/courses/my/${enrollmentId}/questions/${questionId}/replies/`,
    { body }
  );
  return data;
}

export async function downloadMyCertificate(enrollmentId: string, slug: string): Promise<void> {
  await downloadBlob(`/api/courses/my/${enrollmentId}/certificate/`, `certificado-${slug}.pdf`);
}

// ---------------------------------------------------------------- Site público

export async function listPublicCourses(schema: string): Promise<PublicCourse[]> {
  const { data } = await api.get("/api/courses/public/", { params: { schema } });
  return unwrapList(data);
}

export async function getPublicCourse(schema: string, slug: string): Promise<PublicCourse> {
  const { data } = await api.get<PublicCourse>(`/api/courses/public/${slug}/`, { params: { schema } });
  return data;
}

export async function getPublicLessonPreview(schema: string, slug: string, lessonId: string): Promise<PortalLesson> {
  const { data } = await api.get<PortalLesson>(`/api/courses/public/${slug}/lessons/${lessonId}/`, {
    params: { schema },
  });
  return data;
}

export async function verifyCertificate(schema: string, code: string): Promise<CertificateVerification> {
  const { data } = await api.get<CertificateVerification>(`/api/certificados/${encodeURIComponent(code)}/`, {
    params: { schema },
  });
  return data;
}

export async function downloadPublicCertificate(schema: string, code: string) {
  await downloadBlob(`/api/certificados/${encodeURIComponent(code)}/pdf/`, `certificado-${code}.pdf`, {
    params: { schema },
  });
}
