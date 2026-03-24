import csv
import pandas as pd

label_to_id = {
    "Commentateur·ice d'actualité": 0.0,
    "Pseudo - médias": 1.0,
    "Anonyme": 2.0,
}


def print_metrics(file, column):
    with open(file) as f:
        reader = csv.DictReader(f)
        mat = {}
        micro_average = {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "support": 0}
        for label_name in label_to_id:
            mat[label_name] = {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "support": 0}
        for row in reader:
            pred = row[column]
            for c in label_to_id:
                score = float(row[c])
                mat[c]["support"] += score
                if c == pred:
                    if score == 1.0:
                        mat[c]["tp"] += 1
                        micro_average["tp"] += 1
                    elif score == 0.0:
                        mat[c]["fp"] += 1
                        micro_average["fp"] += 1
                    elif score == 0.5:
                        mat[c]["tp"] += score
                        mat[c]["fp"] += score
                        micro_average["tp"] += score
                        micro_average["fp"] += score

                else:
                    if score == 1.0:
                        mat[c]["fn"] += 1
                        micro_average["fn"] += 1
                    if score == 0:
                        mat[c]["tn"] += 1
                        micro_average["tn"] += 1
                    elif score == 0.5:
                        mat[c]["tn"] += score
                        mat[c]["fn"] += score
                        micro_average["tn"] += score
                        micro_average["fn"] += score

    for c in label_to_id:
        try:
            mat[c]["precision"] = mat[c]["tp"] / (mat[c]["tp"] + mat[c]["fp"])
        except ZeroDivisionError:
            mat[c]["precision"] = 0
        try:
            mat[c]["recall"] = mat[c]["tp"] / (mat[c]["tp"] + mat[c]["fn"])
        except ZeroDivisionError:
            mat[c]["recall"] = 0
        try:
            mat[c]["f1 score"] = (
                2
                * (mat[c]["precision"] * mat[c]["recall"])
                / (mat[c]["precision"] + mat[c]["recall"])
            )
        except ZeroDivisionError:
            mat[c]["f1 score"] = 0

    micro_average["precision"] = micro_average["tp"] / (
        micro_average["tp"] + micro_average["fp"]
    )
    micro_average["recall"] = micro_average["tp"] / (
        micro_average["tp"] + micro_average["fn"]
    )
    micro_average["f1 score"] = (
        2
        * (micro_average["precision"] * micro_average["recall"])
        / (micro_average["precision"] + micro_average["recall"])
    )

    df = pd.DataFrame(mat).transpose()
    df.loc["macro average"] = df.mean()
    df.loc["micro average"] = micro_average
    print(df)
