import { Route, Switch } from "wouter";
import Navbar from "./components/Navbar";
import GenePage from "./components/genes/GenePage";
import AddByIdPage from "./components/lists/AddByIdPage";
import ListPage from "./components/lists/ListPage";
import MyListsPage from "./components/lists/MyListsPage";
import BlastPage from "./components/blast/BlastPage";
import BlastResultsPage from "./components/blast/BlastResultsPage";
import Wizard from "./components/wizard/Wizard";
import { useAccountIdSync } from "./store/useAccountIdSync";

function App() {
  useAccountIdSync();

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <main>
        <Switch>
          <Route path="/" component={MyListsPage} />
          <Route path="/blast" component={BlastPage} />
          <Route path="/blast/" component={BlastPage} />
          <Route path="/blast/:jobId" component={BlastResultsPage} />
          <Route path="/lists/new" component={Wizard} />
          <Route path="/lists/:listId/genes/add-by-id" component={AddByIdPage} />
          <Route path="/lists/:listId" component={ListPage} />
          <Route path="/genes/:annotationId/:geneId" component={GenePage} />
        </Switch>
      </main>
    </div>
  );
}

export default App;
