import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.libs.iso_metric_screw_thread import Iso262_MetricScrewThreadSizes
from faebryk.libs.library import L


class PCB_Mount(Module):
    """
    Mounting holes and features for the PCB
    """

    screw_holes = L.list_field(
        3,
        lambda: F.Mounting_Hole(
            diameter=Iso262_MetricScrewThreadSizes.M2,
            pad_type=F.Mounting_Hole.PadType.Pad,
        ),
    )

    def __preinit__(self):
        # ------------------------------------
        #          parametrization
        # ------------------------------------

        # ------------------------------------
        #            pcb layout
        # ------------------------------------
        for hole_i, hole in enumerate(self.screw_holes):
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
