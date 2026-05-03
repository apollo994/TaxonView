### Implementation plan of TaxonView
The goal of this plan is to describe the purpose and the implementation startegy of a visualisation tool for genomics resources available for a given taxon

#### Purpose
Visualise the genomics resources available for a give taxon (focus taxon) at increasing taxonomic hierachy. 
In the first implementation the focus taxon corresponds to a species and the resource to be visualise are:
- species itself
- genus
- family
- order
- classe
In the first implementation the resources to visualise are (for each taxon):
- named species
- assembled species
- annotated assemblies

#### Implementation strategy
- the base engine to extract resources available is https://github.com/Cobos-Bioinfo/euka_survey 
- the user input should be the taxonomic identifier of a species
- the algorithm does:
    - check if taxon is species
    - extract information a different taxonomic level for that species (species, genus, family, etc)
    - generate visualisation
##### Visualisation details
- multiple concentric circles, each circle reppresent a taxon
- the size of the circle (radius) is plotted on an horizontal scale
- the size of the circle reppresent the number of named species in the taxon
- the circle is divided in wedges
- the main wedge reppresent the proportion of species with an assembly
- a portion of the assembly wedge had a darker section corresponding to the proportion of annotated assemblies
- the visualisation should be rendered in html  
