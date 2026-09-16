import { useAppDispatch, useAppSelector } from "../store/hooks";
import { clearAccountId } from "../store/accountSlice";
import { useLocation } from "wouter";

const LogOutIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    className="size-4"
    aria-hidden="true"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9"
    />
  </svg>
);

// const UserIcon = () => (
//   <svg
//     xmlns="http://www.w3.org/2000/svg"
//     fill="none"
//     viewBox="0 0 24 24"
//     strokeWidth={1.5}
//     stroke="currentColor"
//     className="size-6"
//   >
//     <path
//       strokeLinecap="round"
//       strokeLinejoin="round"
//       d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
//     />
//   </svg>
// );

export default function Navbar() {
  const accountId = useAppSelector((state) => state.account.accountId);
  const dispatch = useAppDispatch();
  const [, setLocation] = useLocation();

  const handleLogOut = () => {
    dispatch(clearAccountId());
    setLocation("/");
  };

  return (
    <header className="h-14 w-full border-b border-border shadow-nav bg-upsc-blue">
      <div className="flex h-full items-center px-6">
        <span className="text-2xl font-bold text-white">🌿 PlantGenIE</span>
        {accountId ? (
          <div className="flex ml-auto items-center gap-2">
            <p className="text-white font-bold text-xs">{accountId}</p>
            <button
              type="button"
              onClick={handleLogOut}
              aria-label="Log out"
              className="bg-upsc-green text-white text-xs rounded-sm py-1 px-2"
            >
              <LogOutIcon />
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
