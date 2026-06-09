import React from "react";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  CircleX,
  Database,
  FileDown,
  FolderKanban,
  Info,
  LayoutDashboard,
  LineChart,
  Plus,
  Save,
  Search,
  Upload
} from "lucide-react";
import hdrLogo from "../assets/hdr-logo.svg";
import type { Calculation } from "../types";

export type PageKey = "dashboard" | "projects" | "projectDetail" | "workspace" | "report" | "standards" | "graphViewer" | "references" | "about";

export const navItems = [
  ["dashboard", LayoutDashboard, "Dashboard"],
  ["projects", FolderKanban, "Projects"],
  ["standards", Database, "Standards Tables"],
  ["graphViewer", LineChart, "Graph Viewer"],
  ["references", BookOpen, "References"],
  ["about", Info, "About"]
] as const;

export function AppShell({
  page,
  setPage,
  autosave,
  activeCalc,
  children
}: {
  page: PageKey;
  setPage: (page: PageKey) => void;
  autosave: string;
  activeCalc: Calculation | null;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#f7f7f7] text-[#111827]">
      <header className="hdr-shell">
        <div className="hdr-top">
          <div className="hdr-brand">
            <img src={hdrLogo} className="hdr-logo" alt="HDR" />
            <div>
              <div className="hdr-kicker">Gas Pipeline - Technical Tool</div>
              <div className="hdr-title">API RP 1102 Loading Calculator</div>
            </div>
          </div>
          <div className="hdr-context">
            <span className="hdr-save"><Save size={15} /> {autosave}</span>
            <span className="hdr-chip">Rev {activeCalc?.revision || "0"}</span>
          </div>
        </div>
        <nav className="hdr-nav">
          {navItems.map(([key, Icon, label]) => (
            <button key={key} onClick={() => setPage(key)} className={page === key ? "active" : ""}>
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>
      </header>
      <main className="page-wrap">{children}</main>
      <footer className="app-footer">
        <div className="footer-meta">
          <span>HDR API RP 1102 Loading Calculator - v1.1.0 - Rev 0 - issued 2025-01-08</span>
          <span>Author: Barry Brookins - HDR Engineering Inc. - Rosemont IL</span>
        </div>
        <p>
          Engineering Disclaimer: This tool is intended to support engineering calculations for API RP 1102 highway/railroad loading checks.
          Results must be reviewed by a qualified engineer. The user is responsible for confirming applicability, inputs,
          assumptions, standards, and final engineering judgment before using results for design or construction.
        </p>
      </footer>
    </div>
  );
}

export function PageTitle({ title, subtitle, action }: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="page-title-row">
      <div>
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`ui-panel ${className}`}>{children}</section>;
}

export function SectionHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: React.ReactNode }) {
  return (
    <div className="section-head">
      <div>
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {right}
    </div>
  );
}

export function Button({
  variant = "secondary",
  icon,
  children,
  onClick,
  href,
  disabled = false
}: {
  variant?: "primary" | "secondary" | "ghost";
  icon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
  href?: string;
  disabled?: boolean;
}) {
  const className = `ui-button ${variant}`;
  if (href) {
    return (
      <a className={className} href={href}>
        {icon}
        {children}
      </a>
    );
  }
  return (
    <button className={className} onClick={onClick} disabled={disabled}>
      {icon}
      {children}
    </button>
  );
}

export function MetricCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <Panel className="metric-card">
      <div className="metric-label">
        {icon}
        {label}
      </div>
      <div className="metric-value">{value}</div>
    </Panel>
  );
}

export function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (value: string) => void; placeholder: string }) {
  return (
    <label className="search-box">
      <Search size={18} />
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </label>
  );
}

