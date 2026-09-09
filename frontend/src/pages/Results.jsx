import { useParams, useNavigate, Link } from "react-router-dom";
import TopNav from "../components/TopNav.jsx";
import { useHistory } from "../state/HistoryContext.jsx";
import { CheckCircleIcon, AlertIcon, ChevronRightIcon } from "../components/icons.jsx";
import "./Results.css";

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { history } = useHistory();
  const report = history.find((entry) => entry.id === id) ?? history[0];
  const isSafe = report.verdict === "safe";
  const isUnknown = report.verdict === "unknown";

  return (
    <div className="page">
      <TopNav />

      <main className="results">
        <div className="results__pair">
          {report.drugs.map((drug) => (
            <span className="pair-pill" key={drug.brand}>
              {drug.brand}
            </span>
          ))}
        </div>

        <section
          className={
            "verdict verdict--" + (isSafe ? "safe" : isUnknown ? "unknown" : "danger")
          }
          aria-live="polite"
        >
          {isSafe ? <CheckCircleIcon /> : <AlertIcon />}
          <div>
            <p className="verdict__headline">{report.verdictHeadline}</p>
            <p className="verdict__meta">Checked {report.checkedLabel}</p>
          </div>
        </section>

        <div className="report-grid">
          <section className="panel">
            <h2 className="panel__heading">Active ingredients</h2>
            <ul className="ingredient-list">
              {report.drugs.map((drug) => (
                <li key={drug.brand} className="ingredient-item">
                  <div>
                    <p className="ingredient-item__brand">{drug.brand}</p>
                    <p className="ingredient-item__source">{drug.source}</p>
                  </div>
                  <p className="ingredient-item__name">{drug.ingredient}</p>
                </li>
              ))}
            </ul>
          </section>

          <section className="panel">
            <h2 className="panel__heading">Why</h2>
            {report.interactionPairs?.length ? (
              <div className="interaction-list">
                {report.interactionPairs.map((pair) => (
                  <article className="interaction-item" key={`${pair.drug_a}-${pair.drug_b}`}>
                    <p className="interaction-item__title">
                      {pair.drug_a} + {pair.drug_b}
                    </p>
                    <p className="interaction-item__severity">{pair.severity} interaction</p>
                    <p className="report-text">{pair.description}</p>
                  </article>
                ))}
              </div>
            ) : (
              <p className="report-text">{report.interaction}</p>
            )}
          </section>

          <section className="panel">
            <h2 className="panel__heading">What to do</h2>
            <ul className="bullet-list">
              {report.management.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </section>

          <section className="panel">
            <h2 className="panel__heading">Alternatives</h2>
            <ul className="alt-list">
              {report.alternatives.map((alt) => (
                <li key={alt.brand} className="alt-item">
                  <p className="alt-item__brand">{alt.brand}</p>
                  <p className="alt-item__suggestion">{alt.suggestion}</p>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <section className="history" aria-labelledby="history-heading">
          <h2 id="history-heading" className="history__heading">
            Previous checks
          </h2>
          <ul className="history-list">
            {history.map((item) => {
              const active = item.id === report.id;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={
                      "history-item" + (active ? " history-item--active" : "")
                    }
                    onClick={() => navigate(`/results/${item.id}`)}
                    aria-current={active ? "true" : undefined}
                  >
                    <span
                      className={
                        "history-item__dot history-item__dot--" +
                        (item.verdict === "safe" ? "safe" : "danger")
                      }
                      aria-hidden="true"
                    />
                    <span className="history-item__names">
                      {item.drugs.map((d) => d.brand).join(" + ")}
                    </span>
                    <span className="history-item__time">{item.checkedLabel}</span>
                    <ChevronRightIcon className="history-item__chevron" />
                  </button>
                </li>
              );
            })}
          </ul>
        </section>

        <p className="results__back">
          <Link to="/">Check another medicine</Link>
        </p>
      </main>
    </div>
  );
}
