const projects = [
  {
    title: "Project One",
    description: "A short description of an impressive project you built.",
    tech: ["Next.js", "TypeScript", "Tailwind CSS"],
  },
  {
    title: "Project Two",
    description: "Another strong example focused on real-world impact.",
    tech: ["React", "Node.js", "PostgreSQL"],
  },
  {
    title: "Project Three",
    description: "Highlight your role, challenges, and results here.",
    tech: ["Design Systems", "UI/UX", "Figma"],
  },
];

const skills = [
  "Next.js",
  "React",
  "TypeScript",
  "Node.js",
  "UI/UX Design",
  "REST APIs",
  "Performance",
  "Accessibility",
];

export default function Home() {
  return (
    <main>
      <header className="nav">
        <div className="nav-inner">
          <div className="logo">YN</div>
          <nav className="nav-links">
            <a href="#about">About</a>
            <a href="#projects">Projects</a>
            <a href="#skills">Skills</a>
            <a href="#contact" className="btn-ghost">
              Contact
            </a>
          </nav>
        </div>
      </header>

      <section className="hero" id="top">
        <div className="hero-content">
          <p className="hero-eyebrow">Portfolio · Next.js</p>
          <h1>
            Crafting clean, modern
            <br />
            digital experiences.
          </h1>
          <p className="hero-subtitle">
            I&apos;m{" "}
            <span className="accent">Your Name</span>, a{" "}
            <span className="accent">frontend engineer</span> focused on
            building fast, accessible, and beautiful web products.
          </p>
          <div className="hero-actions">
            <a href="#projects" className="btn-primary">
              View projects
            </a>
            <a href="#contact" className="btn-secondary">
              Let&apos;s work together
            </a>
          </div>
          <div className="hero-meta">
            <span>Available for freelance & full‑time roles</span>
            <span>Based in Your City · Open to remote</span>
          </div>
        </div>
        <div className="hero-card">
          <div className="hero-avatar" />
          <div className="hero-card-body">
            <p>Currently improving</p>
            <h3>Conversion-focused landing pages</h3>
            <p className="hero-card-detail">
              I blend product thinking, interaction design, and engineering to
              ship experiences that feel polished and intentional.
            </p>
          </div>
        </div>
      </section>

      <section className="section" id="about">
        <div className="section-header">
          <h2>About</h2>
          <p>
            A short, clear story about who you are, what you do, and the kind
            of work you enjoy.
          </p>
        </div>
        <div className="about-grid">
          <p>
            I&apos;m a frontend-focused engineer with a passion for design
            systems, motion, and delightful micro‑interactions. I care about
            clear structure, strong typography, and experiences that feel
            effortless to use.
          </p>
          <p>
            Recently, I&apos;ve been working on high‑impact marketing sites and
            product dashboards, collaborating closely with designers and
            product teams to move key metrics like activation and retention.
          </p>
        </div>
      </section>

      <section className="section" id="projects">
        <div className="section-header">
          <h2>Selected projects</h2>
          <p>Work that showcases your strengths and the problems you solve.</p>
        </div>
        <div className="cards-grid">
          {projects.map((project) => (
            <article key={project.title} className="card">
              <div className="card-pill">Case study</div>
              <h3>{project.title}</h3>
              <p>{project.description}</p>
              <ul className="pill-row">
                {project.tech.map((item) => (
                  <li key={item} className="pill">
                    {item}
                  </li>
                ))}
              </ul>
              <button className="link-button" type="button">
                View details
                <span aria-hidden>↗</span>
              </button>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="skills">
        <div className="section-header">
          <h2>Skills</h2>
          <p>
            A quick overview of the tools and areas you&apos;re strongest in.
          </p>
        </div>
        <div className="skills-grid">
          {skills.map((skill) => (
            <div key={skill} className="skill-chip">
              {skill}
            </div>
          ))}
        </div>
      </section>

      <section className="section" id="contact">
        <div className="contact-card">
          <h2>Let&apos;s build something great</h2>
          <p>
            Share a bit about your project, timeline, or team. I&apos;ll respond
            within 1–2 business days.
          </p>
          <form
            className="contact-form"
            onSubmit={(e) => {
              e.preventDefault();
              alert("This is a static demo form. Replace with your own logic.");
            }}
          >
            <div className="form-row">
              <div className="field">
                <label htmlFor="name">Name</label>
                <input id="name" name="name" placeholder="Your name" />
              </div>
              <div className="field">
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                />
              </div>
            </div>
            <div className="field">
              <label htmlFor="message">Project details</label>
              <textarea
                id="message"
                name="message"
                rows={4}
                placeholder="Tell me about what you want to build..."
              />
            </div>
            <button className="btn-primary" type="submit">
              Send message
            </button>
          </form>
          <div className="contact-meta">
            <span>Email: you@yourdomain.com</span>
            <span>LinkedIn · GitHub · Dribbble</span>
          </div>
        </div>
      </section>

      <footer className="footer">
        <span>© {new Date().getFullYear()} Your Name</span>
        <span>Built with Next.js</span>
      </footer>
    </main>
  );
}

