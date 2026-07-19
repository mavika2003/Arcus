"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center px-6 text-center">
      <h2 className="text-xl font-semibold text-text">Could not load dashboard</h2>
      <p className="mt-2 max-w-md text-sm text-text-secondary">
        {error.message || "Something went wrong while rendering this page."}
      </p>
      <button
        type="button"
        onClick={() => reset()}
        className="btn-primary mt-6"
      >
        Try again
      </button>
    </div>
  );
}
