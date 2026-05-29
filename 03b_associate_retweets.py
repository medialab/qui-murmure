"""
# 03b_associate_retweets.py

Date: 2026-05-26
Author: Béatrice Mazoyer

Includes retweets in time series.
This script produces one file per topic, located in data_prod/dashboard/bertopic/data/with_retweets/

"""

import io
import os
import argparse
import casanova
from ebbe import Timer
from collections import defaultdict

from utils import (
    PUBLICS,
    GROUPS,
    count_nb_files,
    iter_on_files,
    existing_dir_path,
    grep_group_name,
    create_dir,
)

def write_time_serie_with_retweets(results, writer, topic, party, date):
    nb_tweets = results[topic] if topic in results else 0
    writer.writerow(
        [
            date,
            party,
            topic,
            round(nb_tweets / results["total"], 5),
            nb_tweets,
            results["total"]
        ]
    )


parser = argparse.ArgumentParser()

parser.add_argument(
    "--origin_path",
    help="Path to a folder containing the data in a subfolder called data_source.",
    type=existing_dir_path,
    default=os.getcwd(),
)

parser.add_argument(
    "--public",
    help=("List of publics separated by commas : public1,public2,public3"),
    default=",".join(PUBLICS),
)

args = parser.parse_args()

publics = args.public.split(",")

for elem in publics:
    if elem not in PUBLICS:
        raise ValueError(
            "{} is not part of the supported publics, please select publics from the following list : {}".format(
                elem, PUBLICS
            )
        )

tweets_topics = defaultdict(dict)
topics = set()

for public in publics:
    reader = casanova.reader(
        os.path.join(
            args.origin_path,
            "data_prod",
            "dashboard",
            "bertopic",
            "ids_topics_{}.csv".format(public),
        )
    )
    topic_pos = reader.headers.topic
    id_pos = reader.headers.id

    for row in reader:
        if int(row[topic_pos]) != -1:
            tweets_topics[public][int(row[id_pos])] = int(row[topic_pos])
            topics.add(int(row[topic_pos]))

retweets_topics_count = {
    p: {g: defaultdict(dict) for g in GROUPS}
    if p in ["congress", "supporter"]
    else defaultdict(dict)
    for p in publics
}

for public in publics:
    data_source = os.path.join(args.origin_path, "data_source", public)
    tar, loop, compressed = iter_on_files(data_source, count_nb_files(data_source))

    for file in loop:
        if compressed:
            filename = file.name
        else:
            filename = file

        loop.set_description(filename)

        file_date = os.path.basename(filename)[:10]

        group_name = grep_group_name(filename)

        if public in ["congress", "supporter"]:
            retweets_topics_count[public][group_name][file_date]["total"] = 0
            date_dict = retweets_topics_count[public][group_name][file_date]
        else:
            retweets_topics_count[public][file_date]["total"] = 0
            date_dict = retweets_topics_count[public][file_date]

        if compressed:
            filestream = io.TextIOWrapper(tar.extractfile(file))
        else:
            filestream = open(file)
        reader = casanova.reader(filestream)

        rt_pos = reader.headers.retweeted_id
        id_pos = reader.headers.id

        for row in reader:
            if int(row[id_pos]) in tweets_topics[public]:
                topic_id = tweets_topics[public][int(row[id_pos])]
            elif row[rt_pos] and int(row[rt_pos]) in tweets_topics:
                topic_id = tweets_topics[public][int(row[rt_pos])]
            else:
                topic_id = None
            if topic_id is not None:
                date_dict["total"] += 1

                if topic_id not in date_dict:
                    date_dict[topic_id] = 0
                date_dict[topic_id] += 1



output_folder = create_dir(
    os.path.join(
        args.origin_path, "data_prod", "dashboard", "bertopic", "data", "with_retweets"
    )
)
with Timer("Write time series with retweets"):
    for topic in topics:
        with open(
            os.path.join(output_folder, "bertopic_ts_{}.csv".format(topic)), "w"
        ) as f:
            writer = casanova.writer(
                f,
                fieldnames=["date", "party", "topic", "prop", "nb_tweets", "total"],
            )

            for public in retweets_topics_count:
                if public in ["congress", "supporter"]:
                    for group in retweets_topics_count[public]:
                        party = (
                            group if public == "congress" else "{}_supp".format(group)
                        )

                        for date in retweets_topics_count[public][group]:
                            results = retweets_topics_count[public][group][date]
                            write_time_serie_with_retweets(results, writer, topic, party, date)

                else:
                    for date in retweets_topics_count[public]:
                        results = retweets_topics_count[public][date]
                        write_time_serie_with_retweets(results, writer, topic, public, date)


# tweets_topics = {1538673000274448384: -1, 1538673908743905280: 36}
# retweets_topics_count = {{} for p in publics}
# for public in ["congress", "supporter"]:
#     if public in publics:
#         retweets_topics_count["congress"] = {{} for g in GROUPS}

# d = {
#     "2020-06-20": {
#         "congress": {
#             "lr": {
#                 "total": 32,
#                 -1: 32,
#             }
#         }
#     }
# }
