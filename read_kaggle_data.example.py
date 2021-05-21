from collections.abc import Iterable
import pandas as pd
from environs import Env
from pathlib import Path
from data_preparation import cutout_cell_images

env = Env()
env.read_env()
DATA_DIR = Path(env("IO_DATA_DIR"))
CELL_DIR = DATA_DIR / "cells"
WSI_DIR = DATA_DIR / "wsi"

# Test labeled_cells.csv
cell_df = pd.read_csv(DATA_DIR / "labeled_cells.csv")
cell_multilabel_columns = ["cellType", "segmentationQuality", "specialCharacteristics", "objectType"]

# Test wsi.csv
wsi_df = pd.read_csv(DATA_DIR / "wsi.csv")
wsi_multilabel_columns = ["label"]


def is_iterable_but_not_str(obj):
    return isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, bytearray))


def multilabel_columns_to_sparse_df(df, multilabel_columns):
    labels = {}
    for idx, row in df[multilabel_columns].iterrows():
        for group_name, group_values in row.items():
            if type(group_values) == str:
                group_values = eval(group_values)
            if is_iterable_but_not_str(group_values):
                for label in group_values:
                    if not label in labels:
                        labels[label] = []
                    labels[label].append(idx)
    for key, values in labels.items():
        df.loc[:, key] = df.index.isin(values)
    df = df.drop(multilabel_columns, axis=1)
    return df


# Assign correct img_path based on local DATA_DIR
cell_df = cell_df.assign(img_path=cell_df["id"].apply(lambda id: CELL_DIR / f"{id}.png"))
# Setting cell_id to id to prevent mixup with wsi_ids
cell_df = cell_df.assign(cell_id=cell_df["id"])
# Cleanup cells with incorrect bbox
cell_df = cell_df.dropna(subset=["bbox"])
cell_df["bbox"] = cell_df["bbox"].apply(eval)

# Assign correct img_path based on local DATA_DIR
wsi_df = wsi_df.assign(img_path=wsi_df["imgName"].apply(lambda imgName: WSI_DIR / imgName))

# Cutout cells
cutout_cell_images(cell_df, wsi_df)

# Transform dataframes into sparse matrix format
cell_df = multilabel_columns_to_sparse_df(cell_df, cell_multilabel_columns)
wsi_df = multilabel_columns_to_sparse_df(wsi_df, wsi_multilabel_columns)

cell_df.to_csv(str(DATA_DIR / "cell_df.csv"))
wsi_df.to_csv(str(DATA_DIR / "wsi_df.csv"))
