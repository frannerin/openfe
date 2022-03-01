# This code is part of OpenFE and is licensed under the MIT license.
# For details, see https://github.com/OpenFreeEnergy/openfe

import click
from openfecli import OFECommandPlugin
from openfecli.parameters import MOL, MAPPER, OUTPUT_FILE_AND_EXT


def allow_two_molecules(ctx, param, value):
    """click callback to require that --mol is specified exactly twice"""
    if len(value) != 2:
        raise click.BadParameter("Must specify --mol exactly twice.")
    return value


@click.command(
    "atommapping",
    short_help="Check the atom mapping of a given pair of ligands"
)
@MOL.parameter(multiple=True, callback=allow_two_molecules, required=True,
               help=MOL.kwargs['help'] + " Must be specified twice.")
@MAPPER.parameter(required=True)
@OUTPUT_FILE_AND_EXT.parameter(
    help=OUTPUT_FILE_AND_EXT.kwargs['help'] + " (PNG format)"
)
def atommapping(mol, mapper, output):
    """
    This provides tools for looking at a specific atommapping.
    """
    # note that the text of the docstring will be the help when you run
    # `openfe atommapping --help`.
    mol1_str, mol2_str = mol
    mol1 = MOL.get(mol1_str)
    mol2 = MOL.get(mol2_str)
    mapper_cls = MAPPER.get(mapper)
    mapper_obj = mapper_cls()
    file, ext = OUTPUT_FILE_AND_EXT.get(output)
    if file:
        atommapping_visualize_main(mapper_obj, mol1, mol2, file, ext)
    else:
        atommapping_print_dict_main(mapper_obj, mol1, mol2)


def generate_mapping(mapper, mol1, mol2):
    """Utility method to extract a single mapping from a mapper.

    Parameters
    ----------
    mapper : :class:`.AtomMapper`
        the mapper to use to generate the mapping
    mol1, mol2 : :class:`.Molecule`
        molecules to map between

    Returns
    ------
    :class:`.AtomMapping` :
        the mapping generated by the mapper; errors if there is not exactly
        one mapping generated
    """
    mappings = list(mapper.suggest_mappings(mol1, mol2))
    if len(mappings) != 1:
        raise click.UsageError(
            f"Found {len(mappings)} mappings; this command requires a mapper "
            "to provide exactly 1 mapping"
        )
    return mappings[0]


def atommapping_print_dict_main(mapper, mol1, mol2):
    """Main function for generating and printing out the mapping"""
    mapping = generate_mapping(mapper, mol1, mol2)
    print(mapping.mol1_to_mol2)


def atommapping_visualize_main(mapper, mol1, mol2, file, ext):
    from rdkit.Chem import Draw
    from openfe.utils import visualization

    mapping = generate_mapping(mapper, mol1, mol2)
    ext_to_artist = {
        "png": Draw.rdMolDraw2D.MolDraw2DCairo(600, 300, 300, 300),
    }
    try:
        artist = ext_to_artist[ext]
    except KeyError:
        raise click.BadParameter(
            f"Unknown file format: '{ext}'. The following formats are "
            "supported: " + ", ".join([f"'{ext}'" for ext in ext_to_artist])
        )

    contents = visualization.draw_mapping(mapping.mol1_to_mol2,
                                          mapping.mol1.to_rdkit(),
                                          mapping.mol2.to_rdkit(), d2d=artist)

    file.write(contents)


PLUGIN = OFECommandPlugin(
    command=atommapping,
    section="Setup",
    requires_ofe=(0, 0, 1),
)
