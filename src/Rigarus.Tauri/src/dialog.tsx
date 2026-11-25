import { useEffect, useRef, type ReactNode } from "react";

export function Dialog({
  title,
  children,
  onClose,
  busy = false,
  initialFocus,
  className,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  busy?: boolean;
  initialFocus?: string;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    ref.current?.showModal();
    if (initialFocus)
      ref.current?.querySelector<HTMLElement>(initialFocus)?.focus();
    return () => {
      ref.current?.close();
      if (previous?.isConnected) previous.focus();
    };
  }, [initialFocus]);
  return (
    <dialog
      ref={ref}
      className={`desktop-dialog ${className ?? ""}`}
      aria-labelledby="dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) close.current();
      }}
    >
      <div className="dialog-heading">
        <h2 id="dialog-title">{title}</h2>
        <button
          type="button"
          aria-label="Close dialog"
          disabled={busy}
          onClick={onClose}
        >
          ×
        </button>
      </div>
      {children}
    </dialog>
  );
}
