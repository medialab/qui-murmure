from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import TrainingArguments, Trainer
from datasets import load_dataset
import numpy as np
import evaluate
from ural import urls_from_text
from ural.twitter import is_twitter_url
from ural.youtube import is_youtube_url
from ural.instagram import is_instagram_url

tokenizer = AutoTokenizer.from_pretrained("almanach/camembertav2-base")
label_to_id = {
    "Commentateur·ice d'actualité": 0.0,
    "Pseudo - médias": 1.0,
    "Anonyme": 2.0,
}
id_to_label = {
    0.0: "Commentateur·ice d'actualité",
    1.0: "Pseudo - médias",
    2.0: "Anonyme",
}


def encode_labels(row):
    row["label"] = row["Catégorie"]
    return row


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
    row["text"] = f"""
    Nom: {row["user_name"]}
    Description : {row["user_description"]}
    Tweets : {tweets}
    """
    return row


# train_set = pd.read_csv("../data/public_attentif_train_set.csv", dtype={"user_id": int})
dataset = load_dataset(
    "csv",
    data_files={
        "train": "../data/public_attentif_train_set.csv",
        "eval": "../data/public_attentif_val_set.csv",
    },
)

dataset = dataset.map(preprocess_text)
dataset = dataset.map(tokenize)
dataset = dataset.map(encode_labels)
dataset = dataset.remove_columns(
    [
        "Catégorie",
        "Positionnement",
        "user_name",
        "user_screen_name",
        "user_description",
        "user_id",
        "coder",
        "text",
    ]
    + [str(i) for i in range(1, 11)]
)
print(dataset["train"][0])
dataset.set_format("torch")

model = AutoModelForSequenceClassification.from_pretrained(
    "almanach/camembertav2-base",
    num_labels=3,
    id2label=id_to_label,
    label2id=label_to_id,
)

accuracy = evaluate.load("accuracy")
f1 = evaluate.load("f1")


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


batch_size = 8
output_dir = "../data/model"

training_args = TrainingArguments(
    output_dir=output_dir,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    weight_decay=0.01,
    load_best_model_at_end=True,
    save_total_limit=3,
    num_train_epochs=5,
    metric_for_best_model="f1",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["eval"],
    compute_metrics=compute_metrics,
)

trainer.train()

metrics = trainer.evaluate()
print(metrics)
