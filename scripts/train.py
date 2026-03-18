from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import TrainingArguments, Trainer
from torch.utils.data import Dataset
import numpy as np
import evaluate
from ural import urls_from_text
from ural.twitter import is_twitter_url
from ural.youtube import is_youtube_url
from ural.instagram import is_instagram_url
import os
import torch
import csv

accuracy = evaluate.load("accuracy")
f1 = evaluate.load("f1")


def preprocess_tweet(tweet):
    for url in urls_from_text(tweet):
        if is_twitter_url(url) or is_instagram_url(url) or is_youtube_url(url):
            tweet = tweet.replace(url, "")
    return tweet


def tokenize(row):
    return tokenizer(
        row["text"], truncation=True, padding="max_length", max_length=1024
    )


def preprocess_text(row):
    tweets = ""
    for tweet_rank in range(1, 11):
        tweet = preprocess_tweet(str(row[str(tweet_rank)]))
        tweets += tweet
        tweets += "\n"
    return f"""
    Nom: {row["user_name"]}
    Description : {row["user_description"]}
    Tweets : {tweets}
    """


def encode_labels(row, remaping):
    return remaping[int(float(row["Catégorie"]))]


def load_datasets(datasets, remaping, filtered):
    for dataset in datasets.values():
        dataset["texts"] = []
        dataset["labels"] = []
        with open(dataset["path"], "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if filtered(row):
                    dataset["texts"].append(preprocess_text(row))
                    dataset["labels"].append(encode_labels(row, remaping))
    return datasets


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy.compute(predictions=predictions, references=labels)[
            "accuracy"
        ],
        "f1": f1.compute(
            predictions=predictions, references=labels, average="weighted"
        )["f1"],
    }

class TorchDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=1024):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )

        item = {key: val.squeeze(0) for key, val in encoding.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def train_model(datasets, tokenizer, label_to_id, output_dir):

    id_to_label = {i: l for l, i in label_to_id.items()}

    train_set = TorchDataset(datasets["train"]["texts"], datasets["train"]["labels"], tokenizer)
    val_set = TorchDataset(datasets["val"]["texts"], datasets["val"]["labels"], tokenizer)

    model = AutoModelForSequenceClassification.from_pretrained(
        "almanach/camembertav2-base",
        num_labels=2,
        id2label=label_to_id,
        label2id=id_to_label,
    )

    for name, param in model.deberta.named_parameters():
        if "encoder.layer.9" in name or "encoder.layer.10" in name or "encoder.layer.11" in name:
            param.requires_grad = True
        else:
            param.requires_grad = False


    training_args = TrainingArguments(
        output_dir=output_dir,
        learning_rate=2e-4,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        weight_decay=0.01,
        load_best_model_at_end=True,
        save_total_limit=3,
        num_train_epochs=10,
        metric_for_best_model="f1",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_set,
        eval_dataset=val_set,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    metrics = trainer.evaluate()
    print(metrics)


if __name__=="__main__":
    paths = {
        "train": {"path": "../data/public_attentif_train_set.csv"},
        "val": {"path": "../data/public_attentif_val_set.csv"}
    }

    # label_to_id = {
    #     "Commentateur·ice d'actualité": 0,
    #     "Pseudo - médias": 1,
    #     "Anonyme": 2,
    # }

    label_to_id = {
        "Actu": 0,
        "Anonyme": 1,
    }

    remaping = {0: 0, 1: 0, 2: 1}

    datasets = load_datasets(paths, remaping, lambda x: True)

    tokenizer = AutoTokenizer.from_pretrained("almanach/camembertav2-base")

    train_model(datasets, tokenizer, label_to_id, "~/storage/medialex/enquete-attentif/anonymes/")

    label_to_id = {
        "Commentateur·ice d'actualité": 0,
        "Pseudo - médias": 1,
    }

    remaping = {0: 0, 1: 1}

    def filtered(row):
        return row["Catégorie"] != "2.0"

    datasets = load_datasets(paths, remaping, filtered)

    train_model(datasets, tokenizer, label_to_id, "~/storage/medialex/enquete-attentif/actu/")
