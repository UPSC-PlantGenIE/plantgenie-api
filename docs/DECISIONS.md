##BRANCH DECISIONS

2026-10-06: Add semantic search option as a way to add genes to the list. 
-Context: The user can add genes by clicking on the "Search genes" button. A search engine appears that is available for 5 species: arath, betpe, pinsy, picab and potra. 
-Decision: Use of an AI model "FremyCompany/BioLORD-2023" to compute the embeddings. 
-Alternatives considered: The model "mixedbread-ai/mxbai-embed-large-v1" already tested and seemed inefficient to identify biological significance. 
-Consequences: The applied model has a better ability to connect biological similarities. 


2026-10-07: Several buttons added for a friendlier interface. 
Context: The list interface was missing the following buttons: 1) Create a new list, 2) multiple selection of genes 3) Rename the list on spot 4) Save the list 5) Go back to home page of lists 6) Save the list 7) Network graph (incoming feature). 
Decision: All the above buttons mentioned were added. Export button was moved to the bottom. 
Alternatives considered: Button "Save list" can be avoided, as the list is automatically saved upon exiting, but this button gives a sense of security to the user. 
Consequences: 

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

2026-10-07: Example title fix.
Context: To create a list, 1) click "+New list", 2) select a taxon, 3) Add a title and optionally a description.  For the title an example appears "Drought-response TFs in Pinus sylvestris". The example title species did not follow the selected species, it is the same regardless the species.
Decision: It is now correspondent to the selected taxon. Extra addition: The user can click in the title and tab to autofill accept the example title. The example title can adapt if these conditions are met: 1. The user has at least one more saved list 2. The user creates a new list with a different species 3. Title format is "<something> in <species>". Outcome: The example title of the new list is the same <something> in the different species selected. 
Alternatives considered: Keeping it simpler would be also okay, but less fancy or/and slower. 
Consequences: User can save up some seconds of effort by tab-ing the titles if they are running comparison of the same genes across species. 


2026-10-07: Follow-up formating of autofilling search example respective to title example. 
Context: The semantic search example promt stayed the same no matter the list title. 
Decision: The example changes according to the title. Condition: Format title is "<something> in <species>". The user can tab the example to autofill it. 
Alternatives considered: - 
Consequences: Easier and faster search that follows the title-theme. 


2026-10-07: Fix- Gene information page "Go back to My Lists button.  
Context: After clicking on a gene added in the list the user can see all the informations about this gene. There is a button "Back to My Lists" and it takes the user to all the lists instead of the list where the gene was. 
Decision: Changed the button to "Back to list". 
Alternatives considered: -
Consequences: Removes the inconvenience of exiting the gene list the user was working on. 



2026-10-12: New feature: Embeddings worker for online automatic update between database and embeddings. 
Context: Exporting the data, manually runnning the computation of the annotation embeddings and using it as a source for result retrieval for the semantic search feature causes several issues. The embeddings do not follow the database's updates, it takes time to update manually and the api is not reproducible without the .npy files. 
Decision: embeddings_worker.py is the new backend feature that computes the descriptions of the genes on spots and stays online to check for updates every 5 minutes. The semantic search feature now reads from Neo4J instead of .npy files. 
Alternatives considered: Keeping the .npy files (drift risk, extra storage, ~all embeddings in API memory). Running the worker continuously (keeps the model in memory all the time for rare description changes).
Consequences: API start-up no longer loads embedding matrices, only the model. 




(Form: 
2026- - : Title
Context: Problem
Decision: Solution
Alternatives considered: Alt solution rejected
Consequences: result - justification
)