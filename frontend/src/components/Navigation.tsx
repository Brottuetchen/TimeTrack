import { useState } from "react";

interface Props {
  currentPage: "home" | "admin" | "privacy";
  onPageChange: (page: "home" | "admin" | "privacy") => void;
  theme: "light" | "dark";
  onThemeToggle: () => void;
}

export function Navigation({ currentPage, onPageChange, theme, onThemeToggle }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);

  const menuItems = [
    { id: "home" as const, label: "Logs", icon: "📋" },
    { id: "admin" as const, label: "Administration", icon: "⚙️" },
    { id: "privacy" as const, label: "Privacy", icon: "🔒" },
  ];

  const handleNavigate = (page: "home" | "admin" | "privacy") => {
    onPageChange(page);
    setMenuOpen(false);
  };

  return (
    <nav className="relative">
      {/* Mobile Burger Menu Button */}
      <button
        onClick={() => setMenuOpen(!menuOpen)}
        className="p-2 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        aria-label="Menu"
      >
        <svg
          className="w-6 h-6 text-slate-700 dark:text-slate-200"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {menuOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Dropdown Menu */}
      {menuOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />

          {/* Menu Card */}
          <div className="absolute top-12 right-0 z-50 w-64 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
              <h3 className="font-semibold text-slate-900 dark:text-white">Navigation</h3>
            </div>

            {/* Menu Items */}
            <div className="py-2">
              {menuItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleNavigate(item.id)}
                  className={`
                    w-full px-4 py-3 flex items-center gap-3 text-left transition-colors
                    ${
                      currentPage === item.id
                        ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium"
                        : "text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
                    }
                  `}
                >
                  <span className="text-xl">{item.icon}</span>
                  <span>{item.label}</span>
                  {currentPage === item.id && (
                    <svg className="w-5 h-5 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>

            {/* Theme Toggle */}
            <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
              <button
                onClick={() => {
                  onThemeToggle();
                  setMenuOpen(false);
                }}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors flex items-center justify-between"
              >
                <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Dark Mode</span>
                <span className="text-xl">{theme === "dark" ? "🌙" : "☀️"}</span>
              </button>
            </div>
          </div>
        </>
      )}
    </nav>
  );
}
