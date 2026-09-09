import { createContext, useCallback, useContext, useMemo, useState } from "react";

const HistoryContext = createContext(null);

function pairKey(report) {
  return report.medications
    .map((medication) => medication.ingredient || medication.inputName)
    .slice()
    .sort()
    .join("+");
}

// Session-only, in-memory — React state, never localStorage. Resets on reload,
// matching PRODUCT.md's current-milestone scope (no accounts, no persistence).
// Starts empty: seeding it with invented past checks would be fabricated data.
export function HistoryProvider({ children }) {
  const [history, setHistory] = useState([]);

  const recordCheck = useCallback((report) => {
    const key = pairKey(report);

    setHistory((previous) => {
      const withoutSameCombination = previous.filter((entry) => pairKey(entry) !== key);
      return [report, ...withoutSameCombination].slice(0, 12);
    });

    return report.id;
  }, []);

  const value = useMemo(() => ({ history, recordCheck }), [history, recordCheck]);

  return <HistoryContext.Provider value={value}>{children}</HistoryContext.Provider>;
}

export function useHistory() {
  const context = useContext(HistoryContext);
  if (!context) {
    throw new Error("useHistory must be used within a HistoryProvider");
  }
  return context;
}
