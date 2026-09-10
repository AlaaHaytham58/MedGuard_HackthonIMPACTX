import { Routes, Route } from "react-router-dom";
import { HistoryProvider } from "./state/HistoryContext.jsx";
import { LanguageProvider } from "./state/LanguageContext.jsx";
import Home from "./pages/Home.jsx";
import Results from "./pages/Results.jsx";

export default function App() {
  return (
    <LanguageProvider>
      <HistoryProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/results" element={<Results />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </HistoryProvider>
    </LanguageProvider>
  );
}
