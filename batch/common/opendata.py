# -*- coding: utf8 -*-
from __future__ import print_function, unicode_literals

import json
import os
import sys
from copy import deepcopy
from zipfile import ZipFile

from bs4 import BeautifulSoup
import requests

from . import COMMON_DIR

CACHE_DIR = os.path.join(COMMON_DIR, "opendata")

AN_BASE_URL = "http://data.assemblee-nationale.fr"
AN_ENTRYPOINTS = {
    "14": {
        "amo": "opendata-archives-xive/deputes-senateurs-et-ministres-xive-legislature",
        "reunions": "opendata-archives-xive/agendas-xive-legislature",
        "scrutins": "opendata-archives-xive/scrutins-xive-legislature",
    },
    "15": {
        "amo": "acteurs/historique-des-deputes",
        "reunions": "reunions/reunions",
        "scrutins": "travaux-parlementaires/votes",
    },
}

MODELS = {
    "amo": {
        "export": {
            "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "acteurs": {
                "acteur": "acteur"
            },
            "organes": {
                "organe": "organe"
            }
        }
    },
    "reunions": {
        "reunions": {
            "reunion": "reunion"
        }
    },
    "scrutins": {
        "scrutins": {
            "scrutin": "scrutin"
        }
    }
}

DEBUG = "--debug" in sys.argv

def log(str, debug=False):
    if not debug or DEBUG:
        try:
            print(str, file=sys.stderr)
        except:
            print(str.encode("utf-8"), file=sys.stderr)


def fetch_an_jsonzip(legislature, objet):
    """
    Télécharge le zip du JSON depuis une page de l'open data AN, s'il a été
    modifié depuis le dernier téléchargement.

    Renvoie le chemin local du fichier zip téléchargé (stocké dans le
    répertoire de cache) et un flag indiquant s'il a été modifié
    """

    if (
        str(legislature) not in AN_ENTRYPOINTS
        or objet not in AN_ENTRYPOINTS[str(legislature)]
    ):
        raise Exception(
            "Objet inconnu: %s (%s legislature)" % (objet, legislature)
        )

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    localzip = os.path.join(CACHE_DIR, "%s_%s.zip" % (legislature, objet))
    localzip_lastmod = "%s.last_modified" % localzip

    url = "%s/%s" % (AN_BASE_URL, AN_ENTRYPOINTS[str(legislature)][objet])
    log("Téléchargement %s" % url, debug=True)

    try:
        soup = BeautifulSoup(requests.get(url).content, "lxml")
    except Exception:
        raise Exception("Téléchargement %s impossible" % url)

    def match_link(a):
        return a["href"].endswith(".json.zip") or a["href"].endswith(
            ".json.zip "
        )

    try:
        link = [a for a in soup.select("a[href]") if match_link(a)][0]
    except Exception:
        raise Exception("Lien vers dump .json.zip introuvable")

    jsonzip_url = link["href"].replace(".json.zip ", ".json.zip")
    if jsonzip_url.startswith("/"):
        jsonzip_url = "%s%s" % (AN_BASE_URL, jsonzip_url)

    log("URL JSON zippé : %s" % jsonzip_url, debug=True)

    try:
        lastmod = requests.head(jsonzip_url).headers["Last-Modified"]
    except Exception:
        raise Exception("Date du dump .json.zip introuvable")

    log("Date modification dump .json.zip: %s" % lastmod, debug=True)
    do_download = True

    if os.path.exists(localzip) and os.path.exists(localzip_lastmod):
        with open(localzip_lastmod, "r") as f:
            known_lastmod = f.read()

        log("Date modification dernier telechargement: %s" % known_lastmod, debug=True)
        if known_lastmod == lastmod:
            do_download = False

    if do_download:
        log("Téléchargement .json.zip", debug=True)

        try:
            with open(localzip, "wb") as out:
                r = requests.get(jsonzip_url, stream=True)
                for block in r.iter_content(1024):
                    out.write(block)
            with open(localzip_lastmod, "w") as f:
                f.write(lastmod)
        except Exception:
            raise Exception("Téléchargement .json.zip impossible")
    else:
        log("Téléchargement skippé, fichier non mis à jour", debug=True)

    return localzip, do_download


def fetch_an_json(legislature, objet):
    """
    Télécharge le zip du JSON depuis une page de l'open data AN, s'il a été
    modifié depuis le dernier téléchargement.

    page: URL relative de la page, par exemple "travaux-parlementaires/votes"

    Renvoie les données JSON du fichier zip téléchargé et un flag indiquant si
    le fichier a été modifié.
    """

    localzip, updated = fetch_an_jsonzip(legislature, objet)
    if legislature >= 15:
        assembled_data = deepcopy(MODELS[objet])
        export = assembled_data["export"] if "export" in assembled_data else assembled_data
        objects = [(objname.values()[0], objcat) for objcat, objname in export.items() if type(objname) is dict]
        for obj, objcat in objects:
            export[objcat][obj] = []
    with ZipFile(localzip, "r") as z:
        for f in [f for f in z.namelist() if f.endswith(".json")]:
            log("JSON extrait : %s" % f, debug=True)
            with z.open(f) as zf:
                elmt = json.load(zf)
                if legislature < 15:
                    return elmt, updated
                for obj, objcat in objects:
                    if "/%s/" % obj in f or len(objects) == 1:
                        if obj in elmt:
                            elmt = elmt[obj]
                        export[objcat][obj].append(elmt)
                        break
        return assembled_data, updated


