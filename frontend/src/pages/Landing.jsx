import { useEffect, useRef, useState } from "react";
import Nav from "../components/marketing/Nav.jsx";
import Footer from "../components/marketing/Footer.jsx";
import NetworkOrbitCanvas from "../components/marketing/NetworkOrbitCanvas.jsx";
import ProblemGraph from "../components/marketing/ProblemGraph.jsx";
import StackFlow from "../components/marketing/StackFlow.jsx";
import FAQ from "../components/marketing/FAQ.jsx";
import { CornerFrame, Reveal, SectionEyebrow, PrimaryButton, FrameButton } from "../components/ui.jsx";
import { Link } from "react-router-dom";

const DashedRule = () => (
  <hr className="m-0 w-full border-0 border-t border-dashed border-fg/12" />
);

/* ---------------- Hero ---------------- */
function Hero() {
  return (
    <section id="header" aria-label="Hero" className="relative isolate w-full overflow-hidden pt-[56px] md:pt-[100px]">
      {/* desktop: the rotating network fills the right-hand column */}
      <NetworkOrbitCanvas className="z-0 hidden md:block" />
      <div className="pointer-events-none relative z-10 mx-auto flex w-full max-w-[1512px] flex-col gap-1 px-6 pt-20 pb-0 md:gap-10 md:px-[120px] md:pt-[170px] md:pb-[190px]">
        <div className="flex max-w-[760px] flex-1 flex-col">
          <Reveal>
            {/* <p className="text-eyebrow text-fg/60">
              An undergraduate research project · Department of Building, FUTMinna
            </p> */}
          </Reveal>
          <Reveal delay={80}>
            <h1 className="text-heading mt-5 text-fg">
              Intelligence Behind Every Tender.
            </h1>
          </Reveal>
          <Reveal delay={160}>
            <h2 className="text-body mt-6 max-w-[600px] text-fg/70 md:mt-8">
              Cribra is the intelligence behind every tender. It evaluates contractor submissions 
              against tender requirements and tells procurement officers,
              what's compliant, what's missing, and what needs human review.
            </h2>
          </Reveal>
          <Reveal delay={240}>
            <div className="pointer-events-auto mt-10 flex flex-wrap items-center gap-4 md:mt-16">
              <PrimaryButton to="/signup">Get Started</PrimaryButton>
              <FrameButton to="/research">Explore the Research</FrameButton>
            </div>
          </Reveal>
        </div>
        {/* mobile: the network gets its own contained block between the CTAs
            and the section divider, like Antimetal's */}
        <div className="relative -mx-6 -mt-4 h-[310px] md:hidden" aria-hidden="true">
          <NetworkOrbitCanvas />
        </div>
      </div>
    </section>
  );
}

