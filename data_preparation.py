import requests
import json
import skimage.io
import skimage.filters
from filecache import filecache
from pathlib import Path
import re

# import pickle
import pandas as pd

# @filecache(365 * 24 * 60 * 60)
# def pickle_repo(pickle_file_path, backend_url, dataset_ids, segmentation_set_ids, annotator_ids, CELL_DIR, WSI_DIR):
#     if pickle_file_path.exists():
#         with open(pickle_file_path, "rb") as cache_file:
#             return pickle.load(cache_file)
#     else:
#         data_repo = DataRepo(backend_url, dataset_ids, segmentation_set_ids, annotator_ids, CELL_DIR, WSI_DIR)
#         with open(pickle_file_path, "wb") as cache_file:
#             pickle.dump(data_repo, cache_file)


@filecache(365 * 24 * 60 * 60)  #
def build_cell_label_data(cell_dir, cell_data_by_id, selections_by_cell, labels_by_selection):
    data = []
    for cell_id, selections in selections_by_cell.items():
        try:
            for annotator_cell_label_selection in selections:
                if annotator_cell_label_selection["id"] in labels_by_selection:
                    for label in labels_by_selection[annotator_cell_label_selection["id"]]:
                        data.append(
                            {
                                "cell_id": cell_id,
                                "img_path": str(cell_dir / cell_data_by_id[cell_id]["imgName"]),
                                "label": label,
                                "wsi_id": cell_data_by_id[cell_id]["wsi"],
                            }
                        )
                    # if cell_id not in data:
                    #     data[cell_id] = {"imgPath": cell_dir / cell_data_by_id[cell_id]["imgName"], "labels": []}
                    # data[cell_id]["labels"] += labels_by_selection[annotator_cell_label_selection["id"]]
        except Exception as e:
            print(e)
            continue
    return pd.DataFrame(data)
    # df = pd.DataFrame(data).transpose()
    # return df


@filecache(365 * 24 * 60 * 60)  #
def build_wsi_label_data(wsi_dir, wsi_data_by_id):
    data = []
    for wsi_id, wsi in wsi_data_by_id.items():
        for label in wsi["label"]:
            data.append(
                {
                    "wsi_id": wsi_id,
                    "img_path": str(wsi_dir / wsi["imgName"]),
                    "pixel_diameter_in_micrometer": wsi["pixelDiameterInMicrometer"],
                    "label": label,
                    "dataset_id": wsi["datasetId"],
                }
            )
    return pd.DataFrame(data)
    # df = pd.DataFrame(data).transpose()
    # return df


@filecache(365 * 24 * 60 * 60)  #
def build_xy_data(cell_dir, cell_data_by_id, selections_by_cell, labels_by_selection, labels_by_id, target_label_id):
    data = {"id": [], "x": [], "y": []}
    label_group_id = labels_by_id[target_label_id]["labelGroup"]
    for cell_id, selections in selections_by_cell.items():
        try:
            annotator_cell_label_selection = next(
                selection
                for selection in selections
                if selection["labelGroup"] == label_group_id and selection["id"] in labels_by_selection
            )
            img_path = cell_dir / cell_data_by_id[annotator_cell_label_selection["cell"]]["imgName"]
            try:
                # skimage.io.imread(CELL_DIR / f"{selection['cell']}.png")
                # Label 1 = is Promyelocyte cell)
                if target_label_id in labels_by_selection[annotator_cell_label_selection["id"]]:
                    data["x"].append(skimage.io.imread(img_path))
                    data["y"].append(1)
                    data["id"].append(annotator_cell_label_selection["cell"])
                    # Label 7 means no special characteristic
                else:
                    data["x"].append(skimage.io.imread(img_path))
                    data["y"].append(0)
                    data["id"].append(annotator_cell_label_selection["cell"])
            except:
                print(f"image corrupted: {img_path}")
                img_path.unlink()
        except:
            continue
    return data


@filecache(365 * 24 * 60 * 60)
def retrieve_wsi_data(endpoint, dataset_id):
    response = requests.get(endpoint, verify=False)
    wsi_data = json.loads(response.content)
    valid_wsi = []
    for wsi in wsi_data:
        if wsi["datasetId"] == dataset_id:
            valid_wsi.append(wsi)
    return valid_wsi


