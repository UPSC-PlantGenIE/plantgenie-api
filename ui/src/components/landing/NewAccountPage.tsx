import { useState } from "react";
import { Link, Redirect } from "wouter";
import { useCreateAccountMutation } from "../../api/plantgenieApi";
import { setAccountId } from "../../store/accountSlice";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { buttonClassName } from "../shared/buttonClassName";
import ErrorPage from "../shared/ErrorPage";

function formatAccountId(accountId: string) {
  return accountId.match(/.{1,4}/g)?.join(" ") ?? accountId;
}

export default function NewAccountPage() {
  const [generatedAccountId, setGeneratedAccountId] = useState<string | null>(
    null
  );
  const [isCopied, setIsCopied] = useState(false);
  const [createAccount, { isError, reset }] = useCreateAccountMutation();
  const dispatch = useAppDispatch();
  const signedInUser = useAppSelector((state) => state.account.accountId);

  async function handleGenerate() {
    try {
      const { accountId: newAccountId } = await createAccount().unwrap();
      setGeneratedAccountId(newAccountId);
    } catch {
      return;
    }
  }

  const handleContinue = (accountForContinuing: string) => {
    dispatch(setAccountId(accountForContinuing));
  };

  async function handleCopy(accountIdToCopy: string) {
    await navigator.clipboard.writeText(accountIdToCopy);
    setIsCopied(true);
  }

  if (isError) {
    return (
      <ErrorPage
        message="Your account could not be created. Check your connection and try again."
        onRetry={reset}
      />
    );
  }

  return signedInUser && !generatedAccountId ? (
    <Redirect to="/lists" />
  ) : (
    <div className="mx-auto w-full max-w-lg px-6 py-8">
      <section
        aria-labelledby="new-account-heading"
        className="rounded-2xl border border-border bg-card p-7 shadow-card"
      >
        <h1
          id="new-account-heading"
          className="text-lg font-semibold text-heading"
        >
          Create an account
        </h1>
        {generatedAccountId ? (
          <>
            <div className="mt-3 flex items-center justify-between gap-3">
              <p className="font-mono text-2xl font-semibold tracking-wide text-heading">
                {formatAccountId(generatedAccountId)}
              </p>
              <button
                type="button"
                onClick={() => handleCopy(generatedAccountId)}
                className={`${buttonClassName("secondary", "small")} shrink-0 gap-1.5`}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  aria-hidden="true"
                  className="size-4"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75"
                  />
                </svg>
                {isCopied ? "Copied" : "Copy ID"}
              </button>
            </div>
            <p
              role="alert"
              className="mt-4 border-l-4 border-yellow-400 bg-yellow-50 px-4 py-3 text-sm text-heading"
            >
              Save this ID somewhere safe. It is your only way back in: if you
              lose it, you lose your lists.
            </p>
            <Link
              onClick={() => handleContinue(generatedAccountId)}
              href="/lists"
              className={`${buttonClassName()} mt-4`}
            >
              Continue to my lists
            </Link>
          </>
        ) : (
          <>
            <p className="mt-1 text-sm text-label">
              Get a 16-digit ID. It is your login, so keep it somewhere safe.
            </p>
            <button
              type="button"
              onClick={handleGenerate}
              className={`${buttonClassName()} mt-5`}
            >
              Generate a new ID
            </button>
            <p className="mt-5 border-t border-border pt-5 text-sm text-label">
              Already have an ID?{" "}
              <Link href="/" className="font-semibold text-primary">
                Sign in
              </Link>
            </p>
          </>
        )}
      </section>
    </div>
  );
}
