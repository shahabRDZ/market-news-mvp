import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function NavBar() {
  const { user, logout } = useAuth();
  return (
    <header className="border-b border-subtle bg-canvas/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-4 md:px-6 h-14">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-brand" />
          <span className="font-semibold tracking-tight">MNI</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm text-text_secondary">
          <NavLink to="/dashboard" className={({ isActive }) => (isActive ? "text-text_primary" : "hover:text-text_primary")}>
            Dashboard
          </NavLink>
          <NavLink to="/pricing" className={({ isActive }) => (isActive ? "text-text_primary" : "hover:text-text_primary")}>
            Pricing
          </NavLink>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="hover:text-text_primary"
          >
            API
          </a>
          {user ? (
            <>
              <NavLink to="/account" className={({ isActive }) => (isActive ? "text-text_primary" : "hover:text-text_primary")}>
                Account
              </NavLink>
              <button onClick={logout} className="text-text_muted hover:text-text_primary">
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="hover:text-text_primary">Log in</NavLink>
              <NavLink
                to="/register"
                className="bg-brand text-canvas font-medium rounded-md px-3 py-1.5 hover:brightness-110"
              >
                Start free
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
