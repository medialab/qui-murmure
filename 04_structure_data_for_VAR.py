"""
# 04_structure_data_for_VAR.py

Date: 2026-04-13
Author: Fynch Meynent

The aim of this script is to create a database to an accomodating format for VAR model implementation

"""

from datetime import datetime, timedelta
from utils import write_general_TS
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--RT", action = "store_true",
                    help = "Run the models considering retweets instead of tweets only.")

args = parser.parse_args()

def list_dates(start_date: str, end_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta = (end - start).days

    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta + 1)]


# Exemple d'utilisation :
dates = list_dates("2022-06-20", "2023-03-14")
nb_dates = len(dates)

write_general_TS("bertopic", nb_dates, "nb_tweets", dates, RT = args.RT)
# write_general_TS('bertopic', nb_dates, 'prop', dates)
# write_general_TS('lda', nb_dates, 'prop', dates)
