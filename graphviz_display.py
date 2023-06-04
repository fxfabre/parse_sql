import graphviz
import pandas as pd
import sys


def main(table_prefix=""):
    df_raw = pd.read_csv("joins_frequency_no_func.csv")

    df_raw = df_raw.assign(
        left=lambda _df: _df["join_condition"].map(
            lambda join: join.split("=")[0].strip().split(":")[0]
        ),
        right=lambda _df: _df["join_condition"].map(
            lambda join: join.split("=")[1].strip().split(":")[0]
        )
    )

    #df_raw = df_raw[df_raw["left"] < df_raw["right"]]   # deduplicate
    df_raw = df_raw[~df_raw["left"].map(lambda node: "." not in node)]
    df_raw = df_raw[~df_raw["right"].map(lambda node: "." not in node)]
    df_raw = df_raw[
        df_raw["left"].str.startswith(table_prefix) | df_raw["right"].str.startswith(table_prefix)
    ]

    df_raw = df_raw.assign(
        equality=lambda _df: _df["join_condition"].map(
            lambda join: join.split("=")[0].strip().split(":")[1] + " = " + join.split("=")[1].strip().split(":")[1]
        )
    )

    df_freq = pd.concat([
        df_raw.rename(columns={"left": "node"}),
        df_raw.rename(columns={"right": "node"})
    ], ignore_index=True)[["node", "frequency"]]

    node_frequency = df_freq.groupby("node").agg({"frequency": "sum"}).to_dict()["frequency"]
    nodes_in_order = sorted(
        node_frequency.keys(),
        key=node_frequency.get,
        reverse=True
    )

    # Create graph
    file_suffix = table_prefix.strip("_") or "ALL"
    f = graphviz.Digraph('bigquery', filename=f"bigquery_{file_suffix}.gv")

    # Create nodes : double cicle for the 10 most common tables
    f.attr('node', shape='doublecircle')
    for table_name in nodes_in_order[:10]:
        create_node(f, table_name)

    f.attr('node', shape='circle')
    for table_name in nodes_in_order[10:]:
        create_node(f, table_name)

    # create edges
    for idx, row in df_raw.iterrows():
        f.edge(row["left"], row["right"], row["equality"])

    f.view()


def create_node(f, node_name: str):
    if node_name.startswith("ODS_"):
        color = "beige"
    elif node_name.startswith("DW_"):
        color = "aquamarine"
    elif node_name.startswith("DM_"):
        color = "firebrick1"
    elif node_name.startswith("EFFY_STORE"):
        color = "blue2"
    else:
        color = "white"
    f.node(node_name, color=color)


def sample():
    f = graphviz.Digraph('finite_state_machine', filename='fsm.gv')

    f.attr(rankdir='LR', size='8,5')

    f.attr('node', shape='doublecircle')
    f.node('LR_0')
    f.node('LR_3')
    f.node('LR_4')
    f.node('LR_8')

    f.attr('node', shape='circle')
    f.edge('LR_0', 'LR_2', label='SS(B)')
    f.edge('LR_0', 'LR_1', label='SS(S)')
    f.edge('LR_1', 'LR_3', label='S($end)')
    f.edge('LR_2', 'LR_6', label='SS(b)')
    f.edge('LR_2', 'LR_5', label='SS(a)')
    f.edge('LR_2', 'LR_4', label='S(A)')
    f.edge('LR_5', 'LR_7', label='S(b)')
    f.edge('LR_5', 'LR_5', label='S(a)')
    f.edge('LR_6', 'LR_6', label='S(b)')
    f.edge('LR_6', 'LR_5', label='S(a)')
    f.edge('LR_7', 'LR_8', label='S(b)')
    f.edge('LR_7', 'LR_5', label='S(a)')
    f.edge('LR_8', 'LR_6', label='S(b)')
    f.edge('LR_8', 'LR_5', label='S(a)')

    f.view()


if __name__ == '__main__':
    table_prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    main(table_prefix)
