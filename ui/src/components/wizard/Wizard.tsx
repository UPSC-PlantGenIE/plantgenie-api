import { useEffect } from "react";
import { Redirect, Route, Switch } from "wouter";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { reset } from "../../store/wizardSlice";
import ListName from "./panels/ListName";
import TaxonSelector from "./panels/TaxonSelector";
import GenomeSelector from "./panels/GenomeSelector";

export default function Wizard() {
  const dispatch = useAppDispatch();
  const taxonId = useAppSelector((s) => s.wizard.taxonId);
  const annotationId = useAppSelector((s) => s.wizard.annotationId);

  useEffect(() => {
    return () => {
      dispatch(reset());
    };
  }, [dispatch]);

  const firstIncompleteStep = !taxonId
    ? "~/lists/new"
    : !annotationId
      ? "~/lists/new/genome"
      : null;

  return (
    <Switch>
      <Route path="/" component={TaxonSelector} />
      <Route path="/genome">
        {taxonId ? <GenomeSelector /> : <Redirect to="~/lists/new" replace />}
      </Route>
      <Route path="/details">
        {firstIncompleteStep ? (
          <Redirect to={firstIncompleteStep} replace />
        ) : (
          <ListName />
        )}
      </Route>
      <Route>
        <Redirect to="~/lists/new" replace />
      </Route>
    </Switch>
  );
}