@filecache(365 * 24 * 60 * 60)
def retrieve_cell_data(endpoint):
    response = requests.get(endpoint, verify=False)
    return json.loads(response.content)


@filecache(365 * 24 * 60 * 60)
def retrieve_annotator_cell_label_selections(endpoint, valid_cell_id_dict, annotator_id):
    response = requests.get(endpoint, verify=False)
    cell_label_selections = json.loads(response.content)
    valid_selections = []
    for selection in cell_label_selections:
        if int(selection["annotator"]) == annotator_id and int(selection["cell"]) in valid_cell_id_dict:
            valid_selections.append(selection)
    return valid_selections


@filecache(365 * 24 * 60 * 60)
def retrieve_labels_in_selections(endpoint, valid_selections_id_dict):
    response = requests.get(endpoint, verify=False)
    labels_in_selections = json.loads(response.content)
    valid_labels = []
    for label in labels_in_selections:
        if int(label["annotatorCellLabelSelection"]) in valid_selections_id_dict:
            valid_labels.append(label)
    return valid_labels


@filecache(365 * 24 * 60 * 60)
def retrieve_labels(endpoint):
    response = requests.get(endpoint, verify=False)
    return json.loads(response.content)


@filecache(365 * 24 * 60 * 60)
def filter_valid_images(df):
    shapes = {"width": [], "height": []}
    valid_indices = []
    for row in df.itertuples(index=True):
        try:
            img = skimage.io.imread(row.img_path)
            shapes["width"].append(img.shape[1])
            shapes["height"].append(img.shape[0])
            valid_indices.append(row.Index)
        except:
            shapes["width"].append(0)
            shapes["height"].append(0)
    df["img_width"] = shapes["width"]
    df["img_height"] = shapes["height"]
    return df.loc[valid_indices]


@filecache(365 * 24 * 60 * 60)
def retrieve_wsi_and_cell_data(backend_url, dataset_ids, segmentation_set_ids):
    cell_data = []
    wsi_data = []
    for dataset_id in dataset_ids:
        wsi_data += retrieve_wsi_data(f"{backend_url}/api/wsi/", dataset_id)
    for wsi in wsi_data:
        wsi["label"] = parse_wsi_labels(wsi)
        for segmentation_set_id in segmentation_set_ids:
            cell_data += retrieve_cell_data(f"{backend_url}/api/wsi_cells/{wsi['id']}/{segmentation_set_id}")
    return wsi_data, cell_data


@filecache(365 * 24 * 60 * 60)
def parse_wsi_labels(wsi):
    if wsi["datasetId"] == 3:
        return {"healthy"}
    if wsi["datasetId"] == 2:
        m = re.match(r"pat\d+-slide(?: |r|-)?\d+(?:(?:-|\.)([^-]+))?(?:-([a-z]+))?", wsi["imgName"])
        if m:
            if m.lastindex == 2:
                return {"aml", m.group(1), m.group(2)}
            if m.lastindex == 1:
                return {"aml", m.group(1)}
            return {"aml"}
    if wsi["datasetId"] == 1:
        matches = re.search("(\d+)-(AML|Napoleon)-Register-((\d+)-)?", wsi["imgName"], re.IGNORECASE)
        if matches:
            return {"aml", "m3"}
            # rows.append({'Filepath': file_path, 'OriginalFilename': filename, 'PatientId': matches[1], 'Register': matches[2],
            # 'Diagnosis': 'AML', 'SlideId': matches[4], 'Magnification': matches[5], 'Subtype': 'M3'})
        matches = re.search("(.+)-AIDA-?2000-?(\d+)", wsi["imgName"], re.IGNORECASE)
        if matches:
            return {"aml", "m3"}
            # rows.append({'Filepath': file_path, 'OriginalFilename': filename, 'PatientId': matches[1], 'Register': 'AIDA2000',
            # 'Diagnosis': 'AML', 'SlideId': matches[2], 'Magnification': matches[3], 'Subtype': 'M3'})
        matches = re.search("Pat(\d+)(?:-|_)(?:Slide ?)?(\d+)(?:-|\.)((M\d|not_?classified)-)?", wsi["imgName"], re.IGNORECASE)
        if matches:
            return {"aml", "not_classified" if matches[3] == None or matches[4] == "notclassified" else matches[4]}
            # rows.append({'Filepath': file_path, 'OriginalFilename': filename, 'PatientId': matches[1],
            # 'Diagnosis': 'AML', 'SlideId': matches[2], 'Magnification': matches[5],
            # 'Subtype': 'not_classified' if matches[3] == None  or matches[4] == 'notclassified' else matches[4]})
    raise ValueError(f'Invalid wsi name: {wsi["imgName"]}, dataset: {wsi["datasetId"]}')