export function Field({
  label,
  value,
  onChange,
  readOnly,
  hint,
  helpText,
  unit,
  select,
  freeformOptions,
  options,
  textarea
}: {
  label: string;
  value: string | number;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  hint?: string;
  helpText?: string;
  unit?: string;
  select?: boolean;
  freeformOptions?: boolean;
  options?: Array<string | number>;
  textarea?: boolean;
}) {
  const comboListId = React.useId();
  const [comboOpen, setComboOpen] = React.useState(false);
  const [comboActiveIndex, setComboActiveIndex] = React.useState(-1);
  const comboOptions = (options || []).map((option) => String(option));
  const currentValue = String(value ?? "");
  const currentOptionIndex = comboOptions.findIndex((option) => option === currentValue);

  function chooseComboOption(option: string) {
    onChange?.(option);
    setComboOpen(false);
    setComboActiveIndex(comboOptions.findIndex((item) => item === option));
  }

  function onComboKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (readOnly) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (!comboOptions.length) return;
      setComboOpen(true);
      setComboActiveIndex((index) => (index + 1 >= comboOptions.length ? 0 : index + 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      if (!comboOptions.length) return;
      setComboOpen(true);
      setComboActiveIndex((index) => (index <= 0 ? comboOptions.length - 1 : index - 1));
    } else if (event.key === "Enter" && comboOpen && comboActiveIndex >= 0 && comboOptions[comboActiveIndex]) {
      event.preventDefault();
      chooseComboOption(comboOptions[comboActiveIndex]);
    } else if (event.key === "Escape") {
      setComboOpen(false);
    }
  }

  function onComboBlur(event: React.FocusEvent<HTMLLabelElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setComboOpen(false);
    }
  }

  return (
    <label className={`field ${textarea ? "textarea-field" : ""}`} onBlur={freeformOptions ? onComboBlur : undefined}>
      <span>
        {label}
        {helpText ? (
          <span className="tooltip-wrap">
            <Info size={13} tabIndex={0} aria-label={`${label} help`} />
            <span className="field-tooltip" role="tooltip">{helpText}</span>
          </span>
        ) : (
          <Info size={13} aria-hidden="true" />
        )}
      </span>
      <div className={`field-control ${freeformOptions ? "combo-control" : ""}`}>
        {textarea ? (
          <textarea value={value ?? ""} onChange={(event) => onChange?.(event.target.value)} readOnly={readOnly} />
        ) : select ? (
          <select value={value} onChange={(event) => onChange?.(event.target.value)} disabled={readOnly}>
            {(options || []).map((option) => (
              <option key={String(option)} value={option}>
                {option}
              </option>
            ))}
          </select>
        ) : freeformOptions ? (
          <>
            <input
              value={value ?? ""}
              onChange={(event) => {
                onChange?.(event.target.value);
                setComboOpen(true);
                setComboActiveIndex(comboOptions.findIndex((option) => option === event.target.value));
              }}
              readOnly={readOnly}
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={comboOpen}
              aria-controls={comboListId}
              aria-activedescendant={comboActiveIndex >= 0 ? `${comboListId}-${comboActiveIndex}` : undefined}
              onFocus={() => {
                if (!readOnly) {
                  setComboActiveIndex(currentOptionIndex);
                }
              }}
              onKeyDown={onComboKeyDown}
            />
            <button
              type="button"
              className="combo-toggle"
              aria-label={`Show ${label} options`}
              aria-expanded={comboOpen}
              disabled={readOnly}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => {
                setComboOpen((open) => !open);
                setComboActiveIndex(currentOptionIndex >= 0 ? currentOptionIndex : 0);
              }}
            >
              <ChevronDown size={16} />
            </button>
            {comboOpen && comboOptions.length ? (
              <ul className="combo-menu" id={comboListId} role="listbox">
                {comboOptions.map((option, index) => (
                  <li
                    id={`${comboListId}-${index}`}
                    className={`combo-option ${index === comboActiveIndex ? "active" : ""} ${option === currentValue ? "selected" : ""}`}
                    key={option}
                    role="option"
                    aria-selected={option === currentValue}
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => chooseComboOption(option)}
                  >
                    {option}
                  </li>
                ))}
              </ul>
            ) : null}
          </>
        ) : (
          <input value={value ?? ""} onChange={(event) => onChange?.(event.target.value)} readOnly={readOnly} />
        )}
        {unit ? <em>{unit}</em> : null}
      </div>
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

export function StatusPill({ value }: { value: string }) {
  const normalized = (value || "Not Calculated").toLowerCase().replaceAll(" ", "-");
  const Icon = statusIcon(value);
  return <span className={`status-pill ${normalized}`}><Icon size={13} />{value || "Not Calculated"}</span>;
}

export function ResultBadge({ value }: { value: string }) {
  const Icon = statusIcon(value);
  return (
    <span className={`result-badge ${(value || "not-calculated").toLowerCase().replaceAll(" ", "-")}`}>
      <Icon size={13} />
      {value || "Not Calculated"}
    </span>
  );
}

function statusIcon(value: string) {
  if (value === "Pass") return CheckCircle2;
  if (value === "Fail") return CircleX;
  if (value === "Needs Review") return AlertTriangle;
  return Info;
}

export function UtilizationBar({ value }: { value: number }) {
  return (
    <span className="util-wrap">
      <span style={{ width: `${Math.min(Math.max(value * 100, 0), 100)}%` }} />
    </span>
  );
}

export function ToolbarButtonSet({ projectId }: { projectId: number }) {
  return (
    <div className="toolbar-actions">
      <Button href={`/api/exports/project/${projectId}.csv`} icon={<FileDown size={16} />}>
        Export CSV
      </Button>
      <Button href={`/api/exports/project/${projectId}.json`} icon={<FileDown size={16} />}>
        Export JSON
      </Button>
      <Button variant="primary" href={`/api/exports/project/${projectId}.pdf`} icon={<FileDown size={16} />}>
        Print / PDF
      </Button>
    </div>
  );
}

export const icons = { AlertTriangle, CheckCircle2, Database, FileDown, FolderKanban, Info, LayoutDashboard, Plus, Save, Search, Upload };
