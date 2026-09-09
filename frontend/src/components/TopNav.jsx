import { NavLink } from "react-router-dom";
import { ShieldMark, SearchIcon } from "./icons.jsx";
import "./TopNav.css";

export default function TopNav() {
  return (
    <header className="top-nav">
      <div className="top-nav__inner">
        <NavLink to="/" className="top-nav__brand">
          <ShieldMark size={30} />
          <span>MedGuard</span>
        </NavLink>

        <nav className="top-nav__links" aria-label="Main">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              "top-nav__link" + (isActive ? " top-nav__link--active" : "")
            }
          >
            Check
          </NavLink>
          <NavLink
            to="/results"
            className={({ isActive }) =>
              "top-nav__link" + (isActive ? " top-nav__link--active" : "")
            }
          >
            Results
          </NavLink>
        </nav>

        <a href="#search" className="top-nav__search" aria-label="Search by medicine name">
          <SearchIcon />
        </a>
      </div>
    </header>
  );
}