class DataRepo(object):
    def __init__(
        self, backend_url, dataset_ids, segmentation_set_ids, annotator_ids, cell_dir, wsi_dir, skip_image_download=False
    ):
        self.backend_url = backend_url
        self.dataset_ids = dataset_ids
        self.segmentation_set_ids = segmentation_set_ids
        self.annotator_ids = annotator_ids
        self.cell_dir = cell_dir
        self.wsi_dir = wsi_dir
        self.pixel_diameter_in_micrometer = 0
        self.wsi_data_by_id = {}
        self.cell_data_by_id = {}
        self.labels_by_id = {}
        self.labels_by_selection = {}
        self.selections_by_cell = {}
        self.preload(skip_image_download)

    #
    def download_image_data(self, data, target_dir):
        for obj in data:
            # response = requests.get(f"http://schmittmann.me:8084/api/cell/{selection['cell']}")
            obj_image = Path(target_dir) / f"{obj['imgName']}"
            if obj_image.is_file():
                continue
            response = requests.get(obj["ressourceUrl"], verify=False)
            with open(obj_image, "wb") as out_file:
                print(f"Save {obj_image}")
                out_file.write(response.content)

    def preload(self, skip_image_download=False):
        wsi_data, cell_data = retrieve_wsi_and_cell_data(self.backend_url, self.dataset_ids, self.segmentation_set_ids)
        if not skip_image_download:
            self.download_image_data(wsi_data, self.wsi_dir)
            self.download_image_data(cell_data, self.cell_dir)
        valid_cell_id_dict = {cell["id"]: 1 for cell in cell_data}
        cell_label_selections = []
        for annotator_id in self.annotator_ids:
            cell_label_selections += retrieve_annotator_cell_label_selections(
                f"{self.backend_url}/api/cell_label_selections/", valid_cell_id_dict, annotator_id
            )
        valid_selections_id_dict = {selection["id"]: 1 for selection in cell_label_selections}
        labels_in_selections = retrieve_labels_in_selections(
            f"{self.backend_url}/api/labels_in_selections/", valid_selections_id_dict
        )
        self.labels_by_id = {label["id"]: label for label in retrieve_labels(f"{self.backend_url}/api/labels/")}
        self.labels_by_selection = {}
        for label in labels_in_selections:
            if label["annotatorCellLabelSelection"] not in self.labels_by_selection:
                self.labels_by_selection[label["annotatorCellLabelSelection"]] = []
            self.labels_by_selection[label["annotatorCellLabelSelection"]].append(label["label"])
        self.selections_by_cell = {}
        for selection in cell_label_selections:
            if selection["cell"] not in self.selections_by_cell:
                self.selections_by_cell[selection["cell"]] = []
            self.selections_by_cell[selection["cell"]].append(selection)
        self.wsi_data_by_id = {wsi["id"]: wsi for wsi in wsi_data}
        self.cell_data_by_id = {cell["id"]: cell for cell in cell_data}

    #
    def build_target_label_xy_data(self, target_label_id):
        return build_xy_data(
            self.cell_dir,
            self.cell_data_by_id,
            self.selections_by_cell,
            self.labels_by_selection,
            self.labels_by_id,
            target_label_id,
        )

    def build_cell_label_data(self):
        return build_cell_label_data(self.cell_dir, self.cell_data_by_id, self.selections_by_cell, self.labels_by_selection)

    #
    def build_wsi_label_data(self):
        return build_wsi_label_data(self.wsi_dir, self.wsi_data_by_id)
