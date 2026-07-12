import { useState } from "react";

const ITEMS = [
  {
    q: "Does Cribra replace the procurement officer?",
    a: [
      "No. Cribra supports procurement officers, it doesn't replace them. It performs the repetitive review of contractor submissions against tender requirements and provides a justification for every finding. The evaluation committee reviews flagged items, and the procurement officer retains responsibility for the final decision.",
      "Items the system cannot confidently determine are marked as Needs Review rather than decided automatically.",
    ],
  },
  {
    q: "How does it know Nigerian requirements?",
    a: [
      "Cribra is grounded in Nigeria's procurement rules, including the Public Procurement Act 2007 and the Bureau of Public Procurement's Standard Bidding Documents. It retrieves the relevant requirements before evaluating every submission.",
      "Every finding is linked to the requirement it was assessed against, making the evaluation transparent and traceable.",
    ],
  },
  {
    q: "Is tender data kept safe?",
    a: [
      "Yes. Each procuring entity's data is isolated, and the system is designed in line with the Nigeria Data Protection Act 2023. Documents are used only for the evaluation they were submitted for.",
    ],
  },
  {
    q: "Is this production-ready?",
    a: [
      "Cribra is currently a research prototype developed as part of an undergraduate study. It demonstrates the feasibility of grounded AI for technical compliance evaluation and provides a foundation for future deployment and validation in live procurement environments.",
    ],
  },
];

export default function FAQ() {
  const [open, setOpen] = useState(0);
  return (
    <div className="border-t border-fg/10">
      {ITEMS.map((item, i) => {
        const isOpen = open === i;
        return (
          <div key={item.q} className={`border-b border-fg/10 ${isOpen ? "bg-fg/[0.03]" : ""}`}>
            <button
              type="button"
              onClick={() => setOpen(isOpen ? -1 : i)}
              aria-expanded={isOpen}
              className="flex w-full cursor-pointer items-center justify-between gap-6 px-6 py-6 text-left md:px-8"
            >
              <span className="text-pullquote text-fg" style={{ fontSize: "clamp(19px,1.7vw,26px)" }}>
                {item.q}
              </span>
              <span className="relative h-4 w-4 shrink-0" aria-hidden="true">
                <span className="absolute left-0 top-1/2 h-px w-4 -translate-y-1/2 bg-fg" />
                <span
                  className="absolute left-1/2 top-0 h-4 w-px -translate-x-1/2 bg-fg transition-transform duration-300"
                  style={{ transform: isOpen ? "scaleY(0)" : "scaleY(1)" }}
                />
              </span>
            </button>
            <div
              className="grid transition-[grid-template-rows] duration-400"
              style={{
                gridTemplateRows: isOpen ? "1fr" : "0fr",
                transitionTimingFunction: "cubic-bezier(0.22,1,0.36,1)",
              }}
            >
              <div className="overflow-hidden">
                <div className="flex flex-col gap-4 px-6 pb-7 md:px-8">
                  {item.a.map((p) => (
                    <p key={p.slice(0, 24)} className="max-w-[70ch] text-caption text-fg/75" style={{ fontSize: 16 }}>
                      {p}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
