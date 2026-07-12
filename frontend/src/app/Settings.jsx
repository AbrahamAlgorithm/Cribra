import { useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import data from "../data/mockData.json";
import { CornerFrame, PrimaryButton, Reveal } from "../components/ui.jsx";
import { Field } from "../pages/AuthLayout.jsx";

export default function Settings() {
  const navigate = useNavigate();
  return (
    <div className="mx-auto w-full max-w-[1600px] px-5 py-10 md:px-7">
      <Reveal>
        <p className="text-eyebrow text-fg/50">Settings</p>
        <h1 className="text-subhead mt-2 text-fg" style={{ fontSize: "clamp(28px,3vw,42px)" }}>
          Profile
        </h1>

        <CornerFrame className="mt-8 flex max-w-[720px] flex-col gap-5 bg-cream/60 p-8">
          <Field label="Full name" value={data.user.name} onChange={() => {}} />
          <Field label="Organisation" value={data.user.organisation} onChange={() => {}} />
          <Field
            label="Professional affiliation"
            options={["Procurement Officer", "Quantity Surveyor", "Builder", "Architect", "Civil Engineer"]}
            value={data.user.role}
            onChange={() => {}}
          />
          <div className="mt-2 flex items-center justify-between">
            <PrimaryButton onClick={() => {}}>Save changes</PrimaryButton>
            <button
              type="button"
              onClick={() => navigate("/")}
              className="text-button inline-flex items-center gap-2 text-fg/55 transition-colors hover:text-missing"
            >
              <LogOut size={14} /> Sign out
            </button>
          </div>
        </CornerFrame>

        <p className="text-caption mt-6 text-fg/45" style={{ fontSize: 12.5 }}>
          Prototype build — changes are not persisted.
        </p>
      </Reveal>
    </div>
  );
}
