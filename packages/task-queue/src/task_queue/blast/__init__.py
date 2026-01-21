from typing import Literal

BlastProgram = Literal["blastn", "blastp", "blastx"]

# files stay on the server for 30 mins
BLAST_DATA_SERVER_LIFETIME = 30 * 60
