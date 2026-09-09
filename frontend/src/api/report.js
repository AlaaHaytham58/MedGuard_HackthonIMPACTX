// Turns the backend's two response shapes (/pipeline and /check) into the single
// report object the Results page renders.
//
// The verdict deliberately has no "safe" state. The catalogue itself says "no
// record found does not establish that a drug combination is medically safe",
// so claiming safety from an empty result would be the one failure that could
// actually hurt someone. Absence of a record is reported as absence of a record.

export const VERDICT = {
  DANGER: "danger",
  CAUTION: "caution",
  NO_RECORD: "no-record",
  UNKNOWN: "unknown",
};

const HEADLINES = {
  [VERDICT.DANGER]: "These medicines should not be taken together",
  [VERDICT.CAUTION]: "Take care with this combination",
  [VERDICT.NO_RECORD]: "No interaction found on record",
  [VERDICT.UNKNOWN]: "Not enough data to confirm",
};

const SUMMARIES = {
  [VERDICT.DANGER]:
    "A verified medical database flagged a serious problem with this combination. Speak to a pharmacist or doctor before taking these together.",
  [VERDICT.CAUTION]:
    "A verified medical database has a record for this combination. It is not necessarily dangerous, but it is worth asking your pharmacist about.",
  [VERDICT.NO_RECORD]:
    "The database holds no interaction record for these medicines. That is not the same as confirming they are safe together — ask your pharmacist if you are unsure.",
  [VERDICT.UNKNOWN]:
    "We could not confirm this combination against the medical database. Ask your pharmacist before taking these together.",
};

// Mirrors the catalogue's own ranking. Needed because the flattened /pipeline
// report sends the severity label without the numeric rank, and a "Major"
// interaction arriving as rank 0 would be shown as a mild caution.
const SEVERITY_RANK = { major: 3, moderate: 2, minor: 1, unknown: 0 };

function rankOf(pair, severity) {
  if (typeof pair.severity_rank === "number") return pair.severity_rank;
  return SEVERITY_RANK[(severity ?? "").toLowerCase()] ?? 0;
}

/** A pair endpoint may name a drug as a plain string or as a full catalogue record. */
function drugName(value) {
  if (typeof value === "string") return value;
  return value?.canonical_name ?? "";
}

/** Catalogue name -> the wording on the patient's own box ("Acetaminophen" -> "Paracetamol"). */
function displayNames(resolutions) {
  const names = new Map();
  (resolutions ?? []).forEach((resolution) => {
    const canonical = resolution.canonical_name ?? resolution.drug?.canonical_name;
    if (canonical && resolution.input_name) {
      names.set(canonical.toLowerCase(), resolution.input_name);
    }
  });
  return names;
}

function mapPair(pair, names) {
  const a = drugName(pair.drug_a);
  const b = drugName(pair.drug_b);
  // Interaction detail is flattened onto the pair by /check, but nested under
  // `interaction` by the catalogue's own endpoints. Accept either.
  const detail = pair.interaction ?? pair;
  const severity = detail.severity ?? null;
  return {
    drugA: names.get(a.toLowerCase()) ?? a,
    drugB: names.get(b.toLowerCase()) ?? b,
    severity,
    severityRank: rankOf(pair, severity),
    description: detail.description ?? detail.interaction_text ?? null,
    mechanism: detail.mechanism ?? null,
    management: detail.management ?? null,
    pairId: detail.pair_id ?? null,
  };
}

function mapDuplicate(duplicate) {
  return {
    activeIngredient: duplicate.active_ingredient,
    severity: duplicate.severity,
    message: duplicate.message,
    medications: (duplicate.medications ?? []).map((med) => ({
      inputName: med.input_name,
      genericName: med.generic_name,
      dosageMg: med.dosage_mg,
    })),
  };
}

function mapAlternativeGroup(group) {
  return {
    inputName: group.input_name,
    genericName: group.generic_name,
    warning: group.warning,
    options: (group.alternatives ?? []).map((alt) => ({
      tradeName: alt.trade_name,
      genericName: alt.generic_name,
      dosageMg: alt.dosage_mg,
      form: alt.form,
      sameDosage: alt.same_dosage,
    })),
  };
}

