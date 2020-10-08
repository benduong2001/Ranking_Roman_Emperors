import numpy as np
import pandas as pd
#from nltk import tokenize
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer


import requests
#import re
from urllib.parse import urlparse
import urllib.robotparser
from bs4 import BeautifulSoup

wiki_list_emperor_url = r"https://en.wikipedia.org/wiki/List_of_Roman_emperors"

def canFetch(url):
    
    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(domain + "/robots.txt")
    try:
        rp.read()
        canFetchBool = rp.can_fetch("*", url)
    except:
        canFetchBool = None
    
    return canFetchBool
canFetch(wiki_list_emperor_url)

new_line = "\n"
empty_str = ""
excluded_str = [new_line, empty_str]
def excluded_strs_filter(word):
    '''
    Input: str; Output: bool; 
    Purpose: This function is only meant to be a filter for any unnecessary pitfalls common with text analysis. \
    Newlines like \n , and empty "ghost" strings like "" can show up despite not being easily visible. \
    This function is used mainly in the context after us making a list of words from a body of text. Like this \
    
    list(filter(excluded_strs_filter, text.split()))
    
    Where the variable text is the body of text itself.
    '''
    new_line = "\n"
    empty_str = ""
    excluded_str = [new_line, empty_str]
    if word in excluded_str:
        return False
    else:
        return True

def remove_header(row):
    '''
    In the wikipedia page's list of Roman Emperors, there are different tables for each era of Roman history
    We will iterate through each of the tables, and iterate through each of the rows in that table
    However, each table has a header row for the names of the columns, like Portrait, Name, Birth, Succession, etc. 
    '''
    row_1 = list(filter(excluded_strs_filter, row))
    first_header = row_1[0]
    first_header_text = (first_header).text
    if "Portrait" in first_header_text:
        return False
    else:
        return True

def wikitable_row_emperor(row):
    '''
    This is the function that actually retrieves the hyperlink for each individual Roman Emperor in the table. \
    After having the header rows removed from each of the tables in the wikipedia's list of Roman Emperors, \
    I will access the second column of the row, which will be the web element containing the emperor's name and likewise, \
    the href attribute to their own article. \
    However, in case the web element is not a hyperlink, (no href attribute), I had to put everything I described above \
    with try and except. 
    '''
    try:
        name_column = row[1] #
        b_tag = name_column.contents[0]
        a_name = b_tag.contents[0]
        a_href = a_name['href']
        return a_href
    except:
        return None

list_emperors_page = requests.get(wiki_list_emperor_url)
soup = BeautifulSoup(list_emperors_page.text, 'html.parser')

#For understandable naming convention, I simply reused the name of one variable 
#but gave them numbers according to their order in this python script

rows_0 = soup.find_all('tr')

#For each of the rows in rows_0, I try to remove the header row, which do not contain the href attributes to each emperor's
#individual wikipedia webpage
rows_1 = list(filter(remove_header, rows_0))

#But rows_1 still contained several troublesome details that would complicate my webscraping like empty strings, newlines, etc.
#So I apply excluded_strs_filter
rows_2 = [list(filter(excluded_strs_filter, row.contents)) for row in rows_1]

# Here, we apply the function wikitable_row_emperor, to actually get the href from the row
#giving us the list of href to each emperor's wikipedia page
rows_3 = list(map(wikitable_row_emperor, rows_2))

# But we are not done yet. We need to filter the None's, which we set up to be returned just in case no href-attribute
#existed for us to get, in the function wikitable_row_emperor
emperor_hrefs_0 = list(filter(lambda x: x != None, rows_3))

def test_all_hrefs_working():
    # test all hrefs are working
    for emperor_href in emperor_hrefs_0:
        print(emperor_href)
print("processed all hrefs")
# We have finished getting the list of all Roman emperors from the wikipedia page.
# However, the list also includes Byzantine emperors. 

# As a brief history lesson, the Roman empire's life is usually divided into 2 main eras:
# the Western Roman Empire- when the empire was centered in Rome,
# and the Eastern Byzantine Empire - when the empire was centered in Constantinople (modern day Istanbul) after the western half collapsed. 
# For my project, I will restrict the emperors to just the western emperors.
# Traditionally, -and this is very simplified- historians regard [Romulus Augustulus](https://www.britannica.com/biography/Romulus-Augustulus) as the "last emperor".
# So I will trim off the list after Romulus Augustulus.

last_western = '/wiki/Romulus_Augustulus'
last_western_index = emperor_hrefs_0.index(last_western)
emperor_hrefs_1 = emperor_hrefs_0[:last_western_index + 1]
try:
    assert emperor_hrefs_1[-1] == '/wiki/Romulus_Augustulus'
except:
    print(emperor_hrefs_1[-1])

# We will webscrape the paragraphs of the biography pages of the emperor,which conveniently all follow a predictably uniform format.
# We will, however, need to do some manual cleaning of the text.
# For each paragraph, within the text itself, there are moments where wikipedia writers insert additional inner tags like hyperlinks to other articles like a tags, and sup tags for superscripted citation numbers or other texts. 
# We need an if statement that tests the current line's data type. 
# * If it is a navigable String (bs4's type of string), it is kept.
# * If it is an htmltag, we actually can't simply remove it. We must retrieve the text nested inside it. This is especially true with "a" tags, where the hyperlink text is part of the sentence itself.

def soup_emperor(url):
    url_text = requests.get(url)
    soup = BeautifulSoup(url_text.text, 'html.parser')
    return soup
def parse_emperor(soup):
    all_text = ""
    paragraphs = soup.find_all("p")
    for paragraph in paragraphs:
        paragraph_str = ""
        for clause in paragraph.contents:
            
            if str(type(clause)) == "<class 'bs4.element.NavigableString'>":
                clause = "".join(clause.split("\n"))
                paragraph_str += str(clause)
            elif str(type(clause)) ==  "<class 'bs4.element.Tag'>":
                clause_text = str(clause.text)
                clause_text = "".join(clause_text.split("\n"))
                paragraph_str += str(clause_text) #'''
        all_text += " " + paragraph_str
    return all_text

all_emperors_dict = []
def iterate_emperors(emperor_hrefs):
    for emperor_href in emperor_hrefs:
        url = "https://en.wikipedia.org"+emperor_href
        souped_emperor = soup_emperor(url)
        parsed_emperor = parse_emperor(souped_emperor)
        name = emperor_href.split("/")[-1]
        emp_dict = {"Name": name, "Text": parsed_emperor}
        all_emperors_dict.append(emp_dict)
iterate_emperors(emperor_hrefs_1)




nltk.download('punkt')
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

Emperor_Sentiments = []
for emperor_dict in all_emperors_dict:
    Emperor_Sentiment = sia.polarity_scores(emperor_dict['Text'])
    Emperor_Sentiment['Name'] = emperor_dict['Name']
    Emperor_Sentiments.append(Emperor_Sentiment)
Emperor_Sentiments_Df = pd.DataFrame(Emperor_Sentiments)

Emperor_Sentiments_Df_Ranked = Emperor_Sentiments_Df.sort_values('compound')

Best_20_Emperors = Emperor_Sentiments_Df_Ranked['Name'][-20:][::-1]
print(Best_20_Emperors)

Worst_20_Emperors = Emperor_Sentiments_Df_Ranked['Name'][:20]
print(Worst_20_Emperors)

