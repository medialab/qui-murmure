from transformers import AutoModelForSequenceClassification
import torch
from train import preprocess_text, tokenizer
import csv
from metrics import print_metrics
from tqdm import tqdm
import casanova
import os
import glob
import sys

path_to_actu = os.path.join(sys.argv[1], "actu")
path_to_anonymes = os.path.join(sys.argv[1], "anonymes")

device = "cuda"

model_anonymes = AutoModelForSequenceClassification.from_pretrained(
    max(glob.glob(os.path.join(path_to_anonymes, "*/")), key=os.path.getmtime)
).to(device)
model_actu = AutoModelForSequenceClassification.from_pretrained(
    max(glob.glob(os.path.join(path_to_actu, "*/")), key=os.path.getmtime)
).to(device)

INPUT_FILE = "../data/public_attentif_test_set.csv"
OUTPUT_FILE = "../data/prediction_bert_public_attentif_test_set.csv"


def proba_from_logits(logits):
    probs = torch.softmax(logits, dim=-1)
    pred_id = torch.argmax(probs, dim=-1).item()
    confidence = probs[0][pred_id].item()
    return pred_id, confidence


with open(INPUT_FILE, "r") as input_file, open(OUTPUT_FILE, "w") as output_file:
    reader = csv.DictReader(input_file)
    writer = csv.DictWriter(
        output_file,
        fieldnames=reader.fieldnames
        + ["bert-label", "bert-confidence-anonymes", "bert-confidence-actu"],
    )
    writer.writeheader()

    for row in tqdm(reader, total=casanova.count(INPUT_FILE)):
        inputs = tokenizer(
            preprocess_text(row),
            return_tensors="pt",
            truncation=True,
            max_length=1024,
            padding=True,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model_anonymes(**inputs)
        pred_id, confidence_anonyme = proba_from_logits(outputs.logits)
        label = model_anonymes.config.id2label[pred_id]

        if label == "Actu":
            with torch.no_grad():
                outputs = model_actu(**inputs)
            pred_id, confidence_actu = proba_from_logits(outputs.logits)
            label = model_actu.config.id2label[pred_id]
        else:
            confidence_actu = ""

        row["bert-label"] = label
        row["bert-confidence-anonymes"] = confidence_anonyme
        row["bert-confidence-actu"] = confidence_actu
        writer.writerow(row)

print_metrics(OUTPUT_FILE, "bert-label")
