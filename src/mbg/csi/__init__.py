import os
from flask_bauto import AutoBlueprint, dataclass
from bull_stack import BullStack
from pathlib import Path

#Crop source investigations
class Taxonomy(AutoBlueprint):
    @dataclass
    class Genus:
        name: str
        family: str
        species: list[int] = None

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
        batch: list[int] = None

    @dataclass
    class Batch: # A batch of samples that undergo the same analysis protocols
        project_id: int
        sample: list[int] = None
        batch_process_step: list[int] = None

    @dataclass
    class BatchProcessStep:
        batch_id: int
        protocol_id: int
        batch_output: list[int] = None

    @dataclass
    class BatchOutput:
        batch_process_step_id: int
        file: Path = None
        annotation: str = None
        
    @dataclass
    class Provenance:
        name: str
        polygon: str = None
        description: str = None
    
    @dataclass
    class Sample:
        name: str
        batch_id: int
        species_id: int
        provenance_id: int= None
        sample_output: list[int] = None

    @dataclass
    class SampleOutput:
        sample_id: int
        file: Path = None
        annotation: str = None

class Documentation(AutoBlueprint):
    @dataclass
    class Protocol:
        name: str
        description: str
        _view_function = 'show_protocol'

    def show_protocol(self, protocol_id) -> str:
        return 'test'
         
bs = BullStack(
    __name__,
    [
        Taxonomy(enable_crud=True, forensics=True),
        CSI(
            enable_crud=True, url_prefix=False, forensics=True,
            index_page='csi/index.html', logo='static/Copilot_20250530_143949.png'
        ),
        Documentation(enable_crud=True, forensics=True)
    ],
    sql_db_uri='sqlite:///mcsi.db',
    admin_init_password=os.getenv('BADMIN_INIT','ton')
)
bs.create_app()

app = bs.app
