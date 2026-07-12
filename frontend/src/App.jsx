import { Routes, Route, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Landing from "./pages/Landing.jsx";
import Research from "./pages/Research.jsx";
import SignIn from "./pages/SignIn.jsx";
import SignUp from "./pages/SignUp.jsx";
import AppShell from "./app/AppShell.jsx";
import Dashboard from "./app/Dashboard.jsx";
import NewEvaluation from "./app/NewEvaluation.jsx";
import Processing from "./app/Processing.jsx";
import Report from "./app/Report.jsx";
import History from "./app/History.jsx";
import KnowledgeBase from "./app/KnowledgeBase.jsx";
import Settings from "./app/Settings.jsx";
import NotFound from "./pages/NotFound.jsx";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/research" element={<Research />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="evaluations/new" element={<NewEvaluation />} />
          <Route path="evaluations/processing" element={<Processing />} />
          <Route path="evaluations/:id" element={<Report />} />
          <Route path="evaluations" element={<History />} />
          <Route path="knowledge-base" element={<KnowledgeBase />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
