# -*- coding: utf-8 -*-
"""
Created on Tue Jul  8 08:59:18 2025

@author: asyl_scy (Kara)

topic= la vengeance est un plat qui se mange généralement froid

"""

#have to install seleniumwire, selenium , pandas(time, io, gzip, json)

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options#manage options
from selenium.webdriver.common.by import By #for the selections, etc.

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

import pandas as pd

import gzip
import io
import json


import time



#site
url="https://www.epregistry.com.br/calculator"

#I don't want to display the window (to free up RAM...don't need to thank me)
options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=options)
#opening site
driver.get(url)


name_donor=input("what is the name of the donor dataset ? \n - ")
name_reciev=input("what is the name of the reciever dataset ? \n - ")

#lecture
donor= pd.read_csv(name_donor)
reciev=pd.read_csv(name_reciev)

#replace _ by : (XX:XX)
donor.replace(r'(\d{2})_(\d{2})', r'\1:\2', regex=True, inplace=True)
reciev.replace(r'(\d{2})_(\d{2})', r'\1:\2', regex=True, inplace=True)

#we add the name of the gene and * (Y*XX:XX)
donor = donor.apply(lambda col: col.name + '*' + col)
reciev= reciev.apply(lambda col: col.name + '*' + col)


#check the number of patient for donor and reciever
if reciev.shape[0]!= donor.shape[0]:
    quit()

nb_patient= donor.shape[0]
#table that will contain the mismatches
table=pd.DataFrame([{"MM_class_I": None, "MM_class_II": None}])


for row in range(nb_patient):
    print(f'-----{row}')
    
    #---recup the alleles to writte them on the website
    input_donor=""
    input_reciev=""
    for i in ("A","B","C","DQB1","DRB1"):
        input_donor=input_donor+f"{donor[i][row]} ,"
        input_reciev=input_reciev+f"{reciev[i][row]} ,"
   
    
    #---remove the last element of my news strings
    input_donor=input_donor[:-1]
    input_reciev=input_reciev[:-1]

    #input donor
    write_donor = driver.find_element(By.ID, "multiple-patients-immunizer-alleles")#find element (good form) in the HTML code
    write_donor.send_keys(input_donor)#fill the form
    
    #input reciever
    write_reciev = driver.find_element(By.ID, "multiple-patients-patient-alleles")
    write_reciev.send_keys(input_reciev)
    
    #deal with the cookie banner (it's a pain)
    erase_cook= driver.find_element(By.CLASS_NAME, "cc-dismiss")
    erase_cook.click()
    time.sleep(1)

    
    #click on the "result" button
    search_button=driver.find_element(By.XPATH, "//button[text()='Calculate']")
    driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
    time.sleep(1)
    
    search_button.click()
    

    time.sleep(3)

    #now, we want to get the results, but there are not available directly on the HTML code (they store the results in a dynamic file)
    #so we have to check the requests, and recuperate the file with the results (XHR type)...the name of that file is "eplet mismatches"

    for request in driver.requests:
        if request.response:
            if "eplet_mismatches" in request.url:#
                print(f"URL trouvée : {request.url}")
                
                #we get the file
                raw_body = request.response.body
    
                try:
                    #Decompression in gzip, because we want to read the file
                    with gzip.GzipFile(fileobj=io.BytesIO(raw_body)) as f:
                        decompressed = f.read()
                    text = decompressed.decode('utf-8')
                    
                    
                    #now, we can get the different mismatches 
                    data = json.loads(text)

                    
                    new_line = {"MM_class_I":data["ABC"]["quantity"] , "MM_class_II":data["DQ"]["quantity"] + data["DRB"]["quantity"]  }
                    table = pd.concat([table, pd.DataFrame([new_line])])
                    
    
                except Exception as e:
                    print("Erreur lors de la décompression ou du parsing JSON :", e)
    
    #its could be better honestly, but that work! (pb= RAM)
    driver.quit()
    time.sleep(5)
    driver = webdriver.Chrome(options=options)
    #ouverture du site
    driver.get(url)

#print(table)



table.reset_index(drop=True, inplace=True)
table.drop([0], inplace=True)
table.reset_index(drop=True, inplace=True)


table.to_csv("result_Mismatches_epi.csv", index=True)

    