/* ---------------- Credibility strip ---------------- */
function Credibility() {
  return (
    <section aria-label="Grounding" className="relative w-full">
      <div className="mx-auto grid w-full max-w-[1512px] grid-cols-1 items-center gap-10 px-6 py-[70px] md:grid-cols-2 md:gap-12 md:px-[120px]">
        <Reveal>
          <CornerFrame className="flex aspect-[525/300] w-full flex-col justify-between bg-cream/50 p-8">
            <span className="text-eyebrow text-fg/50">Statutory grounding</span>
            <div className="flex flex-col gap-3">
              <div className="text-pullquote text-fg" style={{ fontSize: "clamp(20px,1.9vw,30px)" }}>
                Public Procurement Act, 2007
              </div>
              <div className="h-px w-full bg-fg/10" />
              <div className="text-pullquote text-fg" style={{ fontSize: "clamp(20px,1.9vw,30px)" }}>
                BPP Standard Bidding Documents
              </div>
            </div>
            <span className="text-eyebrow text-fg/50">Federal Republic of Nigeria</span>
          </CornerFrame>
        </Reveal>
        <Reveal delay={120}>
          <div className="flex flex-col gap-6">
            <blockquote className="text-pullquote relative text-fg">
              <span aria-hidden="true" className="absolute right-full top-0 pr-[0.15em]">
                “
              </span>
              Every finding Cribra makes is checked against Nigeria's own procurement rules — the
              Public Procurement Act 2007 and the BPP Standard Bidding Documents — and cites the
              clause it evaluated.”
            </blockquote>
            <figcaption className="text-credit">
              <div className="text-fg">Development of a Generative AI Agent for Automated Technical Compliance Evaluation</div>
              <div className="text-fg/60">
                B.Tech research · Department of Building, Federal University of Technology, Minna
              </div>
            </figcaption>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ---------------- 01 · The problem ---------------- */
function Problem() {
  return (
    <section id="problem" aria-label="The problem" className="w-full">
      <div className="mx-auto w-full max-w-[1512px] px-6 pt-[80px] md:px-[120px]">
        <Reveal>
          <SectionEyebrow number="01" label="The problem" />
        </Reveal>
      </div>
      <div className="mx-auto grid w-full max-w-[1512px] grid-cols-1 items-start gap-10 px-6 py-[50px] md:grid-cols-2 md:gap-12 md:px-[120px]">
        <ProblemGraph />
        <Reveal delay={100}>
          <div className="flex flex-col gap-5">
            <p className="text-body" style={{ fontSize: "clamp(20px, 1.8vw, 26px)", lineHeight: 1.2, color: "rgb(26, 22, 20)" }}>
            <CornerFrame
              as="span"
              className="float-left mr-3 flex h-[2lh] items-center justify-center px-2"
            >
              <span className="font-serif text-[50px] leading-none text-accent">M</span>
            </CornerFrame>
            anual technical compliance evaluation doesn't scale. Every works tender arrives with dozens of certificates, financial records, and statutory documents that must be verified against procurement requirements.
          </p>

          <p className="text-body" style={{ fontSize: "clamp(20px, 1.8vw, 26px)", lineHeight: 1.2, color: "rgb(26, 22, 20)" }}>
            The result is slower evaluations, inconsistent decisions, and costly oversights. Compliant bidders may be rejected, while non-compliant submissions can slip through unnoticed.
          </p>

          <p className="text-body" style={{ fontSize: "clamp(20px, 1.8vw, 26px)", lineHeight: 1.2, color: "rgb(26, 22, 20)" }}>
            Cribra changes the process. It understands tender requirements, evaluates contractor submissions, and produces transparent compliance reports so procurement officers can focus on informed decisions rather than manual verification.
          </p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ---------------- 02 · How it works (sticky scroll) ---------------- */
const HOW_CARDS = [
  {
    eyebrow: "THE APPROACH",
    title: "Grounded in Nigeria's\nown rules.",
    body: "Cribra doesn't guess at compliance. Every evaluation is grounded in the Public Procurement Act 2007 and BPP Standard Bidding Documents, with findings traceable to their source.",
  },
  {
    eyebrow: "THE SYSTEM",
    title: "Evidence-based \nevaluation.",
    body: "For every requirement, Cribra compares contractor evidence against the relevant procurement rules and returns a clear, explainable compliance finding.",
  },
  {
    eyebrow: "THE HUMAN",
    title: "The officer stays\naccountable.",
    body: "Cribra supports decisions, it doesn't replace them. Uncertain findings are flagged for review while procurement officers retain final authority.",
  },
];

function HowItWorks() {
  const wrapRef = useRef(null);
  const [active, setActive] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let raf = 0;
    const measure = () => {
      raf = 0;
      const el = wrapRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const total = rect.height - window.innerHeight;
      const p = Math.min(1, Math.max(0, -rect.top / Math.max(total, 1)));
      setProgress(p);
      // switch stages a beat before each card locks in, so the diagram is
      // already animating as the card arrives
      setActive(p < 0.28 ? 0 : p < 0.62 ? 1 : 2);
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(measure);
    };
    measure();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  return (
    <section id="how-it-works" aria-label="How it works" className="w-full">
      <div className="mx-auto w-full max-w-[1512px] px-6 py-[80px] md:px-[120px]">
        <Reveal>
          <div className="flex w-full flex-col gap-6">
            <SectionEyebrow number="02" label="How it works" />
            <div className="grid grid-cols-1 items-start gap-6 md:grid-cols-2 md:gap-12">
              <h2 className="text-subhead text-fg">A sieve between the rules and the paperwork</h2>
              <p className="text-body" style={{ fontSize: "clamp(20px, 1.8vw, 26px)", lineHeight: 1.2, color: "rgb(26, 22, 20)" }}>
                Cribra sits between the rules and the paperwork, keeping procurement officers in control.
              </p>
            </div>
          </div>
        </Reveal>
      </div>

      <div ref={wrapRef} className="relative w-full">
        <div className="mx-auto grid w-full max-w-[1512px] grid-cols-1 gap-8 px-6 md:px-[120px] lg:grid-cols-[440px_minmax(0,1fr)] lg:gap-16">
          {/* left: one sticky card slot per viewport-height segment */}
          <div className="flex flex-col gap-16 pb-16">
            {HOW_CARDS.map((card, i) => (
              <div key={card.eyebrow} className="lg:h-screen">
                <div className="lg:sticky lg:top-[8rem]">
                  <CornerFrame
                    className={`flex flex-col gap-3 p-7 transition-colors duration-300 md:p-8 ${
                      active === i ? "bg-fg" : ""
                    }`}
                  >
                    <span className={`text-eyebrow ${active === i ? "text-cream/60" : "text-fg/60"}`}>
                      {card.eyebrow}
                    </span>
                    <h3
                      className={`text-pullquote whitespace-pre-line transition-colors duration-300 ${
                        active === i ? "text-cream" : "text-fg"
                      }`}
                    >
                      {card.title}
                    </h3>
                    <p
                      className={`mt-3 max-w-[480px] text-caption transition-colors duration-300 ${
                        active === i ? "text-cream/60" : "text-fg/60"
                      }`}
                    >
                      {card.body}
                    </p>
                  </CornerFrame>
                </div>
              </div>
            ))}
          </div>

          {/* right: sticky 3D diagram, builds up stage by stage */}
          <div className="relative hidden lg:block">
            <div className="sticky top-0 flex h-screen items-center overflow-hidden">
              <StackFlow stage={active} progress={progress} />
            </div>
          </div>
          <div className="lg:hidden">
            <StackFlow stage={2} progress={0.5} tilt={false} />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ---------------- 03 · What it does ---------------- */
const CAPABILITIES = [
  {
    tag: "EXTRACTION",
    title: "Tender Intelligence",
    body: "Identifies mandatory eligibility, technical, and statutory requirements.",
  },
  {
    tag: "INTELLIGENCE",
    title: "Grounded Evaluation",
    body: "Checks every submission against the statutory rules.",
  },
  {
    tag: "REPORTING",
    title: "Structured Report",
    body: "Generates clear compliance findings with supporting evidence.",
  },
  {
    tag: "OVERSIGHT",
    title: "Human-in-the-loop",
    body: "Flags uncertain findings for review while officers retain final authority.",
  },
];

function DarkBurst() {
  const lines = Array.from({ length: 36 }, (_, i) => {
    const a = (i / 36) * Math.PI * 2;
    return { x2: 200 + Math.cos(a) * 190, y2: 200 + Math.sin(a) * 190 };
  });
  const dots = Array.from({ length: 60 }, (_, i) => {
    const a = (i * 137.5 * Math.PI) / 180;
    const r = 24 + (i / 60) * 168;
    return { cx: 200 + Math.cos(a) * r, cy: 200 + Math.sin(a) * r, r: 1 + ((i * 7) % 10) / 4 };
  });
  return (
    <div className="relative h-full min-h-[420px] w-full overflow-hidden bg-[#161311]">
      <svg viewBox="0 0 400 400" className="absolute inset-0 h-full w-full" aria-hidden="true">
        {lines.map((l, i) => (
          <line key={i} x1="200" y1="200" x2={l.x2} y2={l.y2} stroke="rgba(242,239,231,0.10)" strokeWidth="0.5" />
        ))}
        {dots.map((d, i) => (
          <circle key={i} cx={d.cx} cy={d.cy} r={d.r} fill={i % 9 === 0 ? "#5fbf7f" : "rgba(242,239,231,0.6)"}>
            <animate
              attributeName="opacity"
              values="0.25;1;0.25"
              dur={`${2.4 + (i % 5)}s`}
              begin={`${(i % 10) * 0.3}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}
      </svg>
    </div>
  );
}

function Capabilities() {
  return (
    <section id="capabilities" aria-label="What it does" className="w-full">
      <div className="mx-auto w-full max-w-[1512px] px-6 py-[80px] md:px-[120px]">
        <Reveal>
          <div className="flex w-full flex-col gap-6">
            <SectionEyebrow number="03" label="What it does" />
            <div className="grid grid-cols-1 items-start gap-6 md:grid-cols-2 md:gap-12">
              <h2 className="text-subhead text-fg">
                One agent.
                <br />
                Every tender requirement.
              </h2>
              <p className="text-body" style={{ fontSize: "clamp(20px, 1.8vw, 26px)", lineHeight: 1.2, color: "rgb(26, 22, 20)" }}>
                Every step is traceable, evidence-backed, and designed to support 
                confident procurement decisions.
              </p>
            </div>
          </div>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-8 lg:grid-cols-2">
          <div className="flex flex-col gap-4">
            {CAPABILITIES.map((c, i) => (
              <Reveal key={c.tag} delay={i * 70}>
                <CornerFrame className="flex flex-col gap-4 p-7 md:p-9">
                  <span className="text-eyebrow text-fg/55">{c.tag}</span>
                  <h3 className="text-subhead text-fg" style={{ fontSize: "clamp(26px,2.4vw,38px)" }}>
                    {c.title}
                  </h3>
                  <p className="text-caption max-w-[520px] text-fg/65">{c.body}</p>
                </CornerFrame>
              </Reveal>
            ))}
          </div>
          <Reveal delay={140}>
            <DarkBurst />
          </Reveal>
        </div>
      </div>
    </section>
  );
}

/* ---------------- 04 · From the research ---------------- */
function BlueprintArt({ variant }) {
  return (
    <svg viewBox="0 0 440 200" className="h-auto w-full bg-paper" aria-hidden="true">
      <g stroke="#3B5BA5" strokeWidth="0.8" fill="none" opacity="0.85">
        {variant === 0 && (
          <>
            {Array.from({ length: 12 }, (_, i) => (
              <line key={i} x1={20 + i * 12} y1="150" x2={20 + i * 12} y2="185" />
            ))}
            <path d="M20 150 H420 M20 185 H420" />
            <path d="M120 150 L200 40 L280 150" />
            <path d="M150 150 L200 70 L250 150" />
            <circle cx="340" cy="90" r="38" />
            <circle cx="340" cy="90" r="24" />
          </>
        )}
        {variant === 1 && (
          <>
            <path d="M20 100 H160 C 230 100 230 40 300 40 H420 M20 100 H160 C 230 100 230 160 300 160 H420" />
            {Array.from({ length: 14 }, (_, i) => (
              <line key={i} x1={30 + i * 28} y1="92" x2={30 + i * 28} y2="108" />
            ))}
            <rect x="330" y="26" width="40" height="24" />
            <rect x="330" y="148" width="40" height="24" />
          </>
        )}
        {variant === 2 && (
          <>
            {Array.from({ length: 6 }, (_, i) => (
              <rect key={i} x={30 + i * 66} y={30 + (i % 3) * 44} width="46" height="26" rx="4" />
            ))}
            <path d="M76 43 H96 M162 87 H182 M228 131 H248 M294 43 H314" markerEnd="none" />
            <path d="M20 170 H420" strokeDasharray="4 4" />
          </>
        )}
      </g>
    </svg>
  );
}

const POSTS = [
  {
    category: "RESEARCH",
    date: "05/12/2026",
    title: "Abstract & aim: automating technical compliance without removing the human",
    excerpt: "Why compliance evaluation is the right first task for a grounded AI agent in Nigerian procurement.",
    author: "The Study",
    read: "6 MIN",
    to: "/research",
  },
  {
    category: "METHODOLOGY",
    date: "05/12/2026",
    title: "Design Science + RAG: how the agent is built and evaluated",
    excerpt: "A retrieval-augmented pipeline over the PPA 2007 and BPP standard bidding documents, measured with F1 and cosine similarity.",
    author: "The Study",
    read: "8 MIN",
    to: "/research#methodology",
  },
  {
    category: "RESULTS",
    date: "Forthcoming",
    title: "Findings: accuracy, agreement with evaluators, and questionnaire results",
    excerpt: "Quantitative results and practitioner feedback — published as the study concludes.",
    author: "The Study",
    read: "5 MIN",
    to: "/research#results",
  },
];

function ResearchLog() {
  return (
    <section id="research-log" aria-label="From the research" className="w-full">
      <div className="mx-auto w-full max-w-[1512px] px-6 py-[80px] md:px-[120px]">
        <Reveal>
          <div className="flex flex-col gap-6">
            <SectionEyebrow number="04" label="From the research" />
            <div className="flex flex-wrap items-end justify-between gap-6">
              <h2 className="text-subhead text-fg">From the study.</h2>
              <FrameButton to="/research" className="!px-[18px] !py-[9px]">
                View All
              </FrameButton>
            </div>
          </div>
        </Reveal>
        <div className="mt-12 grid grid-cols-1 gap-3 md:grid-cols-3 md:gap-4">
          {POSTS.map((p, i) => (
            <Reveal key={p.title} delay={i * 90} className="bg-bg">
              <Link to={p.to} className="group block h-full bg-bg transition-colors hover:bg-cream/50">
                <BlueprintArt variant={i} />
                <div className="flex flex-col gap-4 border border-dashed border-fg/20 p-6">
                  <div className="flex items-center gap-6">
                    <span className="text-eyebrow text-fg/55">{p.category}</span>
                    <span aria-hidden="true" className="h-[2px] w-[2px] rounded-full bg-fg/20" />
                    <span className="text-eyebrow text-fg/55">{p.date}</span>
                  </div>
                  <h3 className="text-pullquote text-fg" style={{ fontSize: "clamp(19px,1.6vw,25px)" }}>
                    {p.title}
                  </h3>
                  <p className="text-caption text-fg/60">{p.excerpt}</p>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-credit text-fg/80">{p.author}</span>
                    <span className="text-eyebrow bg-fg/8 px-2 py-1 text-fg/55">{p.read}</span>
                  </div>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------------- 05 · FAQ ---------------- */
function FAQSection() {
  return (
    <section id="faq" aria-label="FAQ" className="w-full">
      <div className="mx-auto w-full max-w-[1512px] px-6 py-[80px] md:px-[120px]">
        <Reveal>
          <div className="flex flex-col gap-6">
            <SectionEyebrow number="05" label="FAQ" />
            <div className="grid grid-cols-1 items-start gap-6 md:grid-cols-2 md:gap-12">
              <h2 className="text-subhead text-fg">Evaluating tenders with an agent</h2>
              <p className="text-body" style={{ fontSize: "clamp(20px, 1.8vw, 26px)", lineHeight: 1.2, color: "rgb(26, 22, 20)" }}>
                Questions procurement officers and evaluation committees ask before trusting Cribra.
              </p>
            </div>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <div className="mt-12">
            <FAQ />
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ---------------- Final CTA ---------------- */
function FinalCTA() {
  return (
    <section aria-label="Get started" className="relative w-full overflow-hidden bg-[#12100e]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 80% at 30% 20%, rgba(14,90,52,0.35), transparent 60%), radial-gradient(50% 70% at 75% 80%, rgba(183,121,31,0.18), transparent 60%)",
        }}
      />
      <div className="relative mx-auto flex min-h-[560px] w-full max-w-[1512px] flex-col items-center justify-center gap-8 px-6 py-[120px] text-center md:px-[120px]">
        <Reveal>
          <h2 className="text-heading text-cream" style={{ fontSize: "clamp(36px,4.6vw,68px)" }}>
            Tender compliance, <em className="italic">sifted</em>.
          </h2>
        </Reveal>
        <Reveal delay={100}>
          <p className="text-body max-w-[520px] text-cream/75" style={{ fontSize: "clamp(18px, 1.6vw, 24px)", lineHeight: 1.5 }}>
            Built from research. Designed for procurement. 
            Explore the prototype or read the study behind it.
          </p>
        </Reveal>
        <Reveal delay={180}>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/signup"
              className="inline-flex items-center justify-center rounded-full bg-cream px-[24.5px] py-[12.5px] text-button text-fg transition-colors hover:bg-white"
            >
              Get Started
            </Link>
            <Link
              to="/research"
              className="inline-flex items-center justify-center rounded-full border border-dashed border-cream/40 px-[24.5px] py-[12.5px] text-button text-cream transition-colors hover:bg-cream/10"
            >
              Read the research
            </Link>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

export default function Landing() {
  return (
    <main className="relative min-h-screen w-full">
      <Nav />
      <Hero />
      <DashedRule />
      <Credibility />
      <DashedRule />
      <Problem />
      <DashedRule />
      <HowItWorks />
      <DashedRule />
      <Capabilities />
      <DashedRule />
      <ResearchLog />
      <DashedRule />
      <FAQSection />
      <FinalCTA />
      <Footer />
    </main>
  );
}
