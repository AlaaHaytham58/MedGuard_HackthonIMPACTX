import { Link, useNavigate, useParams } from "react-router-dom";
import TopNav from "../components/TopNav.jsx";
import { useHistory } from "../state/HistoryContext.jsx";
import { useLanguage } from "../state/LanguageContext.jsx";
import { VERDICT } from "../api/report.js";
import {
  AlertIcon,
  InfoIcon,
  CheckCircleIcon,
  ChevronRightIcon,
  PrinterIcon,
  ShieldMark,
} from "../components/icons.jsx";
import "./Results.css";

const VERDICT_ICON = {
  [VERDICT.DANGER]: AlertIcon,
  [VERDICT.CAUTION]: AlertIcon,
  [VERDICT.NO_RECORD]: CheckCircleIcon,
  [VERDICT.UNKNOWN]: InfoIcon,
};

function severityLabel(severity) {
  if (!severity || severity === "Unknown") return "Severity not rated";
  return `${severity} severity`;
}

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { history } = useHistory();
  const { t, isArabic } = useLanguage();
  const report = history.find((entry) => entry.id === id) ?? history[0];

  if (!report) {
    return (
      <div className="page">
        <TopNav />
        <main className="results results--empty">
          <div className="shell shell--narrow">
            <h1 className="results__emptyTitle">{t("No check to show yet")}</h1>
            <p className="results__emptyBody">
              {isArabic ? "صوّر عبوات أدويتك أو اخترها من القائمة، وسيظهر التقرير هنا." : "Photograph your medicine boxes or pick them from the list, and the report will appear here."}
            </p>
            <button type="button" className="mg-btn mg-btn--solid" onClick={() => navigate("/")}>
              {t("Start a check")}
            </button>
          </div>
        </main>
      </div>
    );
  }

  const VerdictIcon = VERDICT_ICON[report.verdict];
  const hasFindings = report.interactions.length > 0 || report.duplicates.length > 0;
  const conditionLabels = {
    pregnancy: isArabic ? "الحمل" : "Pregnancy",
    high_blood_pressure: isArabic ? "ارتفاع ضغط الدم" : "High blood pressure",
    diabetes: isArabic ? "السكري" : "Diabetes",
    lactation: isArabic ? "الرضاعة الطبيعية" : "Breastfeeding",
    heart: isArabic ? "أمراض القلب" : "Heart disease",
  };

  return (
    <div className="page">
      <TopNav />

      <main className="results">
        {report.mocked && (
          <div className="mock-banner" role="alert">
            <div className="shell">
              <AlertIcon width={26} height={26} />
              <div>
                <p className="mock-banner__title">{t("Demo data — your photos were not read")}</p>
                <p className="mock-banner__body">
                  {t("The server is running with")} <code>MOCK_EXTRACT=1</code>, {t("so the medicines below are a fixed sample, not what is on your boxes. Turn mock extraction off to check real photos.")}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ---------- Verdict ---------- */}
        <section className={`verdict verdict--${report.verdict}`}>
          <div className="shell">
            <div className="verdict__inner">
              <VerdictIcon className="verdict__icon" width={44} height={44} />
              <div>
                <p className="verdict__kicker">{t("Checked")} {t(report.checkedLabel)}</p>
                <h1 className="verdict__headline">{t(report.verdictHeadline)}</h1>
                <p className="verdict__summary">{t(report.verdictSummary)}</p>
              </div>
            </div>

            <ul className="verdict__pills">
              {report.medications.map((medication) => (
                <li key={medication.inputName} className="med-pill">
                  {medication.image && <img src={medication.image} alt="" />}
                  <span>
                    <strong>{medication.inputName}</strong>
                    <small>
                      {medication.ingredient}
                      {medication.dosageMg ? ` · ${medication.dosageMg}mg` : ""}
                    </small>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <div className="shell results__body">
          {report.conditionWarnings.length > 0 && (
            <section className="condition-warning-list" aria-label={isArabic ? "تحذيرات ملف المريض" : "Patient profile warnings"}>
              {report.conditionWarnings.map((warning, index) => (
                <article className="condition-warning" key={`${warning.drug}-${warning.condition}-${index}`}>
                  <AlertIcon width={24} height={24} />
                  <div>
                    <p className="condition-warning__title">
                      {isArabic ? "تحذير متعلق بملف المريض" : "Patient profile warning"}
                    </p>
                    <p className="condition-warning__body">
                      <strong>{warning.drug}</strong>{" — "}
                      {isArabic
                        ? `يتطلب حذرًا بسبب ${conditionLabels[warning.condition] || warning.condition}.`
                        : `${warning.message} (${conditionLabels[warning.condition] || warning.condition})`}
                    </p>
                  </div>
                </article>
              ))}
            </section>
          )}

          {/* ---------- Duplicate active ingredient ---------- */}
          {report.duplicates.length > 0 && (
            <section className="panel panel--flag">
              <h2 className="panel__title">{t("Same ingredient, different boxes")}</h2>
              {report.duplicates.map((duplicate) => (
                <div key={duplicate.activeIngredient} className="duplicate">
                  <div className="duplicate__head">
                    <AlertIcon width={22} height={22} />
                    <p>
                      <strong>{duplicate.activeIngredient}</strong>{t(" appears in ")} {duplicate.medications.length}{t(" of your boxes")}
                    </p>
                  </div>
                  <p className="duplicate__body">{duplicate.message}</p>
                  <ul className="duplicate__list">
                    {duplicate.medications.map((medication) => (
                      <li key={medication.inputName}>
                        {medication.inputName}
                        {medication.dosageMg ? ` — ${medication.dosageMg}mg` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </section>
          )}

          {/* ---------- Interactions ---------- */}
          {report.interactions.length > 0 && (
            <section className="panel">
              <h2 className="panel__title">{t("What the database found")}</h2>
              <ul className="interaction-list">
                {report.interactions.map((interaction) => (
                  <li
                    key={`${interaction.drugA}-${interaction.drugB}`}
                    className={`interaction interaction--rank${interaction.severityRank}`}
                  >
                    <div className="interaction__head">
                      <p className="interaction__pair">
                        {interaction.drugA} <span>+</span> {interaction.drugB}
                      </p>
                      <span className="interaction__severity">
                        {t(severityLabel(interaction.severity))}
                      </span>
                    </div>
                    {interaction.description && (
                      <p className="interaction__text">{t(interaction.description)}</p>
                    )}
                    {interaction.management && (
                      <p className="interaction__manage">
                        <strong>{t("What to do:")}</strong> {t(interaction.management)}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* ---------- Pairs with no record ---------- */}
          {report.noRecordPairs.length > 0 && (
            <section className="panel">
              <h2 className="panel__title">{t("Pairs with no record")}</h2>
              <ul className="norecord-list">
                {report.noRecordPairs.map((pair) => (
                  <li key={`${pair.drugA}-${pair.drugB}`}>
                    {pair.drugA} <span>+</span> {pair.drugB}
                  </li>
                ))}
              </ul>
              {report.notice && <p className="panel__note">{report.notice}</p>}
            </section>
          )}

          {/* ---------- Unreadable / unresolved ---------- */}
          {report.unresolved.length > 0 && (
            <section className="panel panel--flag">
              <h2 className="panel__title">{t("We could not identify these")}</h2>
              <ul className="unresolved-list">
                {report.unresolved.map((item) => (
                  <li key={item.inputName}>
                    <strong>{item.inputName || (isArabic ? "صورة غير مقروءة" : "An unreadable photo")}</strong>
                    {item.reason ? ` — ${item.reason}` : ""}
                  </li>
                ))}
              </ul>
              <p className="panel__note">{t("These were not checked at all. Show them to your pharmacist rather than assuming they are fine.")}</p>
            </section>
          )}

          {/* ---------- Alternatives (badeel) ---------- */}
          {report.alternatives.length > 0 && (
            <section className="panel">
              <h2 className="panel__title">{t("Same ingredient, other brands")}</h2>
              <p className="panel__lede">{t("If a pharmacy does not stock your brand, these Egyptian products contain the same active ingredient. Confirm any swap with the pharmacist.")}</p>
              <div className="alt-groups">
                {report.alternatives.map((group) => (
                  <div key={group.inputName} className="alt-group">
                    <p className="alt-group__source">
                      {t("Instead of")} <strong>{group.inputName}</strong>
                      <small>{group.genericName}</small>
                    </p>
                    <ul className="alt-list">
                      {group.options.map((option) => (
                        <li key={option.tradeName}>
                          <span className="alt-list__name">{option.tradeName}</span>
                          {option.dosageMg && (
                            <span className="alt-list__dose">{option.dosageMg}mg</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ---------- Nothing found at all ---------- */}
          {!hasFindings && report.noRecordPairs.length === 0 && (
            <section className="panel">
              <h2 className="panel__title">{t("Nothing to report")}</h2>
              <p className="panel__lede">
                {report.catalogWarning ??
                  t("No pairs could be compared. Ask your pharmacist before combining these.")}
              </p>
            </section>
          )}

          {/* ---------- Image quality ---------- */}
          {report.imageWarnings.length > 0 && (
            <p className="results__imgwarn">
              <InfoIcon width={18} height={18} />
              {t("The photos had")} {report.imageWarnings.join(", ")}. {t("A clearer shot may pick up more of the label.")}
            </p>
          )}

          {/* ---------- Provenance ---------- */}
          <div className="results__provenance">
            <ShieldMark size={26} />
            <p>
              {t("The AI only read the names off your boxes. Every verdict above came from the DDInter catalogue. MedGuard does not replace your doctor or pharmacist.")}
            </p>
          </div>

          <div className="results__actions">
            <button type="button" className="mg-btn mg-btn--outline" onClick={() => window.print()}>
              <PrinterIcon width={20} height={20} /> {t("Print this page")}
            </button>
            <Link to="/" className="mg-btn mg-btn--solid">
              {t("Check other medicines")}
            </Link>
          </div>

          {/* ---------- Session history ---------- */}
          {history.length > 1 && (
            <section className="panel">
              <h2 className="panel__title">{t("Earlier checks this session")}</h2>
              <ul className="history-list">
                {history
                  .filter((entry) => entry.id !== report.id)
                  .map((entry) => (
                    <li key={entry.id}>
                      <Link to={`/results/${entry.id}`} className="history-item">
                        <span className={`history-item__dot history-item__dot--${entry.verdict}`} />
                        <span className="history-item__names">
                          {entry.medications.map((m) => m.inputName).join(" + ")}
                        </span>
                        <span className="history-item__time">{entry.checkedLabel}</span>
                        <ChevronRightIcon className="history-item__chevron" />
                      </Link>
                    </li>
                  ))}
              </ul>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
