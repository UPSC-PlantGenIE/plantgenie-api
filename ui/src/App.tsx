import { Route, Switch } from "wouter";
import Navbar from "./components/Navbar";
import GenePage from "./components/genes/GenePage";
import AddByIdPage from "./components/lists/AddByIdPage";
import ListPage from "./components/lists/ListPage";
import MyListsPage from "./components/lists/MyListsPage";
import Wizard from "./components/wizard/Wizard";

function App() {
  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <main>
        <Switch>
          <Route path="/" component={MyListsPage} />
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
