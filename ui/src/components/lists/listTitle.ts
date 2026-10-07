// "dehydration in Pinus sylvestris" -> "dehydration". Names that don't
// follow "<something> in <species>" have no reusable topic.
export function titleTopic(listName: string, taxonName: string) {
  const suffix = ` in ${taxonName}`;
  if (!listName.endsWith(suffix)) return undefined;
  return listName.slice(0, -suffix.length).trim() || undefined;
}
