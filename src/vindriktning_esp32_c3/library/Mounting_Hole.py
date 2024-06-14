import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_symmetrically import (
    can_attach_to_footprint_symmetrically,
)


class Mounting_Hole(Module):
    def __init__(self, diameter: F.Constant) -> None:
        super().__init__()
        self.diameter = diameter

        # interfaces
        class _IFs(Module.IFS()):
            pin = F.Electrical()

        self.IFs = _IFs(self)

        # TODO make a universal footprint
        self.add_trait(can_attach_to_footprint_symmetrically())
        self.add_trait(
            F.has_defined_footprint(
                F.KicadFootprint("MountingHole:MountingHole_2.1mm", pin_names=[])
            )
        )
        self.add_trait(F.has_designator_prefix_defined("H"))
