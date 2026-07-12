
Cribra — Frontend Brief
A brief for the frontend developer: what we're building, how it should feel, and every screen and component needed.

1. What Cribra is
   Cribra is a web application that helps public-sector procurement officers check whether a contractor's tender submission meets the mandatory eligibility and technical-compliance requirements of Nigerian construction procurement (the Public Procurement Act 2007 and the Bureau of Public Procurement Standard Bidding Documents).

The name comes from the Latin word for sieve — the app sifts a contractor's documents against the rules and separates what is compliant from what is missing or questionable.

An officer uploads the tender requirements and the contractor's submitted documents; the system checks each requirement and returns a structured compliance report — for every requirement: Compliant, Missing, or Needs Review, each with a short justification. It is a decision-support tool: it does the tedious cross-checking and flags issues, but the human officer stays accountable and makes the final call.

One-line description: An AI assistant that reads a contractor's tender submission and tells a procurement officer, requirement by requirement, what's compliant, what's missing, and what needs a human's eyes.

2. This is a research project (important for the framing)
   Cribra is the software artefact of an undergraduate research study — a final-year BTech project in the Department of Building, Federal University of Technology, Minna: "Development of a Generative AI Agent for Automated Technical Compliance Evaluation in Nigerian Construction Procurement."

That means the site has two audiences and two doors, and the landing page must serve both:

People who want to read the research — supervisors, examiners, other researchers, and professionals — who should be able to explore the study (the problem, the approach, the methodology, and the results) without signing in.
People who want to use the system — who can sign in or sign up to try the prototype.

So the landing page should read like an applied-research lab announcing a working system: credible, evidence-led, and clearly a piece of research — not a generic SaaS marketing page. The design north star for this is antimetal.com (see Section 6).

3. Who uses it
   Procurement officers in Nigerian public procuring entities
   Members of tender / bid evaluation committees
   Researchers, supervisors, and examiners reviewing the study
   (Secondary) consultants and contractors self-checking a submission before bidding

These are professional, desk-based users reviewing documents — not casual mobile users.

4. Platform & approach
   Responsive web app, desktop-first. The core workflow (uploading and reviewing multi-page documents, reading detailed compliance tables) needs screen width. It must still render acceptably on a tablet or phone for demos, but design for desktop.
   Public vs. private: the landing page and the research pages are public; the evaluation workflow lives behind sign-in.
   Stack: React (Vite), React Router, TailwindCSS, lucide-react for icons. A component library such as shadcn/ui is welcome for speed.
   This build is a non-functional prototype. No real backend, no real AI, no real file parsing. Every screen should be driven by mock/fixture data (a local mockData.json) so it looks alive and complete. Buttons navigate; uploads show a fake file list; "Run Evaluation" plays a short processing animation and then shows a pre-built report. The goal is a convincing, clickable product we can show people.
   Deploy the static build to Vercel or Netlify so it has a shareable link.
5. Core user flow
   From the About / Landing page a visitor can go two ways:

Explore the Research → the Research page (public), then optionally sign up.
Sign In / Sign Up → into the app:
Sign in or sign up (stubbed — any input proceeds)
Dashboard → clicks New Evaluation
Step 1 – Tender Requirements: pick a preloaded requirement set or upload a tender document
Step 2 – Contractor Submission: upload the contractor's documents
Processing: short animated pipeline (ingesting → retrieving → evaluating → generating report)
Compliance Report: per-requirement results + overall score; export to PDF
Report is saved to Evaluations History

6. The landing page — modelled on antimetal.com
   We want the same research-forward, editorial structure Antimetal uses. Build the About / Landing page as a long single page with these sections, top to bottom:

Top navigation bar Cribra logo (left). Centre/left links: Research, How it works, FAQ. Right side: a text Sign In link and a solid primary Get Started button (sign up). Keep it minimal and sticky.

Hero

A small eyebrow line above the headline signalling the research, e.g. "An undergraduate research project · Department of Building, FUT Minna."
A bold, oversized one-line headline, e.g. "Tender compliance, sifted in seconds."
A one-sentence subhead (the one-line description from Section 1).
Two CTAs side by side, mirroring Antimetal's Book a demo / Explore the research:
Primary: Get Started (→ Sign Up)
Secondary: Explore the Research (→ Research page)

Credibility strip Antimetal uses a notable quote + logo here. Ours states the study's grounding and provenance, e.g. "Grounded in the Public Procurement Act 2007 and the BPP Standard Bidding Documents" with the department / supervisor attribution. Keep it understated and trustworthy.

