import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useVerifyAccountMutation } from "../api/plantgenieApi";
import { setAccountId } from "./accountSlice";
import type { RootState } from ".";

const STORAGE_KEY = "accountId";

export function useAccountIdSync() {
  const dispatch = useDispatch();
  const accountId = useSelector((s: RootState) => s.account.accountId);
  const [verifyAccount] = useVerifyAccountMutation();

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;
    verifyAccount(stored)
      .unwrap()
      .then(
        () => dispatch(setAccountId(stored)),
        () => {}
      );
  }, [dispatch, verifyAccount]);

  useEffect(() => {
    if (accountId) localStorage.setItem(STORAGE_KEY, accountId);
  }, [accountId]);
}
