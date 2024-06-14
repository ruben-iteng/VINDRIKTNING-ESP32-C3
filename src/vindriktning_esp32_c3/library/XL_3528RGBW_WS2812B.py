import faebryk.library._F as F
from faebryk.core.core import Module


class XL_3528RGBW_WS2812B(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            do = F.ElectricLogic()
            di = F.ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            F.can_attach_to_footprint_via_pinmap(
                {
                    "2": x.power.IFs.lv,
                    "1": x.di.IFs.signal,
                    "3": x.power.IFs.hv,
                    "4": x.do.IFs.signal,
                }
            )
        )

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))

        self.add_trait(F.has_designator_prefix_defined("F.LED"))

        # Add bridge trait
        self.add_trait(F.can_bridge_defined(x.di, x.do))
