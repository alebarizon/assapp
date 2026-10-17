import { useEffect, useRef } from "react";
import {
  Bold,
  Heading2,
  Heading3,
  Image as ImageIcon,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
  Quote,
  RemoveFormatting,
  Underline,
} from "lucide-react";
import { apiErrorMessage, uploadContentImage } from "@/services/courses";

interface RichTextEditorProps {
  value: string;
  onChange: (html: string) => void;
  placeholder?: string;
  onUploadError?: (message: string) => void;
}

/**
 * Editor leve (contentEditable) sem dependências externas.
 * O HTML é sanitizado no backend (courses/html_sanitizer.py).
 */
export default function RichTextEditor({ value, onChange, placeholder, onUploadError }: RichTextEditorProps) {
  const areaRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = areaRef.current;
    if (el && el.innerHTML !== value && document.activeElement !== el) {
      el.innerHTML = value || "";
    }
  }, [value]);

  const emit = () => onChange(areaRef.current?.innerHTML ?? "");

  const exec = (command: string, arg?: string) => {
    areaRef.current?.focus();
    document.execCommand(command, false, arg);
    emit();
  };

  const addLink = () => {
    const url = window.prompt("Endereço do link (https://...)");
    if (url) exec("createLink", url);
  };

  const handleImage = async (file: File | undefined) => {
    if (!file) return;
    try {
      const url = await uploadContentImage(file);
      exec("insertImage", url);
    } catch (err) {
      onUploadError?.(apiErrorMessage(err, "Não foi possível enviar a imagem."));
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const tools = [
    { icon: Bold, title: "Negrito", run: () => exec("bold") },
    { icon: Italic, title: "Itálico", run: () => exec("italic") },
    { icon: Underline, title: "Sublinhado", run: () => exec("underline") },
    { icon: Heading2, title: "Título", run: () => exec("formatBlock", "<h2>") },
    { icon: Heading3, title: "Subtítulo", run: () => exec("formatBlock", "<h3>") },
    { icon: List, title: "Lista", run: () => exec("insertUnorderedList") },
    { icon: ListOrdered, title: "Lista numerada", run: () => exec("insertOrderedList") },
    { icon: Quote, title: "Citação", run: () => exec("formatBlock", "<blockquote>") },
    { icon: LinkIcon, title: "Link", run: addLink },
    { icon: ImageIcon, title: "Imagem", run: () => fileRef.current?.click() },
    { icon: RemoveFormatting, title: "Limpar formatação", run: () => exec("removeFormat") },
  ];

  return (
    <div className="rich-editor">
      <div className="rich-editor-toolbar">
        {tools.map(({ icon: Icon, title, run }) => (
          <button key={title} type="button" title={title} onMouseDown={(e) => e.preventDefault()} onClick={run}>
            <Icon size={15} />
          </button>
        ))}
        <input
          ref={fileRef}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          style={{ display: "none" }}
          onChange={(e) => handleImage(e.target.files?.[0])}
        />
      </div>
      <div
        ref={areaRef}
        className="rich-editor-area course-prose"
        contentEditable
        suppressContentEditableWarning
        data-placeholder={placeholder || "Escreva o conteúdo..."}
        onInput={emit}
        onBlur={emit}
      />
    </div>
  );
}
