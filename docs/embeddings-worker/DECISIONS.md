## BRANCH DECISIONS: feature/embeddings-worker

2026-10-12: New feature: Embeddings worker for online automatic update between database and embeddings. 
Context: Exporting the data, manually runnning the computation of the annotation embeddings and using it as a source for result retrieval for the semantic search feature causes several issues. The embeddings do not follow the database's updates, it takes time to update manually and the api is not reproducible without the .npy files. 
Decision: embeddings_worker.py is the new backend feature that computes the descriptions of the genes on spots and stays online to check for updates every 5 minutes. The semantic search feature now reads from Neo4J instead of .npy files. 
Alternatives considered: Keeping the .npy files (drift risk, extra storage, ~all embeddings in API memory). Running the worker continuously (keeps the model in memory all the time for rare description changes).
Consequences: API start-up no longer loads embedding matrices, only the model. 

2026-10-13: Offline embeddings worker (change)
Context: An embeddings worker was created to keep track of changes online as a new service. However it adds unecessary weight on the services since the database will not require frequent changes.
Decision: The embeddings worker will be offline and has to be loaded (run) only when there are changes in the database. The variables that kept track of changes were kept, so that embeddings are only recomputed for the changes instead of rewriting all vectors. 
Alternatives considered: The variables could be deleted along, but the computation would take significantly more time for the whole database. 
Consequences: Developers have to run the script manually to keep the semantic feature updated with the database.