function mapMedication(medication) {
  return {
    inputName: medication.input_name,
    ingredient: medication.generic_name,
    dosageMg: medication.dosage_mg,
    matchMethod: medication.match_method,
    confidence: medication.match_confidence,
  };
}

function deriveVerdict({ interactions, duplicates, status, catalogWarning }) {
  if (duplicates.length > 0) return VERDICT.DANGER;
  if (interactions.some((item) => item.severityRank >= 3)) return VERDICT.DANGER;
  if (interactions.length > 0) return VERDICT.CAUTION;
  if (catalogWarning || status === "catalog_unavailable") return VERDICT.UNKNOWN;
  if (status === "insufficient_distinct_drugs") return VERDICT.UNKNOWN;
  return VERDICT.NO_RECORD;
}

function assemble({ id, source, medications, unresolved, check, duplicates, alternatives, imageWarnings, mocked }) {
  const names = displayNames(check.resolutions);
  const interactions = (check.interactions ?? []).map((pair) => mapPair(pair, names));
  const mappedDuplicates = (duplicates ?? []).map(mapDuplicate);
  const catalogWarning = check.warning ?? null;

  const verdict = deriveVerdict({
    interactions,
    duplicates: mappedDuplicates,
    status: check.status,
    catalogWarning,
  });

  return {
    id,
    source,
    checkedLabel: "Just now",
    checkedAt: Date.now(),
    verdict,
    verdictHeadline: HEADLINES[verdict],
    verdictSummary: SUMMARIES[verdict],
    medications,
    unresolved: unresolved ?? [],
    interactions,
    noRecordPairs: (check.no_record_pairs ?? []).map((pair) => mapPair(pair, names)),
    duplicates: mappedDuplicates,
    alternatives: (alternatives ?? []).map(mapAlternativeGroup).filter((group) => group.options.length > 0),
    comparisons: check.comparisons ?? 0,
    notice: check.notice ?? null,
    catalogWarning,
    imageWarnings: imageWarnings ?? [],
    mocked: Boolean(mocked),
  };
}

function newId() {
  return `check-${Date.now()}`;
}

/** Build a report from POST /pipeline (the photo flow).
 *
 * /pipeline returns a flattened report (`drugs`, `interactionPairs`, `medications`,
 * …). Older builds returned the raw stages instead (`normalized.medications`), so
 * both are accepted — a deploy running either version still renders. */
export function reportFromPipeline(data) {
  const normalized = data.normalized ?? {};
  const rawMedications = data.medications ?? normalized.medications ?? [];

  const medications = rawMedications.length
    ? rawMedications.map(mapMedication)
    : (data.drugs ?? []).map((drug) => ({
        inputName: drug.brand,
        ingredient: drug.ingredient,
        dosageMg: null,
        matchMethod: drug.source,
      }));

  const check = {
    status: data.status ?? data.interactions?.status,
    interactions: data.interactionPairs ?? data.interactions?.interactions ?? [],
    no_record_pairs: data.noRecordPairs ?? data.interactions?.no_record_pairs ?? [],
    resolutions: data.resolutions ?? data.interactions?.resolutions ?? [],
    comparisons: data.interactions?.comparisons ?? 0,
    notice: data.notice ?? data.interactions?.notice,
    warning: data.catalogWarning ?? data.interactions?.warning,
  };

  return assemble({
    id: newId(),
    source: "photo",
    medications,
    unresolved: (data.unresolved ?? normalized.unresolved ?? []).map((item) => ({
      inputName: item.input_name ?? item.inputName ?? "",
      reason: item.reason,
    })),
    check,
    duplicates: data.duplicates ?? data.interactions?.duplicate_active_ingredients,
    alternatives: data.alternatives,
    imageWarnings: data.extracted?.image_quality_warnings ?? [],
    mocked: data.mocked ?? data.extracted?.mocked,
  });
}

/** Build a report from POST /check plus separately-fetched alternatives (the box-picker flow). */
export function reportFromCheck(check, { medications, alternatives }) {
  return assemble({
    id: newId(),
    source: "boxes",
    medications,
    unresolved: [],
    check,
    duplicates: check.duplicate_active_ingredients,
    alternatives,
  });
}
