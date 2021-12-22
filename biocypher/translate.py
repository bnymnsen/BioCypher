#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the lookup and storage of entity IDs that are part 
of the BioCypher schema. It is part of the BioCypher python package, 
homepage: TODO.


Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.

Todo: 
    - genericise: standardise input data to BioCypher specifications or, 
        optionally, user specifications.
        - if the database exists, read biocypher info node
        - if newly created, ask for user input (?) as to which IDs to 
            use etc
        - default scenario -> YAML?
        - the consensus representation ("target" of translation) is 
            the literal Biolink class, which is assigned to database
            content using user input for each class to be represented
            in the graph ("source" of translation). currently, 
            implemented by assigning source nomenclature explicitly in
            the schema_config.yaml file ("label_in_input").
    - type checking
    - import ID types from pypath dictionary (later, externalised 
        dictionary)? biolink?
"""

from .create import BioCypherEdge, BioCypherNode
from bmt import Toolkit


class BiolinkAdapter(object):
    """
    Performs various functions to integrate the Biolink ontology.

    Todo:
        - refer to pythonised biolink model from YAML
    """

    def __init__(self, leaves) -> None:
        super().__init__()
        self.leaves = self.translate_leaves_to_biolink(leaves)

    def translate_leaves_to_biolink(self, leaves):
        """
        Translates the graph structure given in the `schema_config.yaml`
        to Biolink-conforming nomenclature.
        """
        t = Toolkit()
        l = []
        for entity in leaves.keys():
            e = t.get_element(entity)  # element name
            if e is not None:
                l.append([entity, e])
            else:
                print("Entity not found:" + entity[0])
                l.append([entity, None])

        return l


# -------------------------------------------
# Create nodes and edges from separate inputs
# -------------------------------------------


def gen_translate_nodes(leaves, id_type_tuples):
    """
    Translates input node representation to a representation that
    conforms to the schema of the given BioCypher graph. For now
    requires explicit statement of node type on pass.

    Args:
        leaves (dict): dictionary detailing the leaves of the hierarchy
            tree representing the structure of the graph; the leaves are
            the entities that will be direct components of the graph,
            while the intermediary nodes are additional labels for
            filtering purposes.
        id_type_tuples (list of tuples): collection of tuples
            representing individual nodes by their unique id and a type
            that is translated from the original database notation to
            the corresponding BioCypher notation.

    """

    # biolink = BiolinkAdapter(leaves)

    for id, type in id_type_tuples:
        path = getpath(leaves, type)

        if path is not None:
            bl_type = path[0]
            yield BioCypherNode(
                node_id=id,
                node_label=bl_type,
                # additional here
            )

        else:
            print("No path for type " + type)


def gen_translate_edges(leaves, src_tar_type_tuples):
    """
    Translates input edge representation to a representation that
    conforms to the schema of the given BioCypher graph. For now
    requires explicit statement of edge type on pass.

    Args:
        leaves (dict): dictionary detailing the leaves of the hierarchy
            tree representing the structure of the graph; the leaves are
            the entities that will be direct components of the graph,
            while the intermediary nodes are additional labels for
            filtering purposes.
        src_tar_type_tuples (list of tuples): collection of tuples
            representing source and target of an interaction via their
            unique ids as well as the type of interaction in the
            original database notation, which is translated to BioCypher
            notation using the `leaves`.

    Todo:
        - id of interactions (now simple concat with "_")
    """

    for src, tar, type in src_tar_type_tuples:
        path = getpath(leaves, type)

        if path is not None:
            bl_type = path[0]
            rep = leaves[bl_type]["represented_as"]

            if rep == "node":
                # TODO update
                node_id = str(src) + "_" + str(tar)
                n = BioCypherNode(
                    node_id=node_id,
                    node_label=bl_type,
                    # additional here
                )
                e_s = BioCypherEdge(
                    source_id=src,
                    target_id=node_id,
                    relationship_label="IS_SOURCE_OF",
                    # additional here
                )
                e_t = BioCypherEdge(
                    source_id=tar,
                    target_id=node_id,
                    relationship_label="IS_TARGET_OF",
                    # additional here
                )
                yield (n, e_s, e_t)

            else:
                edge_label = leaves[bl_type]["label_as_edge"]
                yield BioCypherEdge(
                    source_id=src,
                    target_id=tar,
                    relationship_label=edge_label,
                    # additional here
                )

        else:
            print("No path for type " + type)


def edges_from_pypath(records):
    return BioCypherEdge.create_relationship_list(records)


# quick and dirty replacement functions
# this belongs in translate or in the pypath adapter directly


def getpath(nested_dict, value, prepath=()):
    for k, v in nested_dict.items():
        path = prepath + (k,)
        if v == value:  # found value
            return path
        elif hasattr(v, "items"):  # v is a dict
            p = getpath(v, value, path)  # recursive call
            if p is not None:
                return p
