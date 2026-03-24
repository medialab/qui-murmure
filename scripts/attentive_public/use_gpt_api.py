import os
import json
import pandas as pd
from tqdm import tqdm
from openai import OpenAI
import sys
import csv
import time
from sklearn.metrics import classification_report
import casanova

from train import preprocess_tweet
from metrics import print_metrics

API_KEY = sys.argv[1]
MODEL = "gpt-5-mini"

INPUT_FILE = "../data/public_attentif_test_set.csv"
OUTPUT_FILE = "../data/prediction_gpt_public_attentif_test_set.csv"

label_to_id = {
    "Commentateur·ice d'actualité": 0.0,
    "Pseudo - médias": 1.0,
    "Anonyme": 2.0,
}

client = OpenAI(api_key=API_KEY)


def preprocess_text(row):
    tweets = ""
    for tweet_rank in range(1, 11):
        tweet = preprocess_tweet(str(row[str(tweet_rank)]))
        tweets += f"tweet {tweet_rank}: {tweet}"
        tweets += "\n"
    return f"""
    Bio : {row["user_description"].replace(row["user_screen_name"], "redacted_name")}
    Tweets : {tweets.replace(row["user_screen_name"], "redacted_name")}
    """


def build_prompt(user_description):
    return f"""
Tu es un annotateur spécialisé en sciences politiques et en sociologie des médias.

Ta tâche est de classifier un utilisateur de Twitter/X dans UNE des catégories suivantes :

{label_to_id.keys()}

Voici la définition des catégories :

Pseudo - médias : Désigne les médias (qui se présentent explicitement comme média dans leur description) et les journalistes. Inclut les blogueurs spécialisés sur un thème, à condition qu'ils produisent des contenus en dehors de Twitter/X et indépendamment du contenu des tweets (une mention dans la bio suffit). Inclut les créateurs de newsletters, de chaînes youtube et de podcasts.
Commentateur·ice d'actualité : Désigne des personnes particulièrement attentive à l'actualité, qui commentent l'actualité et/ou partagent au moins 3 tweets d'actualité. Inclut les spécialistes d'un domaine qui mobilisent les médias. Inclut les gens qui ne font que retweeter des médias (mais intensément et sur des thèmes précis), un peu comme le feraient des curateurs de news. Inclut les commentateurs exclusifs d'actualité people ou sportive.
Anonyme : Désigne les autres utilisateurs de Twitter/X.

Voici quelques exemples de chaque catégorie :

Anonyme
    Bio : "Qui ne gueule la vérité dans un langage brutal quand il sait la vérité se fait le complice des menteurs et des faussaires .
Zemmourienne.
pas de MP"
    Tweets :
        tweet 1 : "Actu17: Paris : Un homme étranglé pour sa montre et laissé inconscient, la BAC interpelle un suspect de 17 ans.
https://actu17.fr/faits-divers/paris-un-homme-etrangle-pour-sa-montre-et-laisse-inconscient-la-bac-interpelle-un-suspect-de-17-ans.html

via @GoogleNews"
        tweet 2 : @nini_ninimini Parti au bled avec le voleur
        tweet 3 : @BHL @oleksiireznikov Comparer zelinsky  à De Gaulle , c'est ignoble
        tweet 4 : @meyerclotilde1 @JuniorGuibole Plus aucun tweet de disponible

Pseudo - médias
    Bio : Senior Solution Engineer @VMware & Blogger at http://MyVMworld.fr| vExpert x4 - VCP-NV | K8S-NSX-vRA | BlockChain and Crypto Investor | The tweets are mine
    Tweets : tweet 1 : "RT @infos_gg: Nouvelle présentation du #PSVR2 lors du CES 2023 !

Sony a annoncé un événement spécial de 45 mins lors du prochain CES de Las Vegas. Vu la nature du salon porté sur la tech, il est probable que les caractéristiques techniques soient mises en avant...

Sortie le 22/02 sur #PS5 🎮"
    tweet 2 : @Ash2501 @mit_chum 🫣 je suis pas un grand lecteur de romans mais tu vas te régaler 🙂
    tweet 3 : Nous avons le plaisir  de vous annoncer notre première chaîne de #Podcast 🎙️ en collaboration avec Cyril CUVIER et Block Unchained 🔗🔗, explorant les dernières avancées en matière de technologies #Blockchain🔗, #Cloud ☁️ et #Web3 🌍.

Commentateur·ice d'actualité
    Bio : Inquiet par la montée des populismes d'extrême droite et d'extrême gauche, par le complotisme, l'obscurantisme et le communautarisme.
    Tweets : tweet 1 : @MyriamHebuterne Apres avoir été encerclée par les ukrainiens,  l'armée russe vient d'annoncer officiellement s'être retirée de la ville de Lyman !!
    tweet 2 : RT @tcabarrus: CQFD « BHL: Le rapport d’#Amnesty sur l’#Ukraine est non seulement ignoble (comme si on avait, en 44, accusé les résistants de se battre dans Paris) mais stupide (qu’est-ce «19 cas» face à une #Russie qui pilonne & rase purement et simplement les villes?) L’ONG, en persévérant, se déshonore.»
    tweet 3 : "@BFMTV "" L'antisionisme est une incroyable aubaine, car il nous donne la permission, le droit, le devoir d'être antisémite au nom de la démocratie ! L'antisionisme est l'antisémitisme justifié, mis enfin à la portée de tous. Il permet d'être démocratiquement antisémite.""
V.Jankélevitch"
    tweet 4 : "@lemondefr Quel contraste entre le discours bureaucrate, médiocre et gras de Poutine de ce matin et le discours éclairé de Biden de ce soir....
C'est le choc des civilisations !!

Voici les métadonnées concernant l'utilisateur de Twitter :
{user_description}

Réponds uniquement avec un JSON valide de la forme :
{{"label": "NomDeLaCategorie"}}
"""


def predict(user_text):
    prompt = build_prompt(user_text)
    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    try:
        parsed = json.loads(response.output_text)
        return parsed["label"]
    except Exception as e:
        print("Parsing error:", e)
        return "ERROR"


with open(INPUT_FILE) as input_file, open(OUTPUT_FILE, "w") as output_file:
    reader = csv.DictReader(input_file)
    writer = csv.DictWriter(output_file, fieldnames=reader.fieldnames + ["gpt-label"])
    writer.writeheader()

    for row in tqdm(reader, total=casanova.count(INPUT_FILE)):
        user_text = preprocess_text(row)

        row["gpt-label"] = predict(user_text)
        writer.writerow(row)

    print("Terminé.")

print_metrics(OUTPUT_FILE, "gpt-label")
