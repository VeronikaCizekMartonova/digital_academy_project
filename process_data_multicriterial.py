#!/usr/bin/env python3
#  _*_ coding: utf-8 _*_
"""Tento skript zpracovava data pro srovnani aut ze zahranici s nabidkou v CR v soudobe nabidce a obohacuje kod o multikriterialni vyber, 
    ktery je dal zpracovan ve vizualizacnim nastroji Tableau.
    @param: filename - vstupni soubor databaze aut
"""

__author__ = "Veronika Cizek Martonova"
__license__ = "MIT"
__version__ = "1.0.0"

import pandas as pd
import numpy as np
import random
import sys


# definice funkci:
def time_overlap_boolean_fce (car_foreign,car_cz): 
    #print(car_foreign,car_cz, AD_FIRST_OCCURENCE_DATE_index,AD_LAST_OCCURENCE_DATE_index)
    if car_cz[AD_FIRST_OCCURENCE_DATE_index] > car_foreign[AD_LAST_OCCURENCE_DATE_index]:
        return False
    if car_cz[AD_LAST_OCCURENCE_DATE_index] < car_foreign[AD_FIRST_OCCURENCE_DATE_index]:
        return False
    return True

def if_car_actually_better_fce(car_foreign, car_cz):
    if car_cz[DISPLAY_PRICE_CZK_index] < car_foreign[DISPLAY_PRICE_CZK_index]: # kdyz je ceske auto levnejsi, tak zahranicni vyhod
        return False
    if car_cz[CAR_REGISTRATION_DATE_index] > car_foreign[CAR_REGISTRATION_DATE_index]: # kdyz je ceske auto registrovano pozdeji nez zahranicni, zahranicni vyhod
        return False
    if car_cz[CAR_MILEAGE_index] < car_foreign[CAR_MILEAGE_index]: # kdyz ma ceske auto najeto min nez zahranicni, zahranicni vyhod
        return False
    if car_cz[CATALOG_POWER_index] > car_foreign[CATALOG_POWER_index]: #kdyz ma ceske auto vetsi vykon nez zahranicni, zahranicni vyhod
        return False
    if car_cz[CATALOG_TRANSMISSION_index] == 'AUTOMATIC' and car_foreign[CATALOG_TRANSMISSION_index] == 'MANUAL': ## jestlize ceske auto ma automat a zahranicni manual, tak zahranicni vyhod (vychazim z predpokladu, ze automat je lepsi nez manual)
        return False
    return True

# nacteni dat:
if len(sys.argv < 2):
    print("Spatny pocet argumentu")

filename = sys.argv[1]
data = pd.read_csv(filename, encoding='utf-8')



# definice pomocných indexů:
AD_FIRST_OCCURENCE_DATE_index = data.columns.get_loc('AD_FIRST_OCCURENCE_DATE')
AD_LAST_OCCURENCE_DATE_index = data.columns.get_loc('AD_LAST_OCCURENCE_DATE')
DISPLAY_PRICE_CZK_index = data.columns.get_loc('DISPLAY_PRICE_CZK')
CAR_REGISTRATION_DATE_index = data.columns.get_loc('CAR_REGISTRATION_DATE')
CAR_MILEAGE_index = data.columns.get_loc('CAR_MILEAGE')
CATALOG_POWER_index = data.columns.get_loc('CATALOG_POWER')
CATALOG_TRANSMISSION_index = data.columns.get_loc('CATALOG_TRANSMISSION')
ID_index = data.columns.get_loc('ID')
STATUS_index = data.columns.get_loc('STATUS')

#kontrolni vypisy:
#print(data.columns)
#print(data["CAR_REGISTRATION_DATE"])

# nahrazeni data 1990-01-01 ve sloupecku AD_LAST_OCCURENCE_DATE za aktualni
data.replace({'AD_LAST_OCCURENCE_DATE':'1990-01-01'}, '2022-06-01', inplace=True) 
#print(data["AD_LAST_OCCURENCE_DATE"])

# vyhozeni aut, kde neni uvedena hodnota CAR_MILEAGE (cca 10 000, z toho 908 z CR)
data.drop(data[data['CAR_MILEAGE'] < 0].index, inplace = True)
#print(data.shape[0])


