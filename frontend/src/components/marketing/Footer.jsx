import { CornerFrame } from "../ui.jsx";

const CARDS = [
  {
    heading: "Product",
    primary: "Cribra",
    secondary: "Agentic AI for Technical Compliance Evaluation",
  },
  {
    heading: "Researcher",
    primary: "Abraham Folorunso",
    secondary: "B.Tech. Building",
    href: "https://www.linkedin.com/in/abrahamfolorunso/",
  },
  {
    heading: "Supervisor",
    primary: "Professor R. A. Jimoh",
    secondary: "Project Supervisor",
  },
  {
    heading: "Institution",
    primary: "Department of Building",
    secondary: "Federal University of Technology Minna",
  },
];

export default function Footer() {
  return (
    <footer className="w-full px-4 pt-4 pb-6 md:px-[30px] md:pt-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {CARDS.map((card) => (
          <CornerFrame key={card.heading} className="flex min-h-[220px] flex-col p-5">
            <div className="text-eyebrow text-fg/50">{card.heading}</div>
            <div className="mt-6">
              {card.href ? (
                <a
                  href={card.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-pullquote text-fg/85 underline decoration-fg/30 underline-offset-4 transition-colors hover:text-fg hover:decoration-fg/70"
                  style={{ fontSize: "clamp(17px,1.4vw,22px)" }}
                >
                  {card.primary}
                </a>
              ) : (
                <div
                  className="text-pullquote text-fg/85"
                  style={{ fontSize: "clamp(17px,1.4vw,22px)" }}
                >
                  {card.primary}
                </div>
              )}
              <p className="text-caption mt-2 text-fg/55" style={{ fontSize: 13 }}>
                {card.secondary}
              </p>
            </div>
          </CornerFrame>
        ))}

        <CornerFrame className="col-span-2 flex min-h-[220px] flex-col justify-between p-5 md:col-span-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-eyebrow inline-flex items-center gap-2 bg-fg px-2 py-1 text-cream">
              <span className="h-[6px] w-[6px] rounded-full bg-[#5fbf7f]" />
              Research prototype
            </span>
          </div>
          <div>
            <p className="text-eyebrow text-fg/50">
              Undergraduate Research. Grounded in the Public Procurement Act 2007 &amp; BPP
              Standard Bidding Documents.
            </p>
            <img src="/cribra-mark.svg" alt="Cribra" className="mt-3 ml-auto w-[44px] opacity-90" />
          </div>
        </CornerFrame>
      </div>
    </footer>
  );
}
