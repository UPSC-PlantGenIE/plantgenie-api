import type { BlastHit } from "../../api/plantgenieApi";

const BLOCK_WIDTH = 60;

const residueCount = (aligned: string) => aligned.replaceAll("-", "").length;

interface AlignmentProps {
  hit: BlastHit;
  querySequence: string;
  subjectSequence: string;
}

export default function Alignment({
  hit,
  querySequence,
  subjectSequence,
}: AlignmentProps) {
  const queryDirection = hit.queryEnd >= hit.queryStart ? 1 : -1;
  const subjectDirection = hit.subjectEnd >= hit.subjectStart ? 1 : -1;
  const queryStep = Math.round(
    (Math.abs(hit.queryEnd - hit.queryStart) + 1) / residueCount(querySequence)
  );
  const subjectStep = Math.round(
    (Math.abs(hit.subjectEnd - hit.subjectStart) + 1) /
      residueCount(subjectSequence)
  );

  const blocks = [];
  let queryPosition = hit.queryStart;
  let subjectPosition = hit.subjectStart;

  for (let offset = 0; offset < querySequence.length; offset += BLOCK_WIDTH) {
    const query = querySequence.slice(offset, offset + BLOCK_WIDTH);
    const subject = subjectSequence.slice(offset, offset + BLOCK_WIDTH);
    const match = Array.from(query, (letter, index) =>
      letter === subject[index] ? "|" : " "
    ).join("");
    const queryEnd =
      queryPosition + queryDirection * (residueCount(query) * queryStep - 1);
    const subjectEnd =
      subjectPosition +
      subjectDirection * (residueCount(subject) * subjectStep - 1);

    blocks.push({
      offset,
      query,
      match,
      subject,
      queryStart: queryPosition,
      queryEnd,
      subjectStart: subjectPosition,
      subjectEnd,
    });

    queryPosition = queryEnd + queryDirection;
    subjectPosition = subjectEnd + subjectDirection;
  }

  return (
    <figure
      aria-label="Alignment"
      className="overflow-x-auto font-mono text-xs text-heading"
    >
      {blocks.map((block) => (
        <div key={block.offset} className="mb-4 whitespace-pre last:mb-0">
          <div className="flex gap-3">
            <span className="w-16 shrink-0 text-label">Query</span>
            <span className="w-20 shrink-0 text-right">{block.queryStart}</span>
            <span>{block.query}</span>
            <span>{block.queryEnd}</span>
          </div>
          <div className="flex gap-3">
            <span className="w-16 shrink-0" />
            <span className="w-20 shrink-0" />
            <span>{block.match}</span>
          </div>
          <div className="flex gap-3">
            <span className="w-16 shrink-0 text-label">Subject</span>
            <span className="w-20 shrink-0 text-right">
              {block.subjectStart}
            </span>
            <span>{block.subject}</span>
            <span>{block.subjectEnd}</span>
          </div>
        </div>
      ))}
    </figure>
  );
}