# pretypovani datumu na "datetime"
data['CAR_REGISTRATION_DATE'] = pd.to_datetime(data['CAR_REGISTRATION_DATE'], format="%Y-%m-%d")
data['AD_FIRST_OCCURENCE_DATE'] = pd.to_datetime(data['AD_FIRST_OCCURENCE_DATE'], format="%Y-%m-%d")
data['AD_LAST_OCCURENCE_DATE'] = pd.to_datetime(data['AD_LAST_OCCURENCE_DATE'], format="%Y-%m-%d")
#print(data["AD_LAST_OCCURENCE_DATE"])

# vidim, ze ted uz je to pretypovany
data.info() ## data info je print sam o sobe!!!!!

# spocitani veku aut a pretypovani sloupce CAR_AGE_NOT_ROUNDED
data["CAR_AGE_NOT_ROUNDED"] = (data["AD_LAST_OCCURENCE_DATE"] - data["CAR_REGISTRATION_DATE"])
data["CAR_AGE_NOT_ROUNDED"] = pd.to_numeric(data["CAR_AGE_NOT_ROUNDED"]/86400000000000,downcast='float')

# vybrani unikatnich modelu (fabia, scala...):
car_models = data['CATALOG_MAKE_MODEL_FAMILY_NAME'].unique()
#print(car_models)




########################### MULTICRITERIAL PART #################

print("-------------------------------------")
# prevedeni dat do numpy array
data_np = data.to_numpy()
print(data_np)

print(data_np.shape)
# definice vektoru vector_of_coef
vector_of_coef = np.asarray([0]*data_np.shape[1])
print(vector_of_coef)
# definice váhového vektoru weight_vector
weight_vector = np.asarray([1]*len(vector_of_coef))
print(weight_vector)
# definice koeficientu pro uzivatele(od 1 do 10):
c_mileage = 1
c_price = 1
c_age = 1

koef_vaha = 4 ## vahovy koef 4

vector_of_coef[8] = c_mileage
vector_of_coef[14] = c_price
vector_of_coef[15] = c_age

## hledam nenulove hodnoty vektoru vector_of_coef a jeho indexy:
vector_of_coef_index = []
for i,index in enumerate(vector_of_coef):
    if index > 0:
        position = i
        vector_of_coef_index.append(position)
    else: continue
print(vector_of_coef_index)

vector_of_coef_selected = []
for member in vector_of_coef:
    if member > 0:
        vector_of_coef_selected.append(member)
    else: continue
print(vector_of_coef_selected)

# vytazeni sloupcu, ktere se budou vahovat a normalizovat dle vector_of_coef_index
used_headers = list(data.columns.values)
used_headers = [used_headers[i] for i in vector_of_coef_index]
#car_columns_param = car.loc[:,["CAR_MILEAGE","DISPLAY_PRICE_CZK","CAR_AGE_NOT_ROUNDED"]]
car_columns_param = data.loc[:,used_headers]
print(car_columns_param)
#load as "float" to allow later normalization
car_matrix_selected = car_columns_param.to_numpy(dtype='float64')

# normalizace dat
for i in range(0, car_matrix_selected.shape[1]):
    sloupec = car_matrix_selected[:,i]
    min_sloupec = np.min(sloupec)
    max_sloupec = np.max(sloupec)
    normalization = (sloupec-min_sloupec)/float(max_sloupec - min_sloupec)
    car_matrix_selected[:,i] = normalization

print("\ncar_martix_selected:")
print(car_matrix_selected)
data_normalised = data
data_normalised["CAR_MILEAGE"] = car_matrix_selected[:,0]
data_normalised["DISPLAY_PRICE_CZK"] = car_matrix_selected[:,1]
data_normalised["CAR_AGE_NOT_ROUNDED"] = car_matrix_selected[:,2]

print(data_normalised.loc[:,["CAR_MILEAGE", "DISPLAY_PRICE_CZK", "CAR_AGE_NOT_ROUNDED"]])
print(data_normalised.iloc[:,8:15])


