import { useNavigate, Link } from "react-router-dom";
import AuthLayout, { Field } from "./AuthLayout.jsx";
import { PrimaryButton } from "../components/ui.jsx";

export default function SignUp() {
  const navigate = useNavigate();
  return (
    <AuthLayout
      title="Get started"
      subtitle="Create an account to try the Cribra prototype."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/signin" className="text-fg underline underline-offset-4">
            Sign in
          </Link>
        </>
      }
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          navigate("/app");
        }}
        className="flex flex-col gap-5"
      >
        <Field label="Full name" placeholder="Aisha Bello" />
        <Field label="Email" type="email" placeholder="you@organisation.gov.ng" />
        <Field label="Organisation" placeholder="Niger State Ministry of Works" />
        <Field
          label="Professional affiliation"
          options={[
            "Procurement Officer",
            "Quantity Surveyor",
            "Builder",
            "Architect",
            "Civil Engineer",
          ]}
        />
        <Field label="Password" type="password" placeholder="••••••••" />
        <PrimaryButton type="submit" className="mt-2 w-full">
          Create Account
        </PrimaryButton>
      </form>
    </AuthLayout>
  );
}
