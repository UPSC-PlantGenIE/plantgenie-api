import { useAppSelector } from "../../store/hooks";
import ListName from "./panels/ListName";
import TaxonSelector from "./panels/TaxonSelector";
import GenomeSelector from "./panels/GenomeSelector";

export default function Wizard() {
  const step = useAppSelector((s) => s.wizard.step);

  return (
    <div className="w-screen overflow-hidden">
      <div
        className="flex transition-transform duration-300 ease-in-out"
        style={{
          width: "300vw",
          transform: `translateX(-${(step - 1) * 100}vw)`,
        }}
      >
        <ListName />
        <TaxonSelector />
        <GenomeSelector />
      </div>
    </div>
  );
}
