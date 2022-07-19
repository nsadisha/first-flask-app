import time
import csv
import re
import pandas
import xlrd
import numpy as np
import random
from functools import reduce
import operator
import string
import nltk
import spacy
import wordcloud
import lexical_diversity
import collections
import matplotlib.pyplot as plt
from statistics import mean
import unicodedata
import difflib
from nltk.stem.snowball import SnowballStemmer
from collections import OrderedDict
import copy

from nltk.corpus import *
from spacy import *

from prettytable import PrettyTable

nltk.download("stopwords")
!python -m spacy download fr_core_news_sm

# SHORT AND USEFUL FUNCTIONS

def ll_str(ll):
  ll = [" ".join(ele) for ele in ll] # [] pour le for
  ll = " ".join(ll)
  return ll

def ll_l(ll):
  ll = reduce(operator.concat, ll)
  return ll

def ll_l2(ll):
  ll = [' '.join(ele) for ele in ll]
  return ll

def strip_acc(s_acc):
  s_no_acc = ''.join((c for c in unicodedata.normalize('NFD', s_acc) if unicodedata.category(c) != 'Mn'))
  return s_no_acc

def lt_ll(lt):
  ll = [list(ele) for ele in lt]
  return ll

def ll_str_int(lls):
  lli = [list(map(int, x)) for x in lls]
  return lli

def average_ll(ll):
    result = [mean(x) for x in ll]
    return result

def return_stem(sentence):
    doc = nlp(sentence)
    return [stemmer.stem(X.text) for X in doc]

def strip_end(text, suffix):
  l_txt = text.split()
  for i in range(len(l_txt)):
    if suffix and l_txt[i].endswith(suffix):
      l_txt[i] = l_txt[i][:-len(suffix)]
  
  text = " ".join(l_txt)
  return text


# STARTING CLEANING PART

nlp = spacy.load("fr_core_news_sm")
stopwords = nltk.corpus.stopwords.words('french')
stopwords = [strip_acc(i) for i in stopwords]
stemmer = SnowballStemmer(language='french')

rmpls = {"(?!(?<=\d).(?=\d))[^\w\s ,'’\/ \- ]":"", # PONCTUATION --> RIEN (exceptions [^...] et on fait attention aux points des décimaux)
         "(?<=\d),(?=\d)":".", # VIRGULES DES CHIFFRES DEVIENNENT DES POINTS POUR PYTHON
         "œ":"oe", # E DANS L'O
         # POUR LES UNITES
         r"\bcuillere\s*(a)?\s*cafe\b":"qirc",
         r"\bcuillere\s*(a)?\s*(soupe)?\b":"qirs",
         r"\bpoignee\b":"qirs",
         r"\bc\s*(a)?\s*s\b":"qirs",
         r"\bc\s*(a)?\s*c\b":"qirc",
         r"\bk(ilo)?(s)?\b":"kg",
         r"\bg(r)?(ramme)?(s)?\b":"g",
         "['’\/ \- ]":" "} # METTRE UN ESPACE POUR EPURER

pres = ("facultatif", "environ", "petit", "grand", "gros", "bouquet", "plat", "gousse", "sel", "poivre", "pave", "papier", "aluminium", "surgel",
        "fraich", "quelqu", "rondell", "filet", "moulu", "peu", "choix", "melange", "taille","moyen", "concas", "ajout", "moelleux", "decortiq", "cm")
entire_pres = ["frais"]

# Ce que je veux/peux pas faire pour l'instant:
# Les ou, virer les surplus de chiffres (piste : (?<=\d)(?:.*)(\d[^,]+))

def menage(test_str):
    # ESPACES DE TROP, PARENTHESES, END DOTS, LOWERCASE, NORMALISATION, STR|INT
    test_str = re.sub(' +', ' ', test_str)
    test_str = re.sub(r'\([^)]*\)', '', test_str)
    test_str = re.sub(r"\.(?=\s[A-Z 0-9])",  ",", test_str)
    test_str = test_str.lower()
    test_str = strip_acc(test_str)
    test_str = re.sub(r"\b(\d+)([a-z]+)\b", r"\1 \2", test_str)
    
    # REMPLACEMENTS (ET MOY)
    for k, v in rmpls.items():
      test_str = re.sub(k, v, test_str)
    a_nums = average_ll(ll_str_int(lt_ll(re.findall(r"\b(\d+(?:\.\d+)?)(?:[^\w.]+(?:\w+[^\w,]+){0,1}(\d+(?:\.\d+)?))+\b", test_str))))
    test_str = re.sub(r"\b(\d+(?:\.\d+)?)(?:[^\w.]+(?:\w+[^\w,]+){0,1}(\d+(?:\.\d+)?))+\b",  lambda match: str(a_nums.pop(0)), test_str)

    # BLOCS VIRGULES
    begin = re.split(',+', test_str)

    # BLOC SPLITES
    for i in range(len(begin)):
      begin[i] = begin[i].split()

    # STOPWORDS
    for i in range(len(begin)):
      begin[i] = [j for j in begin[i] if j not in stopwords or j == "l"]

    # PRECISIONS INUTILES
    for i in range(len(begin)):
      begin[i] = [j for j in begin[i] if j.startswith(pres) == False]
    for i in range(len(begin)):
      begin[i] = [j for j in begin[i] if j not in entire_pres]

    # DUPLIQUES
    for i in range(len(begin)):
      begin[i] = list(OrderedDict.fromkeys(begin[i]))

    begin = [i for i in begin if i] # PAS D'ITEMS VIDES
    return begin

