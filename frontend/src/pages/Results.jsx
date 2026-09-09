import { Link, useNavigate, useParams } from "react-router-dom";
import TopNav from "../components/TopNav.jsx";
import { useHistory } from "../state/HistoryContext.jsx";
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
  const report = history.find((entry) => entry.id === id) ?? history[0];

  if (!report) {
    return (
      <div className="page">
        <TopNav />
        <main className="results results--empty">
          <div className="shell shell--narrow">
            <h1 className="results__emptyTitle">No check to show yet</h1>
            <p className="results__emptyBody">
              Photograph your medicine boxes or pick them from the list, and the report
              will appear here.
            </p>
            <button type="button" className="mg-btn mg-btn--solid" onClick={() => navigate("/")}>
              Start a check
            </button>
          </div>
        </main>
      </div>
    );
  }

  const VerdictIcon = VERDICT_ICON[report.verdict];
  const hasFindings = report.interactions.length > 0 || report.duplicates.length > 0;

  return (
    <div className="page">
      <TopNav />

      <main className="results">
        {/* ---------- Verdict ---------- */}
        <section className={`verdict verdict--${report.verdict}`}>
          <div className="shell">
            <div className="verdict__inner">
              <VerdictIcon className="verdict__icon" width={44} height={44} />
              <div>
                <p className="verdict__kicker">Checked {report.checkedLabel}</p>
                <h1 className="verdict__headline">{report.verdictHeadline}</h1>
                <p className="verdict__summary">{report.verdictSummary}</p>
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
          {/* ---------- Duplicate active ingredient ---------- */}
          {report.duplicates.length > 0 && (
            <section className="panel panel--flag">
              <h2 className="panel__title">Same ingredient, different boxes</h2>
              {report.duplicates.map((duplicate) => (
                <div key={duplicate.activeIngredient} className="duplicate">
                  <div className="duplicate__head">
                    <AlertIcon width={22} height={22} />
                    <p>
                      <strong>{duplicate.activeIngredient}</strong> appears in{" "}
                      {duplicate.medications.length} of your boxes
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
              <h2 className="panel__title">What the database found</h2>
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
                        {severityLabel(interaction.severity)}
                      </span>
                    </div>
                    {interaction.description && (
                      <p className="interaction__text">{interaction.description}</p>
                    )}
                    {interaction.management && (
                      <p className="interaction__manage">
                        <strong>What to do:</strong> {interaction.management}
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
              <h2 className="panel__title">Pairs with no record</h2>
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
              <h2 className="panel__title">We could not identify these</h2>
              <ul className="unresolved-list">
                {report.unresolved.map((item) => (
                  <li key={item.inputName}>
                    <strong>{item.inputName || "An unreadable photo"}</strong>
                    {item.reason ? ` — ${item.reason}` : ""}
                  </li>
                ))}
              </ul>
              <p className="panel__note">
                These were not checked at all. Show them to your pharmacist rather than
                assuming they are fine.
              </p>
            </section>
          )}

          {/* ---------- Alternatives (badeel) ---------- */}
          {report.alternatives.length > 0 && (
            <section className="panel">
              <h2 className="panel__title">Same ingredient, other brands</h2>
              <p className="panel__lede">
                If a pharmacy does not stock your brand, these Egyptian products contain
                the same active ingredient. Confirm any swap with the pharmacist.
              </p>
              <div className="alt-groups">
                {report.alternatives.map((group) => (
                  <div key={group.inputName} className="alt-group">
                    <p className="alt-group__source">
                      Instead of <strong>{group.inputName}</strong>
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
              <h2 className="panel__title">Nothing to report</h2>
              <p className="panel__lede">
                {report.catalogWarning ??
                  "No pairs could be compared. Ask your pharmacist before combining these."}
              </p>
            </section>
          )}

          {/* ---------- Image quality ---------- */}
          {report.imageWarnings.length > 0 && (
            <p className="results__imgwarn">
              <InfoIcon width={18} height={18} />
              The photos had {report.imageWarnings.join(", ")}. A clearer shot may pick up
              more of the label.
            </p>
          )}

          {/* ---------- Provenance ---------- */}
          <div className="results__provenance">
            <ShieldMark size={26} />
            <p>
              The AI only read the names off your boxes. Every verdict above came from the
              DDInter catalogue. MedGuard does not replace your doctor or pharmacist.
            </p>
          </div>

          <div className="results__actions">
            <button type="button" className="mg-btn mg-btn--outline" onClick={() => window.print()}>
              <PrinterIcon width={20} height={20} /> Print this page
            </button>
            <Link to="/" className="mg-btn mg-btn--solid">
              Check other medicines
            </Link>
          </div>

          {/* ---------- Session history ---------- */}
          {history.length > 1 && (
            <section className="panel">
              <h2 className="panel__title">Earlier checks this session</h2>
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
