CREATE TABLE IF NOT EXISTS gene_lists (
    list_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    annotation_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gene_list_members (
    list_id TEXT NOT NULL,
    gene_id TEXT NOT NULL,
    added_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (list_id, gene_id)
);