# Même idée MAIS on part directement de la liste bien tokenizée et on n'enlève les précisions inutiles
rmpls2 = {"(?!\b[^\w\s]\b)[^\w\s '’ - ]":"", 
          "œ":"oe", # E DANS L'O
          "['’ - ]":" "}
pres2 = ("appertis", "preemball", "rechauff", "reconstit", "cuit", "fait", "maison", "surgel", "fraich")
entire_pres2 = ["frais"]

def menage2(list_food):
    # ESPACES DE TROP, PARENTHESES, END DOTS, LOWERCASE, NORMALISATION, STR|INT, REMPLACEMENTS
    for i in range(len(list_food)):
      list_food[i] = re.sub(' +', ' ', list_food[i])
      list_food[i] = re.sub(r'\([^)]*\)', '', list_food[i])
      list_food[i] = list_food[i].lower()
      list_food[i] = strip_acc(list_food[i])
      list_food[i] = re.sub(r"\b(\d+)([a-z]+)\b", r"\1 \2", list_food[i])
      for k, v in rmpls2.items():
        list_food[i] = re.sub(k, v, list_food[i])

    # BLOC SPLITES
    for i in range(len(list_food)):
      list_food[i] = list_food[i].split()

    # STOPWORDS
    for i in range(len(list_food)):
      list_food[i] = [j for j in list_food[i] if j not in stopwords]

    # PRECISIONS INUTILES
    for i in range(len(list_food)):
      list_food[i] = [j for j in list_food[i] if j.startswith(pres2) == False]
    for i in range(len(list_food)):
      list_food[i] = [j for j in list_food[i] if j not in entire_pres2]

    list_food = [i for i in list_food if i] # PAS D'ITEMS VIDES
    list_food = ll_l2(list_food)
    return list_food

# On prend une liste de chiffres français et on convertit en format python
rmpls3 = {"(?<=\d),(?=\d)":".", "[^\d \.]":""}

def menage3(list_nutri):
    # NON-STR, ESPACES DE TROP, PARENTHESES, REMPLACEMENTS
    for i in range(len(list_nutri)):
      list_nutri[i] = str(list_nutri[i])
      list_nutri[i] = re.sub(' +', ' ', list_nutri[i])
      list_nutri[i] = re.sub(r'\([^)]*\)', '', list_nutri[i])

      for k, v in rmpls3.items():
        list_nutri[i] = re.sub(k, v, list_nutri[i])

    return list_nutri




# STARTING ISOLATION PART
    
units = ["g", "kg", "ml", "cl", "l", "qirc", "qirs", "louche", "tasse", "bol", "verre"]

def isolation(rd):
  
  # RD_D INITIALIZATION
  rd_d = []
  for i in range(len(rd)):
    rd_d.append({"Quantity":[], "Unity":[], "Product":[]})

  for i in range(len(rd)):

  # LOOKING FOR QUANTITIES
    for j in range(len(rd[i])):
      try:
        if float(rd[i][j]):
          rd_d[i]["Quantity"].append(rd[i][j])
      except ValueError:
        pass
    rd[i] = [j for j in rd[i] if j not in rd_d[i]["Quantity"]]

  # LOOKING FOR UNITS
    rd_d[i]["Unity"] = [j for j in rd[i] if j in units]
    rd[i] = [j for j in rd[i] if j not in rd_d[i]["Unity"]]

  # TAKING THE REST AS PRODUCTS 
    rd_d[i]["Product"] = [j for j in rd[i]]
    rd_d[i]["Product"] = " ".join(rd_d[i]["Product"]) # LIST --> STR
    rd[i] = [j for j in rd[i] if j not in rd_d[i]["Product"]]

  rd_d = [i for i in rd_d if i["Product"] and i["Quantity"]] # ONLY PRODUCTS WITH KNOWN QUANTITIES

  for i in range(len(rd_d)):
    rd_d[i]["Quantity"][0] = float(rd_d[i]["Quantity"][0]) # GET ALL QUANTITY TO BE FLOATS

  return rd_d

