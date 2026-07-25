import { FormEvent, useState } from "react";
import { Mail, MapPin, Phone } from "lucide-react";
import { gesttoraLanding } from "@/content/gesttoraLanding";

export function Contact() {
  const { contact } = gesttoraLanding;
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setName("");
    setEmail("");
    setMessage("");
  };

  return (
    <section id="contact" className="gt-section gt-contact">
      <div className="gt-container gt-contact__grid">
        <div className="gt-contact__info">
          <p className="gt-eyebrow">{contact.eyebrow}</p>
          <h2 className="gt-section__title">{contact.title}</h2>

          <ul className="gt-contact__details">
            <li>
              <span className="gt-contact__icon">
                <Mail aria-hidden />
              </span>
              <div>
                <strong>E-mail</strong>
                <a href={`mailto:${contact.email}`}>{contact.email}</a>
              </div>
            </li>
            <li>
              <span className="gt-contact__icon">
                <MapPin aria-hidden />
              </span>
              <div>
                <strong>Endereço</strong>
                <span>{contact.address}</span>
              </div>
            </li>
            <li>
              <span className="gt-contact__icon">
                <Phone aria-hidden />
              </span>
              <div>
                <strong>Telefone</strong>
                <span>{contact.phone}</span>
              </div>
            </li>
          </ul>
        </div>

        <form className="gt-contact__form" onSubmit={handleSubmit}>
          <h3 className="gt-contact__form-title">{contact.formTitle}</h3>

          {submitted && (
            <p className="gt-contact__success" role="status">
              {contact.successMessage}
            </p>
          )}

          <label className="gt-field">
            <span>Nome</span>
            <input
              type="text"
              name="name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Seu nome"
            />
          </label>

          <label className="gt-field">
            <span>E-mail</span>
            <input
              type="email"
              name="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="voce@associacao.org.br"
            />
          </label>

          <label className="gt-field">
            <span>Mensagem</span>
            <textarea
              name="message"
              required
              rows={5}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Conte um pouco sobre a associação"
            />
          </label>

          <button type="submit" className="gt-btn gt-btn--primary gt-btn--block">
            Enviar
          </button>
        </form>
      </div>
    </section>
  );
}