def _cached_ref(
    legislature, objet, id_mapping, extract_list, extract_id, extract_mapped
):
    """
    Génère et renvoie un cache de mapping d'identifiants à partir d'un dump
    open data json.

    legislature, objet: définit le dump à utiliser
    id_mapping: identifiant unique du mapping, utilisé pour stocker en cache
    extract_list: fonction qui extrait la liste des items du dump json
    extract_id: fonction qui extrait l'identifiant à mapper d'un item
    extract_mapped: fonction qui extrait les données mappées d'un item
    """

    data, updated = fetch_an_json(legislature, objet)
    cached_file = os.path.join(
        CACHE_DIR, "mapping_%s_%s.json" % (legislature, id_mapping)
    )

    if updated or not os.path.exists(cached_file):
        cache = {}
        for item in extract_list(data):
            id = extract_id(item)
            cache[id] = extract_mapped(item, data)

        with open(cached_file, "w") as f:
            json.dump(cache, f)
        return cache
    else:
        with open(cached_file) as f:
            return json.load(f)


def ref_groupes(legislature, ND_names=False):
    """
    Renvoie un mapping des id opendata des groupes parlementaires vers leur
    abbréviation
    """

    GROUPES_ND = {
        "UDI-AGIR": "UAI",
        "LAREM": "LREM",
        "FI": "LFI"
    }

    def _extract_list(data):
        return filter(
            lambda o: o["codeType"] == "GP",
            data["export"]["organes"]["organe"],
        )

    def _extract_id(organe):
        return organe["uid"]

    def _extract_mapped(organe, data):
        if ND_names and organe["libelleAbrev"] in GROUPES_ND:
            return GROUPES_ND[organe["libelleAbrev"]]
        return organe["libelleAbrev"]

    return _cached_ref(
        legislature,
        "amo",
        "groupes",
        _extract_list,
        _extract_id,
        _extract_mapped,
    )

def ref_histo_groupes(legislature, ND_names=False):
    """
    Renvoie un mapping des id opendata des parlementaires vers une liste
    ordonnée temporellement de leurs appartenances à un groupe politique
    """

    GROUPES = ref_groupes(legislature, ND_names=ND_names)
    sort_periods = lambda x: "%s-%s" % (x["debut"], x["fin"])

    def _extract_list(data):
        return data["export"]["acteurs"]["acteur"]

    def _extract_id(acteur):
        return acteur["uid"]["#text"]

    def _extract_mapped(acteur, data):
        groupes = [{
            "sigle": GROUPES[m["organes"]["organeRef"]],
            "debut": m["dateDebut"],
            "fin": m["dateFin"]
          } for m in acteur["mandats"]["mandat"]
          if m["typeOrgane"] == "GP"
          and m["legislature"] == legislature
          and m["preseance"] != "1"
        ]
        groupes = sorted(groupes, key=sort_periods)
        return groupes

    return _cached_ref(
        legislature,
        "amo",
        "histo_groupes",
        _extract_list,
        _extract_id,
        _extract_mapped,
    )

def ref_seances(legislature):
    """
    Renvoie un mapping des id opendata des séances vers leur ID
    """

    REMAPPED = {
        "RUANR5L15S2017IDS20667": "20172002",
        "RUANR5L15S2018IDS20817": "20180086",
        "RUANR5L15S2018IDS20864": "20180121",
        "RUANR5L15S2018IDS20981": "20180174",
        "RUANR5L15S2019IDS21507": "20190153",
        "RUANR5L15S2019IDS21608": "20190218",
        "RUANR5L15S2020IDS21840": "20200002",
        "RUANR5L15S2020IDS21841": "20200003",
        "RUANR5L15S2020IDS21859": "20200001",
        "RUANR5L15S2020IDS21968": "20200089",
        "RUANR5L15S2020IDS21970": "20200090",
        "RUANR5L15S2020IDS21983": "20200092",
        "RUANR5L15S2020IDS22019": "20200117",
        "RUANR5L15S2020IDS22020": "20200118",
        "RUANR5L15S2020IDS22021": "20200119",
        "RUANR5L15S2020IDS22054": "20200134",
        "RUANR5L15S2020IDS22055": "20200135",
        "RUANR5L15S2020IDS22056": "20200136",
        "RUANR5L15S2020IDS22057": "20200137",
        "RUANR5L15S2020IDS22087": "20200139",
        "RUANR5L15S2020IDS22089": "20200140",
        "RUANR5L15S2020IDS22106": "20200125",
    }

    def _extract_list(data):
        return filter(
            lambda reunion: "IDS" in reunion["uid"],
            data["reunions"]["reunion"],
        )

    def _extract_id(reunion):
        return reunion["uid"]

    def _extract_mapped(reunion, data):
        return REMAPPED.get(reunion["uid"]) or reunion["identifiants"]["idJO"]

    return _cached_ref(
        legislature,
        "reunions",
        "seances",
        _extract_list,
        _extract_id,
        _extract_mapped,
    )
