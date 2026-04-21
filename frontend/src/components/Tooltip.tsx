import { useState, type ReactNode } from "react";

type Props = {
  content: string;
  children: ReactNode;
};

export function Tooltip({ content, children }: Props) {
  const [show, setShow] = useState(false);
  return (
    <span
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onFocus={() => setShow(true)}
      onBlur={() => setShow(false)}
      className="relative inline-block cursor-help border-b border-dotted border-text_muted"
      tabIndex={0}
    >
      {children}
      {show && (
        <span
          role="tooltip"
          className="absolute z-20 bottom-full mb-2 left-1/2 -translate-x-1/2 w-64 bg-raised border border-subtle rounded-md px-3 py-2 text-xs text-text_primary shadow-lg normal-case leading-relaxed"
          style={{ direction: "inherit" }}
        >
          {content}
        </span>
      )}
    </span>
  );
}
