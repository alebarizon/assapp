import { FileText } from "lucide-react";
import type { PortalLesson } from "@/types/courses";

/** Vídeo, texto e anexos de uma aula (portal e amostra pública). */
export default function LessonContent({ lesson }: { lesson: PortalLesson }) {
  return (
    <div>
      {lesson.lesson_type === "video" && lesson.youtube_id && (
        <div className="course-video">
          <iframe
            src={`https://www.youtube-nocookie.com/embed/${lesson.youtube_id}?rel=0`}
            title={lesson.title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      )}
      {lesson.content && (
        <div className="course-prose" dangerouslySetInnerHTML={{ __html: lesson.content }} />
      )}
      {lesson.attachments.length > 0 && (
        <div style={{ marginTop: "1.25rem" }}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 0.5rem" }}>Materiais</h3>
          {lesson.attachments.map((a) => (
            <div key={a.id} className="course-lesson-row" style={{ paddingLeft: 0 }}>
              <FileText size={15} />
              <a href={a.file_url || "#"} target="_blank" rel="noopener noreferrer">
                {a.title}
              </a>
              <span className="course-muted">{a.file_type.toUpperCase()}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
