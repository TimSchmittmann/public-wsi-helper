from data_preparation import DataRepo, filter_valid_images
from environs import Env
from pathlib import Path

env = Env()
env.read_env()
DATA_DIR = Path(env("IO_DATA_DIR"))
CELL_DIR = DATA_DIR / "cell_images"
WSI_DIR = DATA_DIR / "wsi_images"
CELL_DIR.mkdir(exist_ok=True, parents=True)
WSI_DIR.mkdir(exist_ok=True, parents=True)
"""
Dataset ids correspond to
1: APL Classification with 50 APL and 50 Non-APL WSI images
2: AML Classification with ~1300 AML WSI images
3: Healthy WSI images

Segmentation_set_ids are:
1: Initial segmentation pre DL model
2: HIIT-Segmentation with the help from our DL model
3: Automated segmantation by our DL model

Important annotator_ids are:
12: Expert annotator Jan Eckardt
15: Annotation aggregator Tim
"""
data_repo = DataRepo(
    "https://172.26.62.216:8000",
    dataset_ids=[1, 2, 3],
    segmentation_set_ids=[3],
    annotator_ids=[15],
    cell_dir=CELL_DIR,
    wsi_dir=WSI_DIR,
)
cell_df = data_repo.build_cell_label_data()
wsi_df = data_repo.build_wsi_label_data()

# Build df with valid promyelocyte cell images as cell_df["y"]==1 and "other" cell_df["y"]==0
promyelocyte_label = 1
cell_df["y"] = cell_df["label"].apply(lambda label: 1 if label == promyelocyte_label else 0)
# There is one row for each label of a cell, but we will only keep every cell id once.
# Descending sort makes sure, that we keep all true (1) labels
cell_df = cell_df.sort_values("y", ascending=False).drop_duplicates(subset="cell_id", keep="first")
# Drop label column as it would be misleading, because we dropped unneeded labels
cell_df = cell_df.drop("label", axis=1)
cell_df = filter_valid_images(cell_df)

# Same procedure for wsi. Build df with valid AML M3 images as wsi_df["y"]==1 and "other" wsi_df["y"]==0
m3_label = "m3"
wsi_df["y"] = wsi_df["label"].apply(lambda label: 1 if label == m3_label else 0)
wsi_df = wsi_df.sort_values("y", ascending=False).drop_duplicates(subset="wsi_id", keep="first")
wsi_df = wsi_df.drop("label", axis=1)
wsi_df = filter_valid_images(wsi_df)

# Combine dfs to get all cells labeled as promyelocyte/other (combined_df.y_cell == 1 or 0)
# with their wsi images labeled as m3/other (combined_df.y_wsi == 1 or 0)
combined_df = cell_df.join(wsi_df.set_index("wsi_id"), on="wsi_id", lsuffix="_cell", rsuffix="_wsi")

cell_df.to_csv(str(DATA_DIR / "cell_df.csv"))
wsi_df.to_csv(str(DATA_DIR / "wsi_df.csv"))
combined_df.to_csv(str(DATA_DIR / "combined_df.csv"))