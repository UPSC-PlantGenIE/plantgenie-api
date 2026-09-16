import { Redirect, Route, Switch, useLocation } from "wouter";
import Navbar from "./components/Navbar";
import GenePage from "./components/genes/GenePage";
import LandingPage from "./components/landing/LandingPage";
import AddByIdPage from "./components/lists/AddByIdPage";
import ListPage from "./components/lists/ListPage";
import MyListsPage from "./components/lists/MyListsPage";
import BlastPage from "./components/blast/BlastPage";
import BlastResultsPage from "./components/blast/BlastResultsPage";
import Wizard from "./components/wizard/Wizard";
import { useAccountIdSync } from "./store/useAccountIdSync";
import type { PropsWithChildren } from "react";
import { useAppSelector } from "./store/hooks";

const routePrefixesWithAuthentication = ["/lists"];

const RequireAccount = ({ children }: PropsWithChildren) => {
  const accountId = useAppSelector((state) => state.account.accountId);
  const [location] = useLocation();

  const requiresAccount = routePrefixesWithAuthentication.some((prefix) =>
    location.startsWith(prefix)
  );
  const loggedIn = accountId !== null;

  return requiresAccount && !loggedIn ? <Redirect to="/" /> : children;
};

const App = () => {
  useAccountIdSync();

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <main>
        <RequireAccount>
          <Switch>
            <Route path="/" component={LandingPage} />
            <Route path="/blast" component={BlastPage} />
            <Route path="/blast/" component={BlastPage} />
            <Route path="/blast/:jobId" component={BlastResultsPage} />
            <Route path="/lists" component={MyListsPage} />
            <Route path="/lists/new" component={Wizard} />
            <Route
              path="/lists/:listId/genes/add-by-id"
              component={AddByIdPage}
            />
            <Route path="/lists/:listId" component={ListPage} />
            <Route path="/genes/:annotationId/:geneId" component={GenePage} />
          </Switch>
        </RequireAccount>
      </main>
    </div>
  );
};

export default App;
