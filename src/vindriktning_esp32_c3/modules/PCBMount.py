import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.libs.util import times


class PCB_Mount(Module):
    """
    Mounting holes and features for the PCB
    """

    def __init__(self, enabled: bool = True) -> None:
        super().__init__()

        class _IFs(Module.IFS()): ...

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            screw_holes = times(3, lambda: F.Mounting_Hole())

        self.NODEs = _NODEs(self)

        # PCB layout
        for hole_i, hole in enumerate(self.NODEs.screw_holes):
            if hole_i == 0:
                hole.add_trait(
                    F.has_pcb_layout_defined(
                        layout=LayoutAbsolute(
                            F.has_pcb_position.Point(
                                (-6.5, 2.5, 0, F.has_pcb_position.layer_type.NONE)
                            )
                        ),
                    )
                )
            else:
                hole.add_trait(
                    F.has_pcb_layout_defined(
                        layout=LayoutAbsolute(
                            F.has_pcb_position.Point(
                                (
                                    7.5 if hole_i == 1 else -7.5,
                                    69.5,
                                    0,
                                    F.has_pcb_position.layer_type.NONE,
                                )
                            )
                        ),
                    )
                )