01 · The problem Short narrative: manual technical-compliance evaluation is slow, inconsistent across evaluators, and error-prone; large tender volumes and tight timelines make it worse. (Mirrors Antimetal's "production engineering is breaking" section.)

02 · How it works Use small-caps eyebrow labels over big statements (Antimetal does THE VISION / THE WORLD MODEL / THE AUTONOMOUS LAYER). Ours:

THE APPROACH — grounding an AI agent in Nigeria's own procurement rules.
THE SYSTEM — retrieval-augmented evaluation of each requirement.
THE HUMAN — the officer stays accountable; Cribra is decision support. Include a simple diagram, in the spirit of Antimetal's Team → Agents → World Model: Tender Requirements → Cribra (RAG + GPT-4o) → Compliance Report, with the officer approving.

03 · What it does (capability cards) A row of cards, each with a small category tag (like Antimetal's Proactive / Reactive / Intelligence / Platform):

Extraction — reads requirements from tender documents.
Grounded Evaluation — checks each submission against the statutory rules (RAG).
Structured Report — per-requirement Compliant / Missing / Needs Review with justification.
Human-in-the-loop — flags uncertain items for human review.

04 · From the research Antimetal's "From the research log" — a set of cards with category, date, and read time linking to research posts. Ours links to the Research page and its parts (abstract, methodology, results, and a downloadable thesis/paper PDF). Even one or two cards here, styled this way, sells the research credibility.

05 · FAQ A clean accordion, like Antimetal's FAQ. Suggested questions:

Does Cribra replace the procurement officer? (No — it's decision support; a human approves.)
How does it know Nigerian requirements? (It's grounded in the PPA 2007 and BPP Standard Bidding Documents.)
Is tender data kept safe? (Data-isolation by design; aligned with the Nigeria Data Protection Act 2023.)
Is this production-ready? (It is a research prototype demonstrating the approach.)

Final CTA A bold restatement of the one-liner with the two CTAs again: Get Started and Explore the Research.

Footer Columns: Product, Research, About, Legal. A quiet status/provenance line in Antimetal's style, e.g. "Undergraduate research · Built in Minna, Nigeria."

7. Pages to build
   Core (build these first — they tell the whole story)
   About / Landing (public) — as fully specified in Section 6.

Research / About the Study (public) The academic home of the project, readable without signing in. Sections: title, author, supervisor, department; abstract; aim and objectives; methodology summary (Design Science + mixed methods; the RAG architecture); the system architecture diagram; results (F1-score, cosine similarity, and questionnaire findings — placeholders until available); and a Download the full study (PDF) button. Clean, editorial, easy to read.

Sign In (stubbed) — email/password + sign-in button → Dashboard. A link to Sign Up.

Sign Up (stubbed) — name, email, organisation, professional affiliation (Quantity Surveyor / Builder / Architect / Civil Engineer / Procurement Officer), password → Dashboard. A link to Sign In.

Dashboard — prominent New Evaluation button, summary stat tiles (evaluations run, average compliance rate, submissions flagged), and a short list of recent evaluations linking to their reports.

New Evaluation · Step 1 — Tender Requirements — 2-step wizard. Choose a preloaded requirement set (e.g. "BPP Works – Standard") or upload a tender document; preview the requirements that will be checked. Next → Step 2.

New Evaluation · Step 2 — Contractor Submission — drag-and-drop upload with a file list (filename, detected document-type badge, size). Run Evaluation starts the process.

Processing — transient animated multi-step indicator: Ingesting → Retrieving → Evaluating → Generating report → routes to the report.

Compliance Report (the centrepiece)

Summary header: overall compliance score + counts of Compliant / Missing / Needs Review.
Results table: one row per requirement — Requirement · Status · Evidence found · Justification. Rows expand to show full justification and the requirement checked against.
Controls: filter to "issues only," and Export to PDF.
(Optional branding: the report can be styled as the contractor's "Hallmark." Plain "Compliance Report" is fine if simpler.)

Evaluations History — searchable, sortable table of past evaluations: contractor, date, score, status; each row links to its report.
Secondary (build as static stubs)
Requirement Sets / Knowledge Base — read-only view of the requirement sets and statutory sources loaded (PPA 2007, BPP Standard Bidding Documents).

Settings / Profile — user name, organisation, sign out.

Empty / Error / 404 states — friendly placeholders.
Stretch (only if time allows)
Multi-bidder comparison — several contractor submissions for one tender shown side by side.

8. Shared components
   Public / marketing: NavBar, HeroSection, EyebrowLabel, SectionNumber (01, 02…), FeatureCard (with category tag), HowItWorksDiagram, ResearchCard / PostCard (category · date · read time), FAQAccordion, CTASection, Footer, GroundingStrip (credibility line).

App layout: AppShell (sidebar + top bar), Sidebar, TopBar (page title + user menu), Breadcrumbs.

UI primitives: Button (primary / secondary / ghost), Card, Modal, Toast, Tabs, Tooltip, SearchInput, FilterChips, EmptyState, Spinner / Skeleton, Avatar / UserMenu.

Domain-specific (these give Cribra its identity):

FileDropzone — drag-and-drop upload area
FileListItem — filename, type badge, size, remove control
DocTypeBadge — CAC, Tax Clearance, PENCOM, ITF, NSITF, Audited Accounts, Company Profile, Equipment Schedule, Key Personnel CV
Stepper — the 2-step wizard progress
ProcessingSteps — the animated evaluation pipeline
StatusBadge — Compliant / Missing / Needs Review (colour-coded)
ComplianceScore — overall score ring or bar
RequirementsTable + RequirementRow — report table with expandable rows
StatTile — dashboard metric cards
ReportHeader — report summary block
ExportButton — export report to PDF
DocumentPreview — optional; can be a placeholder panel

9. Design direction
   The tone is institutional, trustworthy, and research-forward — a credible applied-research system, styled after antimetal.com. Calm, precise, evidence-led; never flashy.

Editorial research aesthetic (from Antimetal): bold oversized display headlines; lots of whitespace; small-caps eyebrow labels over section headings; numbered sections (01, 02, 03) for a research-log feel; blog/research-style cards with category · date · read time; an understated, informative footer.
Theme / palette: two workable directions —
(A) Antimetal-style dark hero: a dark, high-contrast landing page for impact, with the in-app screens kept light for document readability. Recommended if you want to match Antimetal closely.
(B) Refined light theme throughout: white/slate base with a deep, official green accent (a subtle nod to Nigerian public-sector identity). Recommended if you want one consistent, trustworthy look. Either way, keep the app's working screens light and legible.
Status colours (used consistently everywhere): Compliant = green, Missing / non-compliant = red, Needs Review = amber.
Typography: a clean, highly readable sans-serif (e.g. Inter or the system stack); generous spacing.
Tables matter. The compliance report is the heart of the product — make tables clean, scannable, and comfortable to read, with clear row states and expandable detail.
