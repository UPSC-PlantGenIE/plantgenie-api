## BRANCH DECISIONS: list-title-suggestion

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
