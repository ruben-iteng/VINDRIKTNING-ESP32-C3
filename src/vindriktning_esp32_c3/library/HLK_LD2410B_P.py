from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import (
    has_defined_type_description,
)
from faebryk.library.UART_Base import UART_Base


class HLK_LD2410B_P(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = ElectricPower()
            uart = UART_Base()
            out = ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "5": x.power.NODEs.hv,
                    "4": x.power.NODEs.lv,
                    "3": x.uart.NODEs.rx.NODEs.signal,
                    "2": x.uart.NODEs.tx.NODEs.signal,
                    "1": x.out.NODEs.signal,
                }
            )
        )

        self.add_trait(has_defined_type_description("U"))