# GETTING FOOD INFORMATIONS

food_df = pandas.read_excel('/content/drive/MyDrive/Colab Notebooks/Python-projets/Maigrir2000/web_app/Tests/Table Ciqual 2020.xls')
Products_info = food_df.to_dict('records')

food = []
for i in range(len(Products_info)):
    food.append(Products_info[i]['alim_nom_fr'])

calories_kcal = []
for i in range(len(Products_info)):
    calories_kcal.append(Products_info[i]['Energie, Règlement UE N° 1169/2011 (kcal/100 g)'])

acides_gras_satures_g = []
for i in range(len(Products_info)):
    acides_gras_satures_g.append(Products_info[i]['AG saturés (g/100 g)'])

glucides_g = []
for i in range(len(Products_info)):
    glucides_g.append(Products_info[i]['Glucides (g/100 g)'])

proteines_g = []
for i in range(len(Products_info)):
    proteines_g.append(Products_info[i]['Protéines, N x 6.25 (g/100 g)'])

lipides_g = []
for i in range(len(Products_info)):
    lipides_g.append(Products_info[i]['Lipides (g/100 g)'])

eau_g = []
for i in range(len(Products_info)):
    eau_g.append(Products_info[i]['Eau (g/100 g)'])

sucre_g = []
for i in range(len(Products_info)):
    sucre_g.append(Products_info[i]['Sucres (g/100 g)'])

sel_g = []
for i in range(len(Products_info)):
    sel_g.append(Products_info[i]['Sel chlorure de sodium (g/100 g)'])

fibres_g = []
for i in range(len(Products_info)):
    fibres_g.append(Products_info[i]['Fibres alimentaires (g/100 g)'])

cholesterol_mg = []
for i in range(len(Products_info)):
    cholesterol_mg.append(Products_info[i]['Cholestérol (mg/100 g)'])

sodium_mg = []
for i in range(len(Products_info)):
    sodium_mg.append(Products_info[i]['Sodium (mg/100 g)'])


nutriments = {"Calories (kcal)":calories_kcal, "Acides gras saturés (g)":acides_gras_satures_g, "Glucides (g)":glucides_g,
              "Protéines (g)":proteines_g, "Lipides (g)":lipides_g, "Eau (g)":eau_g, "Sucre (g)":sucre_g, "Sel (g)":sel_g, "Fibres (g)":fibres_g,
              "Cholesterol (mg)":cholesterol_mg, "Sodium (mg)":sodium_mg}


# STARTING PAIRING PART

def get_pair(prod, l_comp):

  # INITIALIZE NEEDED VARIABLES 
  coff_val = 1.0 
  pairs = [] 
  b_pair = "" 
  found = False
  stemmed_prod = return_stem(prod)

  # STARTING THE PROCESS WITH THE DIFFERENT CONDITIONS
  while not pairs and coff_val >= 0 and found == False:

    pairs = difflib.get_close_matches(prod, l_comp, cutoff=coff_val)

    # IF WE GOT SOMETHING WE THEN LOOK FOR THE RIGHT ITEM
    if pairs:

      # STEMMING ALL ITEMS AND COMPARING
      pairs_set_score = []
      for i in range(len(pairs)):
        stemmed_item = return_stem(pairs[i])

        # MAKING A LIST WITH A SIMILARITY SCORE FOR EACH ITEM
        pairs_set_score.append(len(set(stemmed_prod).intersection(stemmed_item)))

      # TAKING STEMMED ITEM WITH BEST SIMILARITY SCORE AND > 0
      if max(pairs_set_score) > 0:
        b_pair = pairs[pairs_set_score.index(max(pairs_set_score))]
        found = True
        break # On a mis found à True mais la boucle while ne se stoppe pas automatiquement, il faut break en plus

      # RESTART WITH LOWER PRECISION IF ALL WERE 0
      else:
        coff_val -= 0.1
        pairs = []

    # RESTART WITH LOWER PRECISION  IF NO MATCH
    else:
      coff_val -= 0.1

  return b_pair



def pairage():

  for i in range(len(recette_decoupee_dict)): 
    pair = get_pair(recette_decoupee_dict[i]["Product"], newFood)

    # IF WE FOUND SOMETHING WE APPEND ITS INFOS
    if pair:
      pairs_infos[i][recette_decoupee_dict[i]["Product"]].append(pair)
      pairs_infos[i]["Index"].append(newFood.index(pair))
    # WE APPEND N EVERYWHERE TO SAY IT DIDNT FOUND ANYTHING GOOD
    else:
      pairs_infos[i][recette_decoupee_dict[i]["Product"]].append("N")
      pairs_infos[i]["Index"].append("N")


# GETIING FOOD INFORMATION ONCE AGAIN

