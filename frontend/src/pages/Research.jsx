import Nav from "../components/marketing/Nav.jsx";
import Footer from "../components/marketing/Footer.jsx";
import StackDiagram from "../components/marketing/StackDiagram.jsx";
import { CornerFrame, Reveal, SectionEyebrow, PrimaryButton, FrameButton } from "../components/ui.jsx";
import { Download } from "lucide-react";

const OBJECTIVES = [
  "Identify the mandatory eligibility and technical-compliance requirements applicable to works tenders under the PPA 2007 and the BPP Standard Bidding Documents.",
  "Design a generative AI agent, grounded through retrieval-augmented generation, that evaluates a contractor's submission against those requirements.",
  "Implement the agent as a working prototype with a structured, per-requirement compliance report.",
  "Evaluate the artefact's accuracy (F1-score, cosine similarity) and its acceptability to procurement professionals (questionnaire study).",
];

const RESULTS = [
  { metric: "F1-score", value: "—", note: "Classification accuracy against expert-labelled requirements." },
  { metric: "Cosine similarity", value: "—", note: "Semantic agreement between generated and expert justifications." },
  { metric: "Questionnaire (n = —)", value: "—", note: "Perceived usefulness and trust among procurement professionals." },
];

function Section({ number, label, children }) {
  return (
    <section className="mx-auto w-full max-w-[1100px] px-6 py-[56px] md:px-[60px]">
      <Reveal>
        <SectionEyebrow number={number} label={label} />
        <div className="mt-8">{children}</div>
      </Reveal>
    </section>
  );
}

export default function Research() {
  return (
    <main className="relative min-h-screen w-full">
      <Nav />

      {/* Title block */}
      <header className="mx-auto w-full max-w-[1100px] px-6 pt-[80px] pb-10 md:px-[60px] md:pt-[130px]">
        <Reveal>
          <p className="text-eyebrow text-fg/60">The study · Public research page</p>
          <h1 className="text-heading mt-5 text-fg" style={{ fontSize: "clamp(34px,4.2vw,62px)" }}>
            Development of a Generative AI Agent for Automated Technical Compliance Evaluation in
            Nigerian Construction Procurement
          </h1>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <div className="text-eyebrow text-fg/50">Author</div>
              <div className="text-credit mt-1 text-fg">Abraham Folorunso</div>
            </div>
            <div>
              <div className="text-eyebrow text-fg/50">Supervisor</div>
              <div className="text-credit mt-1 text-fg">Prof. R.A. Jimoh</div>
            </div>
            <div>
              <div className="text-eyebrow text-fg/50">Institution</div>
              <div className="text-credit mt-1 text-fg">Federal University of Technology, Minna</div>
            </div>
          </div>
          <div className="mt-10 flex flex-wrap gap-4">
            <PrimaryButton onClick={() => {}}>
              <span className="inline-flex items-center gap-2">
                <Download size={15} /> Download the full study (PDF)
              </span>
            </PrimaryButton>
            <FrameButton to="/signup">Try the prototype</FrameButton>
          </div>
        </Reveal>
      </header>

      <hr className="m-0 w-full border-0 border-t border-dashed border-[var(--color-border)]" />

      <Section number="01" label="Abstract">
        <div className="flex max-w-[76ch] flex-col gap-5">
          <p className="text-body text-fg">
            Technical-compliance evaluation of tender submissions in Nigerian public construction
            procurement is manual, slow, and inconsistent across evaluators. This study develops a
            generative AI agent that automates the evaluation: the agent reads a contractor's
            submitted documents, retrieves the governing provisions from the Public Procurement Act
            2007 and the Bureau of Public Procurement's Standard Bidding Documents, and returns a
            structured, per-requirement verdict — Compliant, Missing, or Needs Review — each with a
            written justification.
          </p>
          <p className="text-body text-fg">
            The artefact is developed under a Design Science methodology and evaluated with mixed
            methods: classification accuracy against expert-labelled submissions and a questionnaire
            study of procurement professionals. The agent is decision support — the human officer
            reviews flagged items and remains accountable for the final determination.
          </p>
        </div>
      </Section>

      <hr className="m-0 w-full border-0 border-t border-dashed border-[var(--color-border)]" />

      <Section number="02" label="Aim & objectives">
        <p className="text-body max-w-[76ch] text-fg">
          The aim is to develop and evaluate a generative AI agent for automated technical
          compliance evaluation in Nigerian construction procurement. The objectives:
        </p>
        <ol className="mt-8 flex flex-col gap-4">
          {OBJECTIVES.map((o, i) => (
            <li key={i} className="flex gap-6">
              <span className="text-eyebrow mt-1 shrink-0 text-fg/50">0{i + 1}</span>
              <span className="text-body max-w-[70ch] text-fg/85">{o}</span>
            </li>
          ))}
        </ol>
      </Section>

      <hr id="methodology" className="m-0 w-full border-0 border-t border-dashed border-[var(--color-border)]" />

      <Section number="03" label="Methodology">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-2">
          <div className="flex flex-col gap-5">
            <p className="text-body text-fg">
              The study follows a <strong>Design Science</strong> approach with mixed-methods
              evaluation. The artefact is a retrieval-augmented generation (RAG) pipeline: statutory
              sources are chunked and indexed; for each requirement, relevant provisions are
              retrieved and supplied to a large language model (GPT-4o) alongside the contractor's
              evidence; the model produces a verdict and justification, which is assembled into the
              compliance report.
            </p>
            <p className="text-body text-fg">
              Uncertainty is handled explicitly: where evidence is ambiguous or borderline, the item
              is classed <em>Needs Review</em> and routed to the human evaluator rather than
              decided by the system.
            </p>
          </div>
          <CornerFrame className="p-6">
            <div className="text-eyebrow mb-6 text-fg/50">System architecture</div>
            <StackDiagram active={1} />
          </CornerFrame>
        </div>
      </Section>

      <hr id="results" className="m-0 w-full border-0 border-t border-dashed border-[var(--color-border)]" />

      <Section number="04" label="Results">
        <p className="text-body max-w-[76ch] text-fg">
          Quantitative and questionnaire results will be published here as the evaluation
          concludes.
        </p>
        <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
          {RESULTS.map((r) => (
            <CornerFrame key={r.metric} className="flex min-h-[190px] flex-col justify-between p-6">
              <div className="text-eyebrow text-fg/55">{r.metric}</div>
              <div className="font-serif text-[56px] leading-none text-fg/85">{r.value}</div>
              <p className="text-caption text-fg/55">{r.note}</p>
            </CornerFrame>
          ))}
        </div>
      </Section>

      <Footer />
    </main>
  );
}
