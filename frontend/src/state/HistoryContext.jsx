import { createContext, useCallback, useContext, useState } from "react";
import { initialHistory } from "../data/reports.js";

const HistoryContext = createContext(null);

function pairKey(report) {
  return report.drugs
    .map((drug) => drug.brand)
    .slice()
    .sort()
    .join("+");
}

// Session-only, in-memory history — React state, never localStorage. Resets
// on reload, matches PRODUCT.md's current-milestone scope (no accounts, no
// persistence).
export function HistoryProvider({ children }) {
  const [history, setHistory] = useState(initialHistory);

  const recordCheck = useCallback((template) => {
    const key = pairKey(template);
    let resultId = null;

    setHistory((prev) => {
      const existingIndex = prev.findIndex((entry) => pairKey(entry) === key);

      if (existingIndex !== -1) {
        const existing = prev[existingIndex];
        resultId = existing.id;
        const superseded = { ...existing, checkedLabel: "Just now" };
        return [superseded, ...prev.slice(0, existingIndex), ...prev.slice(existingIndex + 1)];
      }

      const id = `check-${Date.now()}`;
      resultId = id;
      return [{ ...template, id, checkedLabel: "Just now" }, ...prev];
    });

    return resultId;
  }, []);

  return (
    <HistoryContext.Provider value={{ history, recordCheck }}>
      {children}
    </HistoryContext.Provider>
  );
}

export function useHistory() {
  const ctx = useContext(HistoryContext);
  if (!ctx) {
    throw new Error("useHistory must be used within a HistoryProvider");
  }
  return ctx;
}
