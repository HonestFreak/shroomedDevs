import google.generativeai as genai
from fastapi import FastAPI
import os
import requests 
from dotenv import load_dotenv
from pathlib import Path
from fastapi_utilities import repeat_every
import email.utils
import smtplib

app = FastAPI()


env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("API")
GEMINI_API = os.getenv("GEMINI_API")
LIMIT = 10 

all_job_types = "full_time,part_time,freelance,internship,co_founder"


HOST = os.getenv('MAIL_SERVER')  # Update your environment variable names
PORT = os.getenv('MAIL_PORT')  # Update your environment variable names
FROM_EMAIL = os.getenv('MAIL_USERNAME')  # Update your environment variable names
PASSWORD = os.getenv('MAIL_PASSWORD')  # Update your environment variable names



@app.get("/get_all/" )
def get_all_jobs(limit: int = 10, page: int = 1, min_payment_usd: int = 0, job_types: str = all_job_types):
    url = f'https://api.crackeddevs.com/v1/get-jobs?limit={limit}&page={page}&min_payment_usd={min_payment_usd}&job_types={job_types}'
    headers = {
        'api-key': API_KEY,
    }

    response = requests.get(url, headers=headers)

    if response.ok:
        data = response.json()
        return data
    else:
        print("HTTP-Error:", response.status_code)

@app.get("/get_job_by_id/" ,tags=["Extension"])
def get_job_by_id(job_id: int):

    found = False
    i = 1
    while(found == False):
        url = f'https://api.crackeddevs.com/v1/get-jobs?limit=30&page={i}'
        headers = {
            'api-key': API_KEY,}
        response = requests.get(url, headers=headers)
        data = response.json()

        for job in data:
            if job['id'] == job_id:
                found = True
                return job
            elif(job['id'] < job_id):
                return 'not found'
        
        if(i > 30): return 'not found or data too old'
        i=i+1

@app.get("/get_job_by_title/" , tags=["Extension"])
def get_job_by_id(job_title: str, limit: int = 1):

    found = 0
    result = []
    i = 1
    while(found < limit):
        url = f'https://api.crackeddevs.com/v1/get-jobs?limit=30&page={i}'
        headers = {
            'api-key': API_KEY,}
        response = requests.get(url, headers=headers)
        data = response.json()

        for job in data:
            if job_title in job['title'].lower():
                print("found")
                found = found + 1
                result.append(job)   
                if(found == limit): return result       
        if(i > 30): return 'not found or data too old'
        i=i+1
    return result


@app.get("/ai_newletter/" , tags=["Newsletter"])
def AI_Newsletter_Generator(limit: int = 10):

    url = f'https://api.crackeddevs.com/v1/get-jobs?limit={limit}'
    headers = {
        'api-key': API_KEY,
    }

    response = requests.get(url, headers=headers)

    if response.ok:
        data = response.json()
    else:
        print("HTTP-Error:", response.status_code)

    genai.configure(api_key=GEMINI_API)
    gemini = genai.GenerativeModel('gemini-pro')
    prompt = "roleplay as a daily email newsletter , below is given your data, write email for your readers, make it catchy , use emojis too"
    chat = gemini.start_chat()
    ans =  chat.send_message(prompt + str(data)).text
    return ans


@app.post("/send_newsletter/", tags=["Newsletter"])
def send_newsletter(message: str, subject: str, emails: str):
    email_body = "\r\n".join([
        "From: %s" % FROM_EMAIL,
        "Subject: %s" % subject,
        message,
    ])
    to = emails.split(',')
    with smtplib.SMTP(HOST, PORT) as server:
        server.starttls()
        server.login(FROM_EMAIL, PASSWORD)
        for email in to:
            print("sending to", email)
            server.sendmail(FROM_EMAIL, email, email_body)
    return "Email sent successfully"


cronjob = False
emails = []

@app.post('/add_email_to_newsletter',tags=["Newsletter"])
def add_email_to_newsletter(email: str):
    emails.append(email)
    return "Email added successfully"

@app.on_event('startup')
@repeat_every(seconds=100, wait_first=False)
async def daily_cronjob():
    print("Cronjob running" , emails)
    if(cronjob):
        send_newsletter(AI_Newsletter_Generator(), "Daily Newsletter", ",".join(emails))
    
@app.get('/start_newsletter_cronjob',tags=["Newsletter"])
def start_newsletter_cronjob(start : bool = True):
    global cronjob
    cronjob = start
    if(start): return "Cronjob started successfully"
    else : return "Cronjob stopped successfully"

