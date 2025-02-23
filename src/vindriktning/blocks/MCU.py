import faebryk.library._F as F
from faebryk.core.module import Module


class MCU(Module):
    # TODO: Currently no other way to make a build target out of this
    mcu: F.ESP32_C3_MINI_1_ReferenceDesign

    def __preinit__(self):
        self.mcu.low_speed_crystal_clock.crystal.add(
            F.has_explicit_part.by_supplier(
                supplier_partno="C5213671",
                pinmap={
                    "1": self.mcu.low_speed_crystal_clock.crystal.unnamed[0],
                    "2": self.mcu.low_speed_crystal_clock.crystal.unnamed[1],
                },
            )
        )
        for button in self.get_children_modules(types=F.Button):
            button.add(
                F.has_explicit_part.by_supplier(
                    supplier_partno="C139797",
                    pinmap={
                        "1": button.unnamed[0],
                        "2": button.unnamed[0],
                        "3": button.unnamed[1],
                        "4": button.unnamed[1],
                    },
                )
            )
