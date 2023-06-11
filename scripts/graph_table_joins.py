"""
Require first to generate file "joins_frequency.csv"
& grep -v "Function()" joins_frequency.csv > joins_frequency_no_func.csv

Generate a pdf file with a graph of all tables + edges between
"""
import os

import graphviz
import pandas as pd
import sys


def graph_table_joins(table_prefix=""):
    df_raw = pd.read_csv(
        os.path.join(os.getenv("DATA_DIR"), "parse_sql", "joins_frequency.csv")
    )

    df_raw = df_raw[df_raw["left_table"] < df_raw["right_table"]]  # deduplicate
    df_raw = df_raw[
        df_raw["left_table"].str.startswith(table_prefix) |
        df_raw["right_table"].str.startswith(table_prefix)
    ]

    df_raw["column_equality"] = (df_raw["left_col"] + " = " + df_raw["right_col"]).str.lower()
    df_raw = df_raw[
        ["left_table", "right_table", "column_equality", "frequency"]
    ].groupby(
        ["left_table", "right_table"], as_index=False
    ).agg({"column_equality": list, "frequency": sum}).assign(
        column_equality=lambda _df: _df["column_equality"].map("\n".join)
    )#.query("frequency > 2")

    node_frequency = pd.concat([
        df_raw.rename(columns={"left_table": "node"}),
        df_raw.rename(columns={"right_table": "node"})
    ], ignore_index=True)[
        ["node", "frequency"]
    ].groupby("node").agg({"frequency": "sum"}).to_dict()["frequency"]

    nodes_in_order = sorted(
        node_frequency.keys(),
        key=node_frequency.get,
        reverse=True
    )

    # Create graph
    file_suffix = table_prefix.strip("_").upper() or "ALL"
    f = graphviz.Digraph('bigquery', filename=f"bigquery_{file_suffix}.gv")

    # Create nodes : double cicle for the 10 most common tables
    for table_name in nodes_in_order[:10]:
        create_node(f, table_name, shape='doubleoctagon', penwidth="3")
    for table_name in nodes_in_order[10:]:
        create_node(f, table_name, shape='circle')

    # create edges
    for idx, row in df_raw.iterrows():
        f.edge(row["left_table"], row["right_table"], row["column_equality"])

    f.view()


def create_node(f, node_name: str, **kwargs):
    if node_name.lower().startswith("ods_"):
        color = "beige"
    elif node_name.lower().startswith("dw_"):
        color = "aquamarine"
    elif node_name.lower().startswith("dm_"):
        color = "firebrick1"
    elif node_name.lower().startswith("effy_store"):
        color = "blue2"
    else:
        color = "white"
    # color (circle), fillcolor (background), fontcolor (text)
    # penwidth : > 0, default 1.0
    f.node(node_name, color=color, **kwargs)


if __name__ == '__main__':
    table_prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    graph_table_joins(table_prefix.lower())