poids_df = pandas.read_excel('/content/drive/MyDrive/Colab Notebooks/Python-projets/Maigrir2000/web_app/Tests/poids_moyen_g.ods')

dict_poids = poids_df.set_index('nom_aliment').to_dict()['poids_moyen']


# STARTING CONVERSION + CALCULUS PART

spe_units_conversion = {"qirc":5, "qirs":15, "louche":150, "verre":180, "tasse":130, "bol":280}
other_units_conversion = {"ml":1,"cl":10, "l":1000, "kg":1000}

def no_unity_fix(rd_d_f):
  for i in range(len(rd_d_f)):

    if not rd_d_f[i]["Unity"]:

      rd_d_f[i]["Unity"].append("g")

      coeff_q = rd_d_f[i]["Quantity"][0]
      rd_d_f[i]["Quantity"] = []

      try:
        rd_d_f[i]["Quantity"].append(dict_poids[get_pair(rd_d_f[i]["Product"], dict_poids.keys())] * coeff_q)
      except:
        pass

  return rd_d_f

def spe_unity_fix(rd_d_f):
  for i in range(len(rd_d_f)):

    if rd_d_f[i]["Unity"][0] in spe_units_conversion:

      spe_u_i = rd_d_f[i]["Unity"][0]
      rd_d_f[i]["Unity"] = []
      rd_d_f[i]["Unity"].append("g")

      coeff_q = rd_d_f[i]["Quantity"][0]
      rd_d_f[i]["Quantity"] = []

      rd_d_f[i]["Quantity"].append(spe_units_conversion[spe_u_i] * coeff_q)

  return rd_d_f

def other_unity_fix(rd_d_f):
  for i in range(len(rd_d_f)):

    if rd_d_f[i]["Unity"][0] in other_units_conversion:

      other_u_i = rd_d_f[i]["Unity"][0]
      rd_d_f[i]["Unity"] = []
      rd_d_f[i]["Unity"].append("g")

      coeff_q = rd_d_f[i]["Quantity"][0]
      rd_d_f[i]["Quantity"] = []

      rd_d_f[i]["Quantity"].append(other_units_conversion[other_u_i] * coeff_q)

  return rd_d_f


def table_blanche():
  colonnes = ["Aliments"]
  for k, v in nutriments.items():
    colonnes.append(k)
  
  return PrettyTable(colonnes)


def get_rows_ll():
  for i in range(len(recette_decoupee_dict_fixed)):
    all_rows[i].append(recette_decoupee_dict_fixed[i]["Product"])

    coeff_100_g = recette_decoupee_dict_fixed[i]["Quantity"][0] / 100
    index_nutrition = pairs_infos[i]["Index"][0]

    if index_nutrition != "N":
      for k, v in nutriments.items():
        try: 
          all_rows[i].append(round(float(v[index_nutrition]) * coeff_100_g, 2))
        except ValueError:
          all_rows[i].append("N")

    else:
      for k, v in nutriments.items():
        all_rows[i].append("N")


def get_total_row():
  total = []
  total.append("TOTAL")

  list_zipped_all_rows = list(zip(*all_rows))
  for ele in list_zipped_all_rows[1:]:
    sum_ele = 0
    for item in ele:
      try:
        sum_ele += item
      except:
        pass
    total.append(round(sum_ele, 2))

  all_rows.append(total)


def add_rows():
  for i in range(len(all_rows)):
    recette_table.add_row(all_rows[i])

def all(txt_ing):
  recette_decoupee = menage(ingredients)




  recette_decoupee_dict = isolation(recette_decoupee)

  newFood = menage2(food) # ALL NAMES OF PRODUCTS STORED AND CLEANED IN FOOD
  for k, v in nutriments.items(): # ALL NUTRIMENTS VALUES BEING CLEANED AND STORED IN LISTS
    v = menage3(v)

  # CREATE THE LIST OF DICT WHICH WILL CONTAIN ALL PAIRS AND THEIR INDEX
  pairs_infos = []
  for i in range(len(recette_decoupee_dict)):
    pairs_infos.append({recette_decoupee_dict[i]["Product"]:[], "Index":[]})

  pairage()

  recette_decoupee_dict_fixed = copy.deepcopy(recette_decoupee_dict)
  recette_decoupee_dict_fixed = no_unity_fix(recette_decoupee_dict_fixed)
  recette_decoupee_dict_fixed = spe_unity_fix(recette_decoupee_dict_fixed)
  recette_decoupee_dict_fixed = other_unity_fix(recette_decoupee_dict_fixed)
  recette_table = table_blanche()

  all_rows = []
  for i in range(len(recette_decoupee_dict_fixed)):
    all_rows.append([])

  get_rows_ll()
  get_total_row()
  add_rows()

  print(recette_table)
