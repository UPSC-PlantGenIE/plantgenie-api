## BRANCH DECISIONS: feature/semantic-search-core

2026-10-06: Add semantic search option as a way to add genes to the list. 
-Context: The user can add genes by clicking on the "Search genes" button. A search engine appears that is available for 5 species: arath, betpe, pinsy, picab and potra. 
-Decision: Use of an AI model "FremyCompany/BioLORD-2023" to compute the embeddings. 
-Alternatives considered: The model "mixedbread-ai/mxbai-embed-large-v1" already tested and seemed inefficient to identify biological significance. 
-Consequences: The applied model has a better ability to connect biological similarities. 

2026-10-07: Sixth species added: Tieton as Prunus (Pruav). 
Context: The semantic search feature was unavailable for Prunus, as the corresponding data were not found.
Decision: After consulation with supervisor matched the "tieton" abbreviation to "purav".
Alternatives considered: -
Consequences: Feature available for Prunus too. 

2026-10-07: Data files adapted 
Context: The semantic search draws data from 3 file types: embeddings.npy, id.npy and source.csv. The source.csv file is the one used to compute the embeddings. However, the gene ids and descriptions already exist in Neo4j. 
Desicions: The genes descriptions are now drawn from Neo4J and embedding files are renamed to match the api's species abbreviaton (tieton -> pruav, bepen -> betpe).
Alternatives considered: Keeping the .csv files as source of description polutes the storage. 
Consequences: Risk of mismatch betweeen the embeddings and updated descriptions, but less storage space and less files. 

2026-10-13: Torch change, python dependencies fix
Context: 1) PyTorch with CUDA added to the image makes it large. 2) inaccurate dependencies  
Decision: 1) Torch comes from the CPU-only PyTorch index (pytorch-cpu), which keeps the image much smaller. 2) numpy>=2.0 is no longer listed, sentence-transformers and torch are now regular dependencies
Alternatives considered: -
Consequences: Proper configuration and no uneccesary script load. 
