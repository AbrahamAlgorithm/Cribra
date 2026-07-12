import { Link } from "react-router-dom";
import { CornerFrame, CribraMark } from "../components/ui.jsx";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <CornerFrame className="flex max-w-[440px] flex-col items-center gap-6 bg-cream/60 p-12 text-center">
        <CribraMark className="h-6 w-auto" />
        <h1 className="text-subhead text-fg">Nothing sifted here.</h1>
        <p className="text-caption text-fg/60">
          The page you're looking for doesn't exist — it may have fallen through the sieve.
        </p>
        <Link
          to="/"
          className="inline-flex items-center justify-center rounded-full bg-fg px-6 py-3 text-button text-cream transition-colors hover:bg-fg/85"
        >
          Back to Cribra
        </Link>
      </CornerFrame>
    </main>
  );
}
