from flask_bauto import AutoBlueprint, dataclass, relationship
from bull_stack import BullStack

#Crop source investigations
class Taxonomy(AutoBlueprint):
    @dataclass
    class Genus:
        name: str
        family: str
        species: relationship = None

    @dataclass 
    class Species:
        genus_id: int
        name: str
        gbif_id: int

    @dataclass
    class Crop:
        species_id: int
        name: str
        description: str = None
        
class CSI(AutoBlueprint):
    @dataclass
    class Project:
        name: str
        description: str = None
        sample: relationship = None
        
    @dataclass
    class Provenance:
        name: str
        polygon: str = None
        description: str = None
        
    @dataclass
    class Sample:
        name: str
        project_id: int
        species_id: int
        provenance_id: int= None
    
    def show_species(self) -> str:
        return 'test'

bs = BullStack(
    __name__,
    [
        Taxonomy(
            enable_crud=True, forensics=True
        ),
        CSI(
            enable_crud=True, url_prefix=False,
            index_page='csi/index.html', forensics=True
        )
    ],
    logo = 'images/Copilot_20250530_143949.png'
)
bs.create_app()

app = bs.app
