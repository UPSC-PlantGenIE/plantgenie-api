import { useState, type SubmitEvent } from "react";
import { Link, Redirect, useLocation } from "wouter";
import {
  useCreateAccountMutation,
  useVerifyAccountMutation,
} from "../../api/plantgenieApi";
import { setAccountId } from "../../store/accountSlice";
import { useAppDispatch, useAppSelector } from "../../store/hooks";

function formatAccountId(accountId: string) {
  return accountId.match(/.{1,4}/g)?.join(" ") ?? accountId;
}

export default function LandingPage() {
  const [accountId, setAccountIdInput] = useState("");
  const [generatedAccountId, setGeneratedAccountId] = useState<string | null>(
    null
  );
  const [isCopied, setIsCopied] = useState(false);
  const [verifyAccount, { isError }] = useVerifyAccountMutation();
  const [createAccount] = useCreateAccountMutation();
  const dispatch = useAppDispatch();
  const signedInUser = useAppSelector((state) => state.account.accountId);
  const [, setLocation] = useLocation();

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedAccountId = accountId.replace(/\s/g, "");

    verifyAccount(trimmedAccountId)
      .unwrap()
      .then(() => {
        dispatch(setAccountId(trimmedAccountId));
        setLocation("/lists");
      })
      .catch(() => {});
  };

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

  return signedInUser && !generatedAccountId ? (
    <Redirect to="/lists" />
  ) : (
    <div className="mx-auto w-full max-w-3xl px-6 py-8">
      <h1 className="text-2xl font-bold text-heading text-center">
        Welcome to PlantGenIE!
      </h1>
      <div className="grid md:grid-cols-2 sm:grid-cols-1 gap-x-2">
        <section
          id="returning-user"
          aria-labelledby="returning-user-heading"
          className="rounded-2xl border border-border bg-card p-7 shadow-card"
        >
          <h2
            id="returning-user-heading"
            className="text-lg font-semibold text-heading"
          >
            Returning User?
          </h2>
          <p className="mt-1 text-sm text-label">
            No email, no password. Paste the 16-digit ID you saved to get back
            to your lists.
          </p>
          <form onSubmit={handleSubmit} className="mt-5">
            <label
              htmlFor="account-id"
              className="block text-xs font-medium text-label"
            >
              Account ID
            </label>
            <input
              id="account-id"
              value={accountId}
              placeholder="1234 5678 9012 3456"
              onChange={(event) => setAccountIdInput(event.target.value)}
              className="mt-1 h-11 w-full rounded-lg border border-border bg-card px-3 text-sm text-heading"
            />
            {isError && (
              <p role="alert" className="mt-2 text-sm text-red-600">
                That account ID wasn't recognised.
              </p>
            )}
            <button
              type="submit"
              className="mt-4 h-11 rounded-lg bg-primary px-4 text-sm font-medium text-white"
              disabled={generatedAccountId !== null}
            >
              Continue
            </button>
          </form>
        </section>
        <section
          id="new-account-card"
          aria-labelledby="new-account-heading"
          className="rounded-2xl border border-border bg-card p-7 shadow-card"
        >
          <h2
            id="new-account-heading"
            className="text-lg font-semibold text-heading"
          >
            First time here?
          </h2>
          {generatedAccountId ? (
            <>
              <div className="mt-3 flex items-center justify-between gap-3">
                <p className="font-mono text-2xl font-semibold tracking-wide text-heading">
                  {formatAccountId(generatedAccountId)}
                </p>
                <button
                  type="button"
                  onClick={() => handleCopy(generatedAccountId)}
                  className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-sm font-medium text-label"
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
                className="mt-4 inline-flex h-11 items-center rounded-lg bg-primary px-4 text-sm font-medium text-white"
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
                className="mt-5 h-11 rounded-lg bg-primary px-4 text-sm font-medium text-white"
              >
                Generate a new ID
              </button>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
