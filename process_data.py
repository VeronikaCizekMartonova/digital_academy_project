#!/usr/bin/env python3
#  _*_ coding: utf-8 _*_
"""Tento skript zpracovava data pro srovnani aut ze zahranici s nabidkou v CR v soudobe nabidce.
    @param: filename - vstupni soubor databaze aut
"""

__author__ = "Veronika Cizek Martonova"
__license__ = "MIT"
__version__ = "1.0.0"

import pandas as pd
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
#print(data)

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

# vybrani unikatnich modelu (fabia, scala...):
car_models = data['CATALOG_MAKE_MODEL_FAMILY_NAME'].unique()
#print(car_models)

# rozgrupovani aut dle modelu a jestli jsou z CZ nebo zahranici-> vysledkem je 2x 11 "temporary" tabulek = 22 tabulek
for car_model in car_models:
    output_file = open ("results/" + car_model + '.csv', mode="w", encoding='utf-8') 
    print(car_model)
    #ziskani vsech radku z data dle jednotlivych modelu
    data_models = data.query("CATALOG_MAKE_MODEL_FAMILY_NAME == @car_model") ## moje subtabulka podle modelu (tabulka fabek, scal...)
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
    for czech_car in data_models_czech.values: 
        while not time_overlap_boolean_fce(car_foreign_help[ptr],czech_car):
            ptr+=1
        time_overlap_cars = [x for x in car_foreign_help[ptr::] if time_overlap_boolean_fce(x, czech_car) == True] ##tahle fce mi hodi jen auta, ktere jsou v jednom casovem poolu s danym ceskym autem
        #print(time_overlap_cars)
        len_time_overlap_cars = len(time_overlap_cars)
        
        list_of_better_cars = pd.DataFrame([x for x in time_overlap_cars if if_car_actually_better_fce(x,czech_car) == True])
        len_list_of_better_cars = len (list_of_better_cars)
        print(f"ptr= {ptr},pool of cars is: {len_time_overlap_cars} and number of better is:{len_list_of_better_cars}")
       
        if len_list_of_better_cars > 0:
            best_car  = list_of_better_cars.sort_values(by=[DISPLAY_PRICE_CZK_index])        
            best_car = best_car.to_numpy()        
                    
            #print(best_car.iloc[0][ID_index])
            #print(best_car.iloc[:][ID_index].head(10))
            output_file.write(f"{czech_car[ID_index]}, {len_time_overlap_cars}, {len_list_of_better_cars},{czech_car[STATUS_index]} , {best_car[0,0]}\n")
        
        else:
            output_file.write(f"{czech_car[ID_index]}, {len_time_overlap_cars}, {len_list_of_better_cars},{czech_car[STATUS_index]} , NULL \n")
    output_file.close()