# rozgrupovani aut dle modelu a jestli jsou z CZ nebo zahranici-> vysledkem je 2x 11 "temporary" tabulek = 22 tabulek
for car_model in car_models:
    output_file = open ("results_multicriterial/" + car_model + '.csv', mode="w", encoding='utf-8') 
    print(car_model)
    #ziskani vsech radku z data dle jednotlivych modelu
    data_models = data_normalised.query("CATALOG_MAKE_MODEL_FAMILY_NAME == @car_model") ## moje subtabulka podle modelu (tabulka fabek, scal...)
    #print(data_models)
    #ziskani vsech radku z data dle jednotlivych modelu:
    data_models_czech = data_models.query("CAR_LOCATION_COUNTRY == 'CZ'") ## moje subtabulka ceskych aut podle modelu (tabulka fabek, scal...)
    data_models_czech.sort_values(by=['AD_FIRST_OCCURENCE_DATE'], inplace=True) ## setrizeni podle ad_first_occurency_date
    print(data_models_czech[['CATALOG_MAKE_MODEL_FAMILY_NAME','CAR_LOCATION_COUNTRY', 'AD_FIRST_OCCURENCE_DATE']])

    data_models_foreign = data_models.query("CAR_LOCATION_COUNTRY != 'CZ'") ## moje subtabulka aut ze zahranici podle modelu (tabulka fabek, scal...)
    data_models_foreign.sort_values(by=['AD_LAST_OCCURENCE_DATE'], inplace=True) ## setrizeni podle ad_last_occurency_date
    print(data_models_foreign[['CATALOG_MAKE_MODEL_FAMILY_NAME','CAR_LOCATION_COUNTRY','AD_LAST_OCCURENCE_DATE']])
    ptr = 0
    car_foreign_help = data_models_foreign.values
    data_models_czech_value = random.choices(data_models_czech.values,k=100)
    for czech_car in data_models_czech_value: 
        while not time_overlap_boolean_fce(car_foreign_help[ptr],czech_car):
            ptr+=1
        time_overlap_cars = np.asarray([x for x in car_foreign_help[ptr::] if time_overlap_boolean_fce(x, czech_car) == True]) ##tahle fce mi hodi jen auta, ktere jsou v jednom casovem poolu s danym ceskym autem
        #print(time_overlap_cars)
        len_time_overlap_cars = len(time_overlap_cars)

        for param_mileage in np.arange(0,11):
            for param_price in np.arange(0,11):
                for param_age in np.arange(0,11):
                    # cost funkce (není to CAR_DISPLAY_PRICE)
                    cost_cz_car = czech_car[8]*param_mileage + czech_car[14]*param_price*koef_vaha + czech_car[15]*param_age
                    cost_eu_cars = time_overlap_cars[:,8]*param_mileage + time_overlap_cars[:,14]*param_price*koef_vaha + time_overlap_cars[:,15]*param_age
                    
                    list_of_better_cars = []
                    list_of_costs = []
                    for i in range(0,len(time_overlap_cars)):
                        if cost_cz_car > cost_eu_cars[i]:
                            list_of_better_cars.append(time_overlap_cars[i])
                            list_of_costs.append(cost_eu_cars[i])

                    len_list_of_better_cars = len (list_of_better_cars)
                    
                    if len_list_of_better_cars > 0:
                        list_of_better_cars = np.asarray(list_of_better_cars)
                        list_of_costs = np.asarray(list_of_costs)

                        sorted_indices = np.argsort(list_of_costs)
                        list_of_sorted_cars = list_of_better_cars[sorted_indices]
                        list_of_costs = list_of_costs[sorted_indices]

                        best_car = list_of_sorted_cars[0]
                        output_file.write(f"{czech_car[ID_index]}, {param_mileage}, {param_price}, {param_age},{len_time_overlap_cars}, {len_list_of_better_cars}, {czech_car[STATUS_index]} ,{best_car[0]}\n")
                
                    else:
                        output_file.write(f"{czech_car[ID_index]}, {param_mileage}, {param_price}, {param_age},{len_time_overlap_cars}, {len_list_of_better_cars},{czech_car[STATUS_index]} , NULL \n")
                    print(f"ptr= {ptr},pool of cars is: {len_time_overlap_cars} and number of better is:{len_list_of_better_cars}")

    output_file.close()
        



