# Qui murmure à l'oreille des député·es

Scripts developped for the paper "Qui murmure à l'oreille des député·es" (currently under review).
Most scripts are designed to be run on a GPU graphical card with 20G of RAM.
You may not be able to reproduce some of the steps below (in particular the installation of [cuML](https://docs.rapids.ai/api/cuml/stable/)) on a CPU.

Many functions and variables used in several parts of the code are defined in [utils.py](https://github.com/medialab/qui-murmure/blob/main/utils.py), for example the text preprocessing is described [here](https://github.com/medialab/qui-murmure/blob/be4274669a3d95256ec22e6fdf5a84fcb6904a52/utils.py#L477-L499).

## Installation

1. Clone this repository

2. Install dependencies

Recommended Python version: 3.12.4
```bash
cd reproduction_wlwf
pip install -r requirements.txt
```
3. Install cuML with the [correct specification](https://docs.rapids.ai/install/#selector) depending on your CUDA version (see below for CUDA 12):
```bash
pip install --extra-index-url=https://pypi.nvidia.com "cudf-cu12==26.4.*" "dask-cudf-cu12==26.4.*" "cuml-cu12==26.4.*" "cugraph-cu12==26.4.*" "nx-cugraph-cu12==26.4.*" "cuxfilter-cu12==26.4.*" "cucim-cu12==26.4.*" "pylibraft-cu12==26.4.*" "raft-dask-cu12==26.4.*" "cuvs-cu12==26.4.*" "nx-cugraph-cu12==26.4.*"
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

The csv files should have the following columns: `id`, `text`, `user_id`, `retweeted_id`, `to_userid` (if the tweet is a reply, id of the author of the tweet replied to), `to_tweetid` (if the tweet is a reply, id of the tweet replied to).
```
text                                         id                  retweeted_id        user_id    to_userid  to_tweetid
RT @UEFrance: 🆕 Estimation du taux d'infla… 1587218214638985216 1587030788331159553 347374931
RT @UEFrance: 🆕 Estimation du taux d'infla… 1587218515227992065 1587030788331159553 2250213234
@bertrand149 @alma_dufour Exact. 7 Mds ça f… 1587218672078159873                     328510700  1430392861 1587207053017288705

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

## Run VAR model

Firstly, run this script to create a file that has the correct format for the VAR model script.

```bash
python 04_structure_data_for_VAR.py 
```
This generates a file located in the following path: `data_prod/dashboard/general_TS.csv`.
You can also run the following option: 
- RT: Create the file for the models with RT option (optional). It generates a file located in the following path: `data_prod/dashboard/general_TS_withRT.csv` 

To run the VAR model, you can use a script with some options:
- tests: this option will generate a file located in `data_prod/var/issue-level/infos_topics.csv`. For each topic, this file tells the stationarity type (stationary for each group, stationary in difference for each group, or different type of stationarity between groups), the AIC/HQ/FPE/SC selection criteria, and the minimum number of lags that are necessary to avoid autocorrelation of residuals. This file must exist to use the estimate option.
- estimate: this option will estimate the VAR model for each topic and calculate GIRF. For each topic, it will generate a file for the VAR model parameter located in `data_prod/var/issue-level/var_model_{topic_number}.Rdata` and a GIRF file `data_prod/var/issue-level/var_girf_topic_{topic_number}.Rdata`. VAR model files must exist to use the tests_post option.
- tests_post: This option will generate a file located  `data_prod/var/issue-level/post_checks.csv`. For each topic, it will indicate if the maximum of absolute values of the roots, if the absence of autocorrelation for residuals is assessed (Portmanteau test), and if the normality of residuals is accepted (multivariate Jarque-Bera test).
- number_irf: the number of days for cumulated GIRF chosen for some outputs (default: 40)
- RT: Run the model considering retweets instead of original tweets only. (optional). It generates, depending on the chosen options, the following files: `data_prod/var/issue-level/infos_topics_withRT.csv`, and the other files (identical to those without the RT option) in the following folder: `data_prod/var/issue-level/RT`. 



If files linked to estimation exist, this script generates the following file: `data_prod/var/irf_data.csv` which is a file with cumulated GIRF data for the number of days chosen in the number_irf option.

Here is an example of the script to generate cumulated IRF for 30 days with all options.

```bash
Rscript 05-var-models.r --tests --estimate --tests_post --number_irf 30 --RT
```



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