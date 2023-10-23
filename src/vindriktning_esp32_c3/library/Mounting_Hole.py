from faebryk.core.core import Module
from faebryk.library.has_defined_footprint import has_defined_footprint
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)


class Mounting_Hole(Module):
    def __init__(self, diameter: float) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            ...

        self.IFs = _IFs(self)

        # self.add_trait(has_defined_footprint(MountingHole:MountingHole_2.1mm))
        self.add_trait(has_defined_type_description("H"))
