import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P


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
        # Set crystal parameters based on YST310S datasheet
        xtal = self.mcu.low_speed_crystal_clock.crystal
        xtal.frequency.alias_is(L.Single(32.768 * P.kHz))
        xtal.frequency_tolerance.alias_is(L.Single(20 * P.ppm))
        xtal.frequency_temperature_tolerance.alias_is(L.Single(0.04 * P.ppm))
        xtal.frequency_ageing.alias_is(L.Single(3 * P.ppm))
        xtal.equivalent_series_resistance.alias_is(L.Single(70 * P.kΩ))
        xtal.shunt_capacitance.alias_is(L.Single(1.4 * P.pF))
        xtal.load_capacitance.alias_is(L.Single(12.5 * P.pF))

        # disable current limiting resistor for 70kΩ ESR crystal
        self.mcu.low_speed_crystal_clock.current_limiting_resistor.resistance.constrain_subset(
            L.Range.from_center_rel(0 * P.ohm, 1 * P.percent)
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
