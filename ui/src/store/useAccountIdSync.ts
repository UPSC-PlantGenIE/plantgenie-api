import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { setAccountId } from "./accountSlice";
import type { RootState } from ".";

const STORAGE_KEY = "accountId";

export function useAccountIdSync() {
  const dispatch = useDispatch();
  const accountId = useSelector((s: RootState) => s.account.accountId);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) dispatch(setAccountId(stored));
  }, [dispatch]);

  useEffect(() => {
    if (accountId) localStorage.setItem(STORAGE_KEY, accountId);
  }, [accountId]);
}
