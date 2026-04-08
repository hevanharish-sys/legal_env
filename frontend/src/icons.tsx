import React from "react";

type IconProps = {
  className?: string;
};

export function ChevronDownIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M5 7.5L10 12.5L15 7.5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function UpArrowIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M10 16V4"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M6 8L10 4L14 8"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function StarIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M10 2.2l2.15 4.55 5.03.73-3.64 3.55.86 5.02L10 13.82l-4.4 2.25.86-5.02L2.82 7.48l5.03-.73L10 2.2z"
        fill="currentColor"
      />
    </svg>
  );
}

export function SparkleAIIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M10 2l1.2 3.9L15 7.1l-3.8 1.2L10 12l-1.2-3.7L5 7.1l3.8-1.2L10 2z"
        fill="currentColor"
        opacity="0.9"
      />
      <path
        d="M15.3 10.5l.7 2.2 2.2.7-2.2.7-.7 2.2-.7-2.2-2.2-.7 2.2-.7.7-2.2z"
        fill="currentColor"
        opacity="0.9"
      />
    </svg>
  );
}

export function PaperclipIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M7.2 10.4l5.4-5.4a2.5 2.5 0 013.5 3.5l-6.2 6.2a4 4 0 01-5.7-5.7l6-6"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function MicrophoneIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M10 12.2a2.6 2.6 0 002.6-2.6V6.4A2.6 2.6 0 0010 3.8 2.6 2.6 0 007.4 6.4v3.2A2.6 2.6 0 0010 12.2z"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path
        d="M5.6 9.7a4.4 4.4 0 008.8 0"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path
        d="M10 14.1v2.1"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function SearchIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M9 15a6 6 0 100-12 6 6 0 000 12z"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path
        d="M13.6 13.6L17 17"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}


export function DownloadIcon({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 15V3m0 12l-4-4m4 4l4-4M4 17v4h16v-4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
