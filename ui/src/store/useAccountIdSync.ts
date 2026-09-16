import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useVerifyAccountMutation } from "../api/plantgenieApi";
import { clearAccountId } from "./accountSlice";
import type { RootState } from ".";

const STORAGE_KEY = "accountId";

export function useAccountIdSync() {
  const dispatch = useDispatch();
  const accountId = useSelector((s: RootState) => s.account.accountId);
  const [verifyAccount] = useVerifyAccountMutation();

  useEffect(() => {
    if (!accountId) return;

    verifyAccount(accountId)
      .unwrap()
      .catch(() => {
        dispatch(clearAccountId());
        localStorage.removeItem(STORAGE_KEY);
      });
  }, [dispatch, verifyAccount, accountId]);

  useEffect(() => {
    if (accountId) localStorage.setItem(STORAGE_KEY, accountId);
  }, [accountId]);
}
