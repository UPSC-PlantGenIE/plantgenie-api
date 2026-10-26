import { useEffect, type PropsWithChildren } from "react";

interface ModalProps {
  title: string;
  onClose: () => void;
}

export default function Modal({
  title,
  onClose,
  children,
}: PropsWithChildren<ModalProps>) {
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-card"
      >
        <h2 className="text-lg font-bold text-heading">{title}</h2>
        {children}
      </div>
    </div>
  );
}
