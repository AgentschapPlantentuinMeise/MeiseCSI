import os
from flask_bauto import AutoBlueprint, dataclass, render_template
from flask_bauto.types import url
from bull_stack import BullStack
from typing import Annotated
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

        def __repr__(self):
            return f"{self.genus.name} {self.name}"

    @dataclass
    class Crop:
        species_id: int
        name: str
        description: str = None

class Services(AutoBlueprint):
    @dataclass
    class RequestQuote:
        project: str
        description: str
        samples: int
        icpoes: bool
        icpms: bool
        isotopes: bool
        #customer: int
        #offer_send: bool = False

    @dataclass
    class Order:
        request_quote_id: int
        accept_conditions: bool
        
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
        file: Annotated[Path,{'storage_location':'batch_output'}] = None
        annotation: str = None
        
    @dataclass
    class Provenance:
        name: str
        polygon: str = None
        description: str = None

        def __repr__(self):
            return self.name
    
    @dataclass
    class Sample:
        name: str
        batch_id: int
        species_id: int
        provenance_id: int = None
        weight: float = None
        volume: float = None
        mad_pos: str = None
        oes_pos: str = None
        sample_output: list[int] = None

    @dataclass
    class SampleOutput:
        sample_id: int
        file: Annotated[Path,{'storage_location':'sample_output'}] = None
        annotation: str = None

class Documentation(AutoBlueprint):
    @dataclass
    class Protocol:
        name: str
        version: str
        responsible: str
        description: Annotated[str,{'min_size':250}]
        agenda: list[int] = None
        _view_function = 'show_protocol'

    @dataclass
    class Agenda:
        protocol_id: int
        resource: str
        url: url

    def index(self):
        protocols = {
            p.name:p for p in self.query.protocol.all()
        }
        return render_template(
            'documentation/protocols.html',
            title='Standard operating protocols',
            protocols=protocols.values()
        )
        
    def show_protocol(self, protocol_id) -> '/protocol/view/<protocol_id>':
        import markdown
        protocol = self.query.protocol.get_or_404(protocol_id)
        return render_template(
            'documentation/protocol.html',
            title = protocol.name.capitalize(),
            page = markdown.markdown(
                protocol.description,
                extensions=['extra', 'nl2br', 'sane_lists']
            ),
            agendas = protocol.agenda_list
        )
         
bs = BullStack(
    __name__,
    [
        Taxonomy(enable_crud=True, forensics=True),
        Services(enable_crud=True, forensics=False),
        CSI(
            enable_crud=True, url_prefix=False,
            fair_data=True, forensics=True,
            index_page='csi/index.html'
        ),
        Documentation(enable_crud=True, forensics=True, index_menu='Overview SOPs')
    ],
    logo='images/Copilot_20250530_143949.png',
    sql_db_uri='sqlite:///mcsi.db',
    admin_init_password=os.getenv('BADMIN_INIT','ton')
)
bs.create_app()

app = bs.app
