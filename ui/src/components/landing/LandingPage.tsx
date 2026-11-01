import { useState, type SubmitEvent } from "react";
import { Link, Redirect, useLocation } from "wouter";
import { useVerifyAccountMutation } from "../../api/plantgenieApi";
import { setAccountId } from "../../store/accountSlice";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { buttonClassName } from "../shared/buttonClassName";
import ErrorPage from "../shared/ErrorPage";

export default function LandingPage() {
  const [accountId, setAccountIdInput] = useState("");
  const [verifyAccount, { error, reset }] = useVerifyAccountMutation();
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

  const isRejected =
    error !== undefined && "status" in error && error.status === 401;

  if (error && !isRejected) {
    return (
      <ErrorPage
        message="We could not check your account ID. Check your connection and try again."
        onRetry={reset}
      />
    );
  }

  return signedInUser ? (
    <Redirect to="/lists" />
  ) : (
    <div className="mx-auto w-full max-w-lg px-6 py-8">
      <h1 className="text-2xl font-bold text-heading text-center">
        Welcome to PlantGenIE!
      </h1>
      <section
        aria-labelledby="sign-in-heading"
        className="mt-6 rounded-2xl border border-border bg-card p-7 shadow-card"
      >
        <h2 id="sign-in-heading" className="text-lg font-semibold text-heading">
          Sign in
        </h2>
        <p className="mt-1 text-sm text-label">
          No email, no password. Paste the 16-digit ID you saved to get back to
          your lists.
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
          {isRejected && (
            <p role="alert" className="mt-2 text-sm text-red-600">
              That account ID wasn't recognised.
            </p>
          )}
          <button type="submit" className={`${buttonClassName()} mt-4`}>
            Continue
          </button>
        </form>
        <div className="mt-5 border-t border-border pt-5">
          <Link href="/accounts/new" className={buttonClassName("secondary")}>
            New here? Create an account
          </Link>
        </div>
      </section>
    </div>
  );
}
