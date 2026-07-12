import { useNavigate, Link } from "react-router-dom";
import AuthLayout, { Field } from "./AuthLayout.jsx";
import { PrimaryButton } from "../components/ui.jsx";

export default function SignIn() {
  const navigate = useNavigate();
  return (
    <AuthLayout
      title="Sign in"
      subtitle="Access the evaluation workspace. This prototype accepts any credentials."
      footer={
        <>
          New here?{" "}
          <Link to="/signup" className="text-fg underline underline-offset-4">
            Create an account
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
        <Field label="Email" type="email" placeholder="officer@ministry.gov.ng" />
        <Field label="Password" type="password" placeholder="••••••••" />
        <PrimaryButton type="submit" className="mt-2 w-full">
          Sign In
        </PrimaryButton>
      </form>
    </AuthLayout>
  );
}
