"""
Require first to generate file "joins_frequency.csv"
& grep -v "Function()" joins_frequency.csv > joins_frequency_no_func.csv

Generate a list of all identical fields in different tables
eg :
 - pistes.id = opportunity.piste_id = calls.piste_id
 - table_1.project_id = table_2.project_id
"""
import os
from collections import Counter
from pprint import pprint
from typing import List

import graphviz
import pandas as pd


def graph_field_joins():
    df_raw = pd.read_csv(
        os.path.join(os.getenv("DATA_DIR"), "parse_sql", "joins_frequency.csv"),
        usecols=["file_name", "left_table", "left_col", "right_table", "right_col"]
    ).assign(
        left=lambda df: df["left_table"] + " " + df["left_col"],
        right=lambda df: df["right_table"] + " " + df["right_col"],
    )[["file_name", "left", "left_col", "right", "right_col"]]

    df_joins = pd.concat([
        df_raw.rename(columns={"left": "0", "right": "1"}),
        df_raw.rename(columns={"right": "0", "left": "1"})
    ], ignore_index=True)[["0", "1"]].rename(columns={"0": "left", "1": "right"})

    # Save list of clusters, ready to paste into confluence
    clustered_keys = cluster_same_fields(df_joins)
    with open("column_joins.txt", "w+") as f:
        for table_column_names in sorted(clustered_keys, key=len, reverse=True):
            cols = (col.split(":")[0] for col in table_column_names)
            lines = [
                Counter(col for col in cols if col.lower() != "id").most_common(1)[0][0]
            ]
            lines.extend(map(format_col_name, sorted(table_column_names)))
            f.write("### " + "\n> ".join(lines) + "\n\n")

    # Prepare cluster id with file_name, to gen 1 graph per cluster
    clusters = {
        table_id: num_cluster
        for num_cluster, table_ids in enumerate(clustered_keys)
        for table_id in table_ids
    }

    df_raw["cluster_id"] = df_raw["left"].map(clusters.get)
    df_raw.to_csv("clustered.csv", index=False)

    # Generate graphs:
    for cluster_id, sub_df in df_raw.groupby("cluster_id"):  # .query("cluster_id <= 5")
        df_cluster = sub_df.groupby(
            ["left", "left_col", "right", "right_col"],
            as_index=False,
        ).agg({"file_name": "\n".join})
        # pprint(df_cluster)

        table_names = set(df_cluster["left"]) | set(df_cluster["right"])
        column_names = [
            col
            for col in df_cluster["left_col"].tolist() + df_cluster["right_col"].tolist()
            if col != "id"
        ]

        if len(table_names) < 5:
            continue
        if len(column_names) > 0:
            cluster_name = Counter(column_names).most_common(1)[0][0]
        else:
            cluster_name = df_cluster["left"].iloc[0]

        f = graphviz.Digraph('bigquery', filename=f"cluster_fields/{cluster_name}_{cluster_id}")
        for node_name in table_names:
            f.node(node_name)
        for idx, row in df_cluster.iterrows():
            print("edge", row["left"], row["right"])
            f.edge(row["left"], row["right"], row["file_name"])
        f.view()


def cluster_same_fields(df_joins) -> List[set]:
    dict_joins = df_joins.groupby("left").agg({"right": set}).to_dict()["right"]

    for nb_loop in range(1000):
        dict_joins = {
            key: set(values) | {key}
            for key, values in list(dict_joins.items())
        }

        counter = Counter(
            item
            for k, v in dict_joins.items()
            for item in v
        )
        table_name, count = counter.most_common(1)[0]

        if count <= 1:
            break

        keys = [
            key
            for key, values in dict_joins.items()
            if table_name in values
        ]

        all_columns = set()
        for key in set(keys):
            # pprint(dict_joins.get(key))
            all_columns = all_columns | dict_joins.pop(key)
        dict_joins[table_name] = all_columns

    return list(dict_joins.values())


def format_col_name(col_name: str):
    return col_name
    dataset = col_name.split(".")[0]
    col_name = col_name.split(".")[1]
    table_name = col_name.split(":")[0]
    field_name = col_name.split(":")[1]
    return f"{dataset:<30}{table_name:<30}{field_name}"


if __name__ == '__main__':
    graph_field_joins()
