import { NavLink } from "react-router-dom";
import { useLanguage } from "../state/LanguageContext.jsx";
import { ShieldMark, SearchIcon } from "./icons.jsx";
import "./TopNav.css";

export default function TopNav() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <header className="top-nav">
      <div className="top-nav__inner">
        <NavLink to="/" className="top-nav__brand">
          <ShieldMark size={30} />
          <span>MedGuard</span>
        </NavLink>

        <nav className="top-nav__links" aria-label={t("Main") || "Main"}>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              "top-nav__link" + (isActive ? " top-nav__link--active" : "")
            }
          >
            {t("Check")}
          </NavLink>
          <NavLink
            to="/results"
            className={({ isActive }) =>
              "top-nav__link" + (isActive ? " top-nav__link--active" : "")
            }
          >
            {t("Results")}
          </NavLink>
        </nav>

        <div className="top-nav__actions">
          <div className="top-nav__language" aria-label={language === "ar" ? "اختر اللغة" : "Choose language"}>
            <button
              type="button"
              className={"top-nav__language-btn" + (language === "en" ? " top-nav__language-btn--active" : "")}
              onClick={() => setLanguage("en")}
              aria-pressed={language === "en"}
            >
              EN
            </button>
            <span className="top-nav__language-divider" aria-hidden="true">|</span>
            <button
              type="button"
              className={"top-nav__language-btn" + (language === "ar" ? " top-nav__language-btn--active" : "")}
              onClick={() => setLanguage("ar")}
              aria-pressed={language === "ar"}
            >
              AR
            </button>
          </div>

          <a href="#search" className="top-nav__search" aria-label={t("Search by medicine name")}>
            <SearchIcon />
          </a>
        </div>
      </div>
    </header>
  );
}
