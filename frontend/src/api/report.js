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

function mapPair(pair) {
  return {
    drugA: pair.drug_a,
    drugB: pair.drug_b,
    severity: pair.severity,
    severityRank: pair.severity_rank ?? 0,
    description: pair.description,
    mechanism: pair.mechanism,
    management: pair.management,
    pairId: pair.pair_id,
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

function assemble({ id, source, medications, unresolved, check, duplicates, alternatives, imageWarnings }) {
  const interactions = (check.interactions ?? []).map(mapPair);
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
    noRecordPairs: (check.no_record_pairs ?? []).map(mapPair),
    duplicates: mappedDuplicates,
    alternatives: (alternatives ?? []).map(mapAlternativeGroup).filter((group) => group.options.length > 0),
    comparisons: check.comparisons ?? 0,
    notice: check.notice ?? null,
    catalogWarning,
    imageWarnings: imageWarnings ?? [],
  };
}

function newId() {
  return `check-${Date.now()}`;
}

/** Build a report from POST /pipeline (the photo flow). */
export function reportFromPipeline(data) {
  const normalized = data.normalized ?? {};
  return assemble({
    id: newId(),
    source: "photo",
    medications: (normalized.medications ?? []).map(mapMedication),
    unresolved: (normalized.unresolved ?? []).map((item) => ({
      inputName: item.input_name,
      reason: item.reason,
    })),
    check: data.interactions ?? {},
    duplicates: data.duplicates,
    alternatives: data.alternatives,
    imageWarnings: data.extracted?.image_quality_warnings ?? [],
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
