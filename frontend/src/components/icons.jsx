// One consistent stroke system (1.6px round joins) for every drawn icon.

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export function ShieldMark({ size = 28, crossColor = "var(--cyan)" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <path fill="currentColor" d="M16 2 5 6.4v8.2c0 7.6 4.7 13.6 11 15.4 6.3-1.8 11-7.8 11-15.4V6.4z" />
      <path
        fill="none"
        stroke={crossColor}
        strokeWidth="2.4"
        strokeLinecap="round"
        d="M16 10.2v11.6M10.2 16h11.6"
      />
    </svg>
  );
}

export function ScanFrameIcon(props) {
  return (
    <svg width="60" height="52" viewBox="0 0 60 52" {...base} {...props}>
      <path d="M8 18V9a2 2 0 0 1 2-2h9" />
      <path d="M52 18V9a2 2 0 0 0-2-2h-9" />
      <path d="M8 34v9a2 2 0 0 0 2 2h9" />
      <path d="M52 34v9a2 2 0 0 1-2 2h-9" />
      <rect x="23" y="17" width="14" height="19" rx="3" stroke="var(--navy-900)" />
      <path d="M27 17v-4a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 33 13v4" stroke="var(--navy-900)" />
      <path d="M23 26.5h14" stroke="var(--navy-900)" />
    </svg>
  );
}

export function ArrowRightIcon(props) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" {...base} {...props}>
      <path d="M4 12h15" />
      <path d="m14 7 5 5-5 5" />
    </svg>
  );
}

export function PrinterIcon(props) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" {...base} {...props}>
      <path d="M6 9V3h12v6" />
      <path d="M6 18H4.5A1.5 1.5 0 0 1 3 16.5v-6A1.5 1.5 0 0 1 4.5 9h15a1.5 1.5 0 0 1 1.5 1.5v6a1.5 1.5 0 0 1-1.5 1.5H18" />
      <path d="M6 14h12v7H6z" />
    </svg>
  );
}

export function MenuIcon(props) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" {...base} {...props}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  );
}

export function SearchIcon(props) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" {...base} {...props}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m20 20-4.3-4.3" />
    </svg>
  );
}

export function CheckCircleIcon(props) {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" {...base} {...props}>
      <circle cx="13" cy="13" r="10.2" />
      <path d="m8.5 13.3 3 3 6-6.2" />
    </svg>
  );
}

export function AlertIcon(props) {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" {...base} {...props}>
      <path d="M13 3.6 23.4 21.8H2.6z" strokeLinejoin="round" />
      <path d="M13 10.4v5.4" />
      <circle cx="13" cy="19.2" r="0.15" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function InfoIcon(props) {
  return (
    <svg width="20" height="20" viewBox="0 0 22 22" {...base} {...props}>
      <circle cx="11" cy="11" r="8.4" />
      <path d="M11 10v5.2" />
      <circle cx="11" cy="7.1" r="0.15" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function ChevronRightIcon(props) {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" {...base} {...props}>
      <path d="m7 4 5 5-5 5" />
    </svg>
  );
}

export function TrashIcon(props) {
  return (
    <svg width="16" height="16" viewBox="0 0 20 20" {...base} {...props}>
      <path d="M4.5 6h11M8.2 6V4.4h3.6V6M6 6l.6 9.4a1.4 1.4 0 0 0 1.4 1.3h4a1.4 1.4 0 0 0 1.4-1.3L14 6" />
    </svg>
  );
}

export function SpinnerIcon({ size = 20 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className="spinner-icon"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeOpacity="0.2" strokeWidth="2.4" />
      <path
        d="M21.5 12a9.5 9.5 0 0 0-9.5-9.5"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
    </svg>
  );
}
