import glob
import os
import warnings
import traceback
import extractEntities as entity
from gensim.summarization import summarize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import getCategory as skills
import pandas as pd
from extract_exp import ExtractExp


warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')

class ResultElement:
    def __init__( self,jd, filename,skillRank, name, phoneNo, email, nonTechSkills,exp,
                 finalRank,skillList,nonTechskillList):
        self.jd = jd
        self.filename = filename
        self.skillRank = skillRank
        self.name = name
        self.phoneNo = phoneNo
        self.email = email
        self.nonTechSkills = nonTechSkills
        self.exp = exp
        self.finalRank = finalRank
        self.skillList = skillList
        self.nonTechskillList = nonTechskillList


def getfilepath(loc):
    temp = str(loc)
    temp = temp.replace('\\', '/')
    return temp

def res(jobfile,skillset,jd_exp):
    Resume_Vector = []
    Resume_skill_vector = []
    min_qual_vector = []
    is_min_qual = []
    Resume_skill_list = []
    Resume_non_skill_list = []
    Resume_email_vector = []
    Resume_phoneNo_vector = []
    Resume_ApplicantName_vector = []
    Resume_name_vector = []
    Resume_nonTechSkills_vector = []
    Resume_exp_vector = []
    Ordered_list_Resume = []
    LIST_OF_FILES = []
    LIST_OF_FILES_PDF = []
    Resumes = []
    Temp_pdf = []
    Resume_title = []

    jd_weightage = 15
    not_found = 'Not Found'
    extract_exp = ExtractExp()
    
    resumePath = 'resumeFiltered'
    
    for file in glob.glob(resumePath+'/*.pdf'):
        LIST_OF_FILES_PDF.append(file)

    LIST_OF_FILES = LIST_OF_FILES_PDF

    
    for count,i in enumerate(LIST_OF_FILES):
       
        Temp = i.rsplit('.', 1)
        Resume_title.extend(str(i))
        if Temp[1] == "pdf" or Temp[1] == "Pdf" or Temp[1] == "PDF":
            try:
                print(count," This is PDF" , i)
                with open(i,'rb') as pdf_file:
                    
                    read_pdf = PyPDF2.PdfFileReader(pdf_file)


                    number_of_pages = read_pdf.getNumPages()
                    for page_number in range(number_of_pages): 

                        page = read_pdf.getPage(page_number)
                        page_content = page.extractText()
                        page_content = page_content.replace('\n', ' ')
   
                        Temp_pdf = str(Temp_pdf) + str(page_content)

                    Resumes.extend([Temp_pdf])
                    Temp_pdf = ''
                    Ordered_list_Resume.append(i)

            except Exception as e: 
                print(e)
                print(traceback.format_exc())


    Job_Desc = 0
    
    try:
        tttt = str(jobfile)
        tttt = summarize(tttt, word_count=100)
        text = [tttt]
    except:
        text = 'None'

    
    vectorizer = TfidfVectorizer(stop_words='english')

    vectorizer.fit(text)
    vector = vectorizer.transform(text)

    Job_Desc = vector.toarray()

    tempList = Ordered_list_Resume 
    #os.chdir('../')
    final_result = []
    for index,i in enumerate(Resumes):

        text = i
        temptext = str(text)
        tttt = str(text)
       
        
        try:
            tttt = summarize(tttt, word_count=100) 
            text = [tttt]
            vector = vectorizer.transform(text)
            Resume_Vector.append(vector.toarray())
            Resume_skill_vector.append(skills.programmingScore(temptext,jobfile+skillset))
            Resume_skill_list.append(skills.skillSetListMatchedWithJD())
            Resume_non_skill_list.append(skills.nonTechSkillSetListMatchedWithJD())
            experience = extract_exp.get_features(temptext)
            Resume_name_vector.append(experience)
            temp_applicantName = entity.extractPersonName(temptext, Resume_title[index])
            Resume_ApplicantName_vector.append(temp_applicantName)
            temp_phone = entity.extract_phone_numbers(temptext)
            if(len(temp_phone) == 0):
                Resume_phoneNo_vector.append(not_found)
            else:
                 Resume_phoneNo_vector.append(temp_phone)
            temp_email = entity.extract_email_addresses(temptext)
            if(len(temp_email) == 0):
                Resume_email_vector.append(not_found)
            else:
                 Resume_email_vector.append(temp_email)
                
           
            Resume_exp_vector.append(extract_exp.get_exp_weightage(str(jd_exp),experience))
            Resume_nonTechSkills_vector.append(skills.NonTechnicalSkillScore(temptext,jobfile+skillset))
            print("Rank prepared for ",Ordered_list_Resume.__getitem__(index))
        except Exception:
            print(traceback.format_exc())
            tempList.__delitem__(index)
            
   
    for index,i in enumerate(Resume_Vector):

        samples = i
        similarity = cosine_similarity(samples,Job_Desc)[0][0]
        """Ordered_list_Resume_Score.extend(similarity)"""
        final_rating = round(similarity*jd_weightage,2)+Resume_skill_vector.__getitem__(index)+Resume_nonTechSkills_vector.__getitem__(index)+Resume_exp_vector.__getitem__(index)
        res = ResultElement(round(similarity*jd_weightage,2), os.path.basename(tempList.__getitem__(index)),round(Resume_skill_vector.__getitem__(index),2),
                           Resume_ApplicantName_vector.__getitem__(index), Resume_phoneNo_vector.__getitem__(index),Resume_email_vector.__getitem__(index),
                           Resume_nonTechSkills_vector.__getitem__(index),Resume_exp_vector.__getitem__(index),round(final_rating,2),Resume_skill_list.__getitem__(index),
                           Resume_non_skill_list.__getitem__(index))
        final_result.append(res)
    final_result.sort(key=lambda x: x.finalRank, reverse=True)
    return final_result


def printByRanks():
    results = []
    jdFolder = "./jobReq"
    data_set = ""
    for file in os.listdir(jdFolder):

        data_set = pd.read_excel(jdFolder + "\\" + file)
   
        search_st = data_set['High Level Job Description'][0]
        skill_text = data_set['Technology'][0] + data_set['Primary Skill'][0]
        jd_exp = data_set['Yrs Of Exp '][0]
        title = data_set['Job Title'][0]
 
        flask_return = res(search_st,skill_text,jd_exp) 
        for i in range(len(flask_return)):
            print("in flask_return")
            resultItem = []
            resultItem.append(flask_return[i].filename)
            resultItem.append(flask_return[i].email)
            resultItem.append(flask_return[i].finalRank)
            results.append(resultItem)
    return results
