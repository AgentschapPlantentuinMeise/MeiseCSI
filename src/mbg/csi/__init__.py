from flask_bauto import AutoBlueprint, BullStack, dataclass

#Crop source investigations
class CSI(AutoBlueprint):
    @dataclass
    class Genus:
        name: str
        family: str
        #species_rel: relationship = relationship('Species', backref="genus")

    @dataclass 
    class Species:
        genus_id: int
        name: str

    @dataclass
    class Project:
        name: str
        description: str = None
        #samples: relationship

    @dataclass
    class Provenance:
        name: str
        polygon: str = None
        description: str = None
        
    @dataclass
    class Sample:
        name: str
        species_id: int
        provenance_id: int= None
    
    def show_species(self) -> str:
        return 'test'

bs = BullStack(__name__, [CropSourceInvestigations(enable_crud=True)])

app = bs.app
