#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import bs4
import requests
import re
import warnings
import pandas as pd
from time import sleep

# Suppress DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

BASE = "http://collegecatalog.uchicago.edu"
PROGRAM_STUDY = BASE+'/thecollege/programsofstudy/'
CURRICULUM = BASE+'/thecollege/thecurriculum/'

def scrape_department_data(url):
    '''Scrapes course data from the specified URL and returns it as a DataFrame.
    Output: A DataFrame containing course information including course number,
    descriptions, instructors, prerequisites, terms offered, and equivalent courses'''
    
    url = BASE + url
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    class1 = soup.find_all(class_=["courseblock main", "courseblock subsequence"])
    
    #ITERATING THROUGH CLASSES
    class_names = []
    descriptions = []
    instructors = []
    prerequisites = []
    terms = []
    equivalent_courses = []
    
    for i in range(len(class1)):
        name_unit_tag = class1[i].find("strong")
        if name_unit_tag:
            name_unit = name_unit_tag.string
            class_name = name_unit.split('.')[0].strip().replace("\xa0"," ")
        else:
            class_name= None
        
        description_element = class1[i].find(class_="courseblockdesc")
        if description_element:
            description = description_element.text.lstrip("\n")
        else:
            description = None
            
        instructor_element = class1[i].find(text=re.compile("Instructor"))
        if instructor_element:
            instructor_parts = instructor_element.split(':')
            if len(instructor_parts) > 2:
                instructor = instructor_parts[1].strip().replace("Terms Offered", "").strip()
                term = instructor_parts[2].strip().replace("\n", ",")
            else:
                instructor = instructor_parts[1].strip() if len(instructor_parts) > 1 else None
                term = None
        else:
            instructor = None
            term = None
        
        prerequisite_element = class1[i].find(text=re.compile("Prerequisite"))
        if prerequisite_element:
            prerequisite_parts = prerequisite_element.split(':')
            prerequisite = prerequisite_parts[1].strip() if len(prerequisite_parts) > 1 else None
        else:
            prerequisite = None
        
        # Extract equivalent_courses information, handling the case when it's not available
        equivalent_courses_element = class1[i].find(text=re.compile("Equivalent Course"))
        if equivalent_courses_element:
            equivalent_courses_parts = equivalent_courses_element.split(':')
            equivalent_course = equivalent_courses_parts[1].strip() if len(equivalent_courses_parts) > 1 else None
        else:
            equivalent_course = None
            
        # Append data to lists
        class_names.append(class_name)
        descriptions.append(description)
        instructors.append(instructor)
        prerequisites.append(prerequisite)
        terms.append(term)
        equivalent_courses.append(equivalent_course)
        
    # Create a DataFrame from the lists
    df = pd.DataFrame({
        "Course_Number": class_names,
        "Descriptions": descriptions,
        "Terms": terms,
        "Equivalent_Courses": equivalent_courses,
        "Prerequisites": prerequisites,
        "Instructor": instructors
    })
    return df

def extract_links(url):
    '''Extracts links from the specified URL'''
    programs = requests.get(url)
    soup = bs4.BeautifulSoup(programs.text, "html.parser")
    links = []
    ul_tag = soup.find("ul", class_="nav leveltwo")
    if ul_tag:
        links.extend([a["href"] for a in ul_tag.find_all("a", href=True)])
    return links


department_links = extract_links(PROGRAM_STUDY)
curriculum_links = extract_links(CURRICULUM)

#getting links that actually contain classes
curriculum_links_clean = curriculum_links[3:6] + curriculum_links[8:10]

dfs = []

#getting data from PROGRAM STUDY page and store them in dataframe
for department_link in department_links:
    df_department = scrape_department_data(department_link)
    dfs.append(df_department)
    sleep(3)
#getting data from CURRICULUM page store them in dataframe
for curriculum_link in curriculum_links_clean:
    df_curr = scrape_department_data(curriculum_link)
    dfs.append(df_curr)
    sleep(3)

#Combining list of dataframes into 1 dataframe
combined_df = pd.concat(dfs, ignore_index=True)

#Dropping classes that have NaN values for Course Number and conjugated classes
clean_df = combined_df.dropna(subset=["Course_Number"])
clean_df = clean_df[~clean_df["Course_Number"].str.contains("-")]

#removing duplicates
clean_df = clean_df.drop_duplicates(subset=["Course_Number"])
clean_df = clean_df.sort_values(by="Course_Number")
clean_df = clean_df.reset_index(drop=True)

#exporting the dataframe into a csv file
clean_df.to_csv('catalog.csv', index= False)    