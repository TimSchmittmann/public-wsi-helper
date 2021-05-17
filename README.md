
- [Intro](#intro)
- [Basic setup:](#basic-setup)
- [Selecting the endpoint](#selecting-the-endpoint)
- [Running the examples](#running-the-examples)

# Intro

This repository contains helper code to read and parse wsi and cell data from kaggle dataset and our annotation platform.

# Basic setup:

Clone the repository:

```
git clone git@github.com:TimSchmittmann/public-wsi-helper.git
```

Then create and activate the conda environment (adjust environment.yml if needed):

```
conda env create
conda activate wsi_api_helper
```

Finally copy and modifiy the .env.example file to your local setup

```
cp .env.example .env
nano .env
```

# Selecting the endpoint

There are two ways to access the labeled data:

1. Obtain the zip repository [from kaggle](https://www.kaggle.com/dataset/a49eb5eb219384adf92856e43dcfc79b9cf1eaea5ec13bd57ef304d173ebe42c) and extract it into the directory set in your .env file. This dataset has pseudonymised names for all wsi images and you'll need to run the [read_kaggle_data.example.py](https://github.com/TimSchmittmann/public-wsi-helper/blob/main/read_kaggle_data.example.py) file to cutout the cell images yourself.

2. Obtain the up-to-date data according to your needs via the [REST API](https://172.26.62.216:8000/api/docs/swagger-ui/) of our [annotation platform](https://172.26.62.216:3000). The [data_repo.example.py](https://github.com/TimSchmittmann/public-wsi-helper/blob/main/data_repo.example.py) contains functions to help you create and cache pandas dataframes containing all of the data you'll need. Data from the [REST API](https://172.26.62.216:8000/api/docs/swagger-ui/) is not pseudonymised and you can load the pre-cut cell images directly from the server. This endpoint is only accessible from inside the TU Dresden network (via VPN or direct access).

# Running the examples

It's recommended to move through the .example.py files step by step to get an idea of what is happening. Both files will result in two dataframes for labeled wsi and cell data and create all necessary images. Additionaly [data_repo.example.py](https://github.com/TimSchmittmann/public-wsi-helper/blob/main/data_repo.example.py) contains a join method to join cell and wsi data.
