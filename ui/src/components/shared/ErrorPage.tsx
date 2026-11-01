import { buttonClassName } from "./buttonClassName";

type ErrorPageProps = {
  message: string;
  onRetry?: () => void;
};

export default function ErrorPage({ message, onRetry }: ErrorPageProps) {
  return (
    <div
      role="alert"
      className="mx-auto w-full max-w-lg px-6 py-16 text-center"
    >
      <h1 className="text-2xl font-bold text-heading">Something went wrong</h1>
      <p className="mt-2 text-sm text-label">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className={`${buttonClassName()} mt-6`}
        >
          Try again
        </button>
      )}
    </div>
  );
}
