import { NavLink } from "react-router-dom";
import { ShieldMark } from "./icons.jsx";
import "./TopNav.css";

export default function TopNav() {
  return (
    <header className="top-nav">
      <div className="top-nav__inner">
        <NavLink to="/" className="top-nav__brand">
          <ShieldMark />
          <span>
            MedGuard
            <small>Medicine safety check</small>
          </span>
        </NavLink>

        <nav className="top-nav__links" aria-label="Main">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              "top-nav__link" + (isActive ? " top-nav__link--active" : "")
            }
          >
            Home
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
      </div>
    </header>
  );
}
