"""
TODO: Explain file
"""

import logging
import sys
from pathlib import Path

import faebryk.libs.picker.lcsc as lcsc
import typer
from faebryk.core.util import get_all_modules
from faebryk.exporters.bom.jlcpcb import write_bom_jlcpcb
from faebryk.exporters.esphome.esphome import make_esphome_config
from faebryk.exporters.pcb.kicad.artifacts import (
    export_dxf,
    export_gerber,
    export_glb,
    export_pick_and_place,
    export_step,
)
from faebryk.exporters.pcb.pick_and_place.jlcpcb import (
    convert_kicad_pick_and_place_to_jlcpcb,
)
from faebryk.exporters.visualize.graph import render_matrix
from faebryk.libs.app.erc import simple_erc
from faebryk.libs.app.kicad_netlist import write_netlist
from faebryk.libs.app.parameters import replace_tbd_with_any
from faebryk.libs.logging import setup_basic_logging
from faebryk.libs.picker.picker import pick_part_recursively
from vindriktning_esp32_c3.app import SmartVindrikting
from vindriktning_esp32_c3.pcb import transform_pcb
from vindriktning_esp32_c3.pickers import pick

# logging settings
logger = logging.getLogger(__name__)


def main(
    visualize_graph: bool = False,
    pcb_transform: bool = True,
    export_netlist: bool = True,
    export_pcba_artifacts: bool = False,
    export_esphome_config: bool = False,
):
    # paths --------------------------------------------------
    build_dir = Path("./build")
    faebryk_build_dir = build_dir.joinpath("faebryk")
    faebryk_build_dir.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).parent.parent.parent
    netlist_path = faebryk_build_dir.joinpath("faebryk.net")
    kicad_prj_path = root.joinpath("source")
    pcbfile = kicad_prj_path.joinpath("main.kicad_pcb")
    esphome_path = build_dir.joinpath("esphome")
    esphome_config_path = esphome_path.joinpath("esphome.yaml")
    manufacturing_artifacts_path = build_dir.joinpath("manufacturing")
    cad_path = build_dir.joinpath("cad")

    lcsc.BUILD_FOLDER = build_dir
    lcsc.LIB_FOLDER = root.joinpath("libs")

    # graph --------------------------------------------------
    logger.info("Make app")
    try:
        sys.setrecursionlimit(20000)  # TODO needs optimization
        app = SmartVindrikting()
    except RecursionError:
        logger.error("RECURSION ERROR ABORTING")
        return
    logger.info("Build graph")
    G = app.get_graph()

    # visualize ----------------------------------------------
    if visualize_graph:
        logger.info("Visualize graph")
        render_matrix(
            G.G,
            nodes_rows=[],
            depth=1,
            show_full=True,
            show_non_sum=False,
        ).show()

    # fill unspecified parameters ----------------------------
    logger.info("Filling unspecified parameters")
    import faebryk.libs.app.parameters as p_mod

    lvl = p_mod.logger.getEffectiveLevel()
    p_mod.logger.setLevel(logging.DEBUG)
    replace_tbd_with_any(app, recursive=True)
    p_mod.logger.setLevel(lvl)

    # pick parts ---------------------------------------------
    logger.info("Picking parts")
    pick_part_recursively(app, pick)

    # simple ERC check ---------------------------------------
    simple_erc(G)

    # netlist ------------------------------------------------
    if export_netlist:
        logger.info(f"Writing netlist to {netlist_path}")
        write_netlist(G, netlist_path, use_kicad_designators=True)

    # pcb ----------------------------------------------------
    if pcb_transform:
        logger.info("Transform PCB")
        transform_pcb(pcb_file=pcbfile, graph=G, app=app)
    # ---------------------------------------------------------

    # generate pcba manufacturing and other artifacts ---------
    if export_pcba_artifacts:
        logger.info("Exporting PCBA artifacts")
        write_bom_jlcpcb(
            get_all_modules(app),
            manufacturing_artifacts_path.joinpath("jlcpcb_bom.csv"),
        )
        export_step(pcbfile, step_file=cad_path.joinpath("pcba.step"))
        export_glb(pcbfile, glb_file=cad_path.joinpath("pcba.glb"))
        export_dxf(pcbfile, dxf_file=cad_path.joinpath("pcba.dxf"))
        export_gerber(
            pcbfile, gerber_zip_file=manufacturing_artifacts_path.joinpath("gerber.zip")
        )
        pnp_file = manufacturing_artifacts_path.joinpath("pick_and_place.csv")
        export_pick_and_place(pcbfile, pick_and_place_file=pnp_file)
        convert_kicad_pick_and_place_to_jlcpcb(
            pnp_file,
            manufacturing_artifacts_path.joinpath("jlcpcb_pick_and_place.csv"),
        )

    # esphome config -----------------------------------------
    if export_esphome_config:
        logger.info("Generating esphome config")
        esphome_config = make_esphome_config(G)
        esphome_config_path.write_text(esphome_config, encoding="utf-8")


if __name__ == "__main__":
    setup_basic_logging()
    typer.run(main)
