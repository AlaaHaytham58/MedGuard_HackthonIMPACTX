// One consistent stroke system (1.6px round joins) for every drawn icon.

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export function ShieldMark({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <path fill="currentColor" d="M16 2 5 6.4v8.2c0 7.6 4.7 13.6 11 15.4 6.3-1.8 11-7.8 11-15.4V6.4z" />
      <path
        fill="none"
        stroke="var(--navy-50)"
        strokeWidth="2.4"
        strokeLinecap="round"
        d="M16 10.2v11.6M10.2 16h11.6"
      />
    </svg>
  );
}

export function UploadCloudIcon(props) {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" {...base} {...props}>
      <path d="M8.5 20.5h-1a4.5 4.5 0 0 1-.6-8.96A5.5 5.5 0 0 1 17.7 9.2a4.25 4.25 0 0 1 1.3 8.3" />
      <path d="M14 22v-8.5M14 13.5l-3 3M14 13.5l3 3" />
    </svg>
  );
}

export function CameraIcon(props) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" {...base} {...props}>
      <path d="M4 8.5A1.5 1.5 0 0 1 5.5 7h2.2l.9-1.5a1.5 1.5 0 0 1 1.29-.75h4.22a1.5 1.5 0 0 1 1.29.75l.9 1.5h2.2A1.5 1.5 0 0 1 20 8.5v9A1.5 1.5 0 0 1 18.5 19h-13A1.5 1.5 0 0 1 4 17.5z" />
      <circle cx="12" cy="13" r="3.2" />
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
