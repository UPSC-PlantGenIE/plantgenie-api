import { useRef, useState } from "react";
import {
  MAX_RANDOM_GENES,
  useAddRandomGenesMutation,
} from "../../api/randomGenesApi";

interface Props {
  listId: string;
  className: string;
}

/**
 * "Randomize" entry point: fills the list with random genes of its annotation.
 * Clicking the button opens a small number box next to it; OK adds the genes.
 */
export default function RandomizeControl({ listId, className }: Props) {
  const [addRandomGenes, { isLoading }] = useAddRandomGenesMutation();
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const trimmedValue = value.trim();
  const count = Number(trimmedValue);
  const valid =
    /^\d+$/.test(trimmedValue) && count >= 1 && count <= MAX_RANDOM_GENES;
  const invalid = trimmedValue !== "" && !valid;

  const toggle = () => {
    setOpen((o) => !o);
    setError("");
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const submit = async () => {
    if (!valid || isLoading) return;
    setError("");
    try {
      await addRandomGenes({ listId, count }).unwrap();
    } catch {
      setError("Could not generate genes. Please try again.");
    }
  };

  return (
    <div className="flex flex-col items-center gap-2 sm:relative">
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        title="Generate a list with random gene IDs"
        className={className}
      >
        🎲 Randomize
      </button>
      {open && (
        <div
          role="group"
          aria-label="Number of random genes"
          className="flex items-center gap-2 sm:absolute sm:left-full sm:top-1/2 sm:ml-3 sm:-translate-y-1/2"
        >
          <input
            ref={inputRef}
            type="text"
            inputMode="numeric"
            aria-invalid={invalid}
            aria-describedby={invalid ? "random-genes-hint" : undefined}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
              if (e.key === "Escape") toggle();
            }}
            placeholder="How many?"
            aria-label="Number of genes to generate"
            title={`Between 1 and ${MAX_RANDOM_GENES}`}
            className="h-9 w-24 rounded-md border border-border bg-input px-2 text-center text-xs text-heading placeholder:text-muted focus:border-primary focus:outline-none"
          />
          <button
            type="button"
            onClick={submit}
            disabled={!valid || isLoading}
            className="inline-flex h-9 cursor-pointer items-center justify-center rounded-md bg-primary px-3 text-xs font-semibold text-white shadow-card disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? "…" : "OK"}
          </button>
          {invalid && (
            <p
              id="random-genes-hint"
              role="status"
              className="whitespace-nowrap text-xs text-red-600"
            >
              Please choose a number between 1 and {MAX_RANDOM_GENES}.
            </p>
          )}
        </div>
      )}
      {error && (
        <p role="alert" className="text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}
