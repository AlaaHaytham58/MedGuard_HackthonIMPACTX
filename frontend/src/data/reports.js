// Mock, in-memory only. No persistence, no network — matches PRODUCT.md's
// current-milestone scope. Real interaction verdicts must come from DDInter /
// openFDA once the pipeline exists; these are placeholder demo pairs.
//
// dangerPair / safePair are content templates (no id or timestamp yet) that
// both the pre-seeded history and a fresh Home submission draw from, so a
// repeated check supersedes its own history row instead of duplicating it.

export const dangerPair = {
  drugs: [
    { brand: "Marevan", ingredient: "Warfarin", source: "Egyptian brand table" },
    { brand: "Brufen", ingredient: "Ibuprofen", source: "Egyptian brand table" },
  ],
  verdict: "danger",
  verdictHeadline: "These medicines should not be taken together",
  interaction:
    "Ibuprofen can raise the blood-thinning effect of warfarin. Taking them together increases the risk of serious bleeding, including bleeding you might not notice right away.",
  management: [
    "Avoid taking these two medicines together.",
    "If you need pain relief while taking Marevan, ask your pharmacist or doctor for a safer option first.",
    "If you've already taken both, watch for unusual bruising, bleeding gums, dark stools, or bleeding that won't stop, and contact a doctor if you notice any of these.",
  ],
  alternatives: [
    {
      brand: "Brufen",
      suggestion:
        "Panadol (paracetamol) is a safer choice for pain relief while taking Marevan.",
    },
    {
      brand: "Marevan",
      suggestion:
        "Only your doctor can adjust or replace this medicine — don't stop or substitute it on your own.",
    },
  ],
};

export const safePair = {
  drugs: [
    { brand: "Panadol", ingredient: "Paracetamol", source: "Egyptian brand table" },
    { brand: "Concor", ingredient: "Bisoprolol", source: "Egyptian brand table" },
  ],
  verdict: "safe",
  verdictHeadline: "These medicines are safe to take together",
  interaction:
    "No known interaction between paracetamol and bisoprolol. They work in different ways and don't affect how the other is absorbed or works.",
  management: [
    "You can take these as prescribed.",
    "Always follow the dose your doctor or the package recommends.",
    "Don't go over the maximum daily amount of paracetamol.",
  ],
  alternatives: [
    { brand: "Panadol", suggestion: "No substitution needed for this combination." },
    { brand: "Concor", suggestion: "No substitution needed for this combination." },
  ],
};

const asprinWarfarinPair = {
  drugs: [
    { brand: "Aspocid", ingredient: "Aspirin", source: "Egyptian brand table" },
    { brand: "Marevan", ingredient: "Warfarin", source: "Egyptian brand table" },
  ],
  verdict: "danger",
  verdictHeadline: "These medicines should not be taken together",
  interaction:
    "Aspirin and warfarin both reduce your blood's ability to clot. Taking them together significantly increases the risk of serious bleeding.",
  management: [
    "This combination should only be used under close medical supervision.",
    "Don't start or stop either medicine without talking to your doctor first.",
  ],
  alternatives: [
    {
      brand: "Aspocid",
      suggestion: "Panadol (paracetamol) for general pain relief, if your doctor approves.",
    },
    { brand: "Marevan", suggestion: "Only your doctor can adjust this medicine." },
  ],
};

// The box combinations the current mock data can actually answer. Anything
// else must reach the honest "not enough data" path rather than borrowing
// another pair's verdict (PRODUCT.md: fail visibly, never silently).
const answerablePairs = [
  { boxes: ["brufen", "marevan"], report: dangerPair },
  { boxes: ["concor", "panadol"], report: safePair },
];

export function resolveReport(selectedIds) {
  const key = selectedIds.slice().sort().join("+");
  const match = answerablePairs.find((pair) => pair.boxes.join("+") === key);
  return match ? match.report : null;
}

// The 2-3 mock previous searches the history panel is pre-seeded with.
export const initialHistory = [
  { id: "h1", checkedLabel: "2 hours ago", ...dangerPair },
  { id: "h2", checkedLabel: "Yesterday", ...safePair },
  { id: "h3", checkedLabel: "3 days ago", ...asprinWarfarinPair },
];
