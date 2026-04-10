# Qui murmure à l'oreille des député·es

Scripts developped for the paper "Qui murmure à l'oreille des député·es" (currently under review).
Most scripts are designed to be run on a GPU graphical card with 20G of RAM.
You may not be able to reproduce some of the steps below (in particular the installation of [cuML](https://docs.rapids.ai/api/cuml/stable/)) on a CPU.

## Installation

1. Clone this repository

2. Install dependencies

Recommended Python version: 3.12.4
```bash
cd reproduction_wlwf
pip install -r requirements.txt
pip install --extra-index-url=https://pypi.nvidia.com "cudf-cu12==25.4.0" "dask-cudf-cu12==25.4.0" "c^Cl-cu12==25.4.0" "cugraph-cu12==25.4.0" "nx-cugraph-cu12==25.4.0" "cuxfilter-cu12==25.4.0" "cucim-cu12==25.4.0" "pylibraft-cu12==25.4.0" "raft-dask-cu12==25.4.0" "cuvs-cu12==25.4.0" "nx-cugraph-cu12==25.4.0"
```

## Format your data in the following tree

```
data_source
├── congress
    ├── lr
    │   ├── 2022-06-20.csv
    │   ├── 2022-06-21.csv
    │   ├── 2022-06-22.csv
        ...
    ├── majority
    │   ├── 2022-06-20.csv
    │   ├── 2022-06-21.csv
    │   ├── 2022-06-22.csv
        ...
    ├── nupes
    │   ├── 2022-06-20.csv
    │   ├── 2022-06-21.csv
    │   ├── 2022-06-22.csv
        ...
    └── rn
    │   ├── 2022-06-20.csv
    │   ├── 2022-06-21.csv
    │   ├── 2022-06-22.csv
        ...
├── media
    ├── 2022-06-20.csv
    ├── 2022-06-21.csv
    ├── 2022-06-22.csv
        ...
├── supporter
    ├── lr
    │   ├── 2022-06-20.csv
    │   ├── 2022-06-21.csv
    │   ├── 2022-06-22.csv
        ...
    ...
```

The csv files should have the following columns: `id`, `local_time`, `text`, `user_screen_name`, `user_id`, `retweeted_id`
```
id                  local_time          text                 user_screen_name user_id             retweeted_id
1587218214638985216 2022-11-01T00:01:26 RT @UEFrance: 🆕 Es… trudigoz         347374931           1587030788331159553
1587355550840414208 2022-11-01T09:07:09 RT @midy_paul: #Sai… midy_paul        1090311673985056770 1587112047480918018
1587374936288632833 2022-11-01T10:24:11 Cérémonies du Souve… Bannier_G        866695760905154560

```

## Encoding with Sentence-BERT

Example to encode **congress** data
```bash
python 01_encode_with_sbert.py congress
```
You can choose a group among the following categories : congress, attentive, media, supporter.

Example to encode **congress** data from another location where you have stored the `data_source` folder
```bash
python 01_encode_with_sbert.py congress --origin_path /distant_store/reproduction_wlwf
```
--origin_path is by default your current repository, but you can also select another origin to your file tree. Be careful to respect the structure of files and folders within this repository.

NB : If you are using Windows, use "\" instead of "/" in your paths.

## Compute dimensionality reduction using cuML
Example to run the script from another location where you have stored the `data_source` folder
```bash
python 02_run_umap.py --origin_path /distant_store/reproduction_wlwf/
```

## Run BERTopic model
Example to run the script for congress and media:
```bash
python 03_run_bertopic.py --origin_path /distant_store/reproduction_wlwf/ --public congress,media
```
--origin_path has the same function as in 01_encode_with_sbert.py script. Be careful to keep the same origin-path between the two scripts.
--public allows choosing the group(s) you want to use to run the model (by default, all groups are included). You can choose one of the following publics : congress, attentive, media, supporter. You can write several groups separated by a comma.

NB : If you are using Windows, use "\" instead of "/" in your paths

This script produces 3 types of outputs:
- time series (one file per topic), located in `data_prod/dashboard/bertopic/data/`
- keywords associated to each topic (one file per topic), located in `data_prod/dashboard/bertopic/img/`
- representative tweets, (one file per public) located in `data_prod/dashboard/bertopic/representative_docs...`,

## Produce the dashboard
```bash
python 06_dashboard.py
```
This command will create one html page per topic, and a general index page in the `docs` folder.
Once the website is created, you can serve it using the following command:
```bash
python -m http.server -d docs
```
The website will then be visible in your browser on [http://127.0.0.1:8000/]()

------
## Optional steps (running topic modelling using LDA):
### Create document-term matrix for a given public

See the examples below.

* congress:
```bash
python 01-create-dtm.py congress your/path/to/folder/deputes/
```
The results will be saved in `data_prod/dfm/congress-....txt`
* media
```bash
python 01-create-dtm.py media your/path/to/folder/media/
```
The results will be saved in `data_prod/dfm/media-....txt`
* supporter
```bash
python 01-create-dtm.py supporter your/path/to/folder/supporter/
```
The results will be saved in `data_prod/dfm/supporter-....txt`

Etc.