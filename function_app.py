import azure.functions as func
import logging
import pymongo
import json
from urllib.parse import parse_qs
import datetime
from openai import OpenAI
# from rest_framework.decorators import api_view


aiClient = OpenAI(
    api_key="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",
    organization="org-xXEIzn6NYiho80LJJUG2sI2l"
)
client = pymongo.MongoClient("mongodb://azure-backend-me:wC809DyYS0SH3H9lWXqYOJwvLWxjF14t1Jql1Jk4lMfsbOnD1Ybx19JjfZK4tclzscJbU354ehoWACDbLL0KKg==@azure-backend-me.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000&appName=@azure-backend-me@")
database_name = 'meDB'
database = client[database_name]
users = database['users']
prompts = database['prompts']

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="azure_backend_ME")
def azure_backend_ME(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )


# @api_view(['GET'])
@app.route(route="users/register/")
def registerUser(req:func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()

        # Extracting user information from the request body
        name = req_body.get('name')
        email = req_body.get('email')
        # username = req_body.get('username')
        password = req_body.get('password')

        # Checking if all required fields are present
        if not (name and email and password):
            return func.HttpResponse(
                "Please provide all required fields: first_name, email, username, password",
                status_code=400
            )

        # Check if the email is already taken
        if users.find_one({"email": email}):
            return func.HttpResponse(
                "Email already exists. Please choose a different one.",
                status_code=409
            )

        # Create a new user record
        new_user = {
            "name": name,
            "email": email,
            "username": email,
            "password": password,
            "admin": False
        }
        users.insert_one(new_user)

        # Fetch the created user record and send it back to the user
        created_user = users.find_one({"email": email})
        if created_user:
            # del created_user["_id"]  # Removing MongoDB ObjectId from the response
            return func.HttpResponse(
                json.dumps(created_user, indent=4, sort_keys=True, default=str),
                mimetype="application/json",
                status_code=201
            )
        else:
            return func.HttpResponse(
                "Failed to fetch user data.",
                status_code=500
            )
    except Exception as e:
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )
    
@app.route('users/login')
def loginUser(req:func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()

        # Extracting login information from the request body
        email = req_body.get('email')
        password = req_body.get('password')

        # Checking if all required fields are present
        if not (email and password):
            return func.HttpResponse(
                "Please provide both email and password.",
                status_code=400
            )

        # Check if the user exists with the provided email and password
        user = users.find_one({"email": email, "password": password})

        if user:
            
            return func.HttpResponse(
                json.dumps(user, indent=4, sort_keys=True, default=str),
                mimetype="application/json",
                status_code=200
            )
        else:
            return func.HttpResponse(
                "Invalid email or password.",
                status_code=401
            )
    except Exception as e:
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )
    
@app.route('prompts/send-prompt')
async def sendPrompt(req:func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()

        # OPEN_API_KEY = "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"
        # OPENAI_ORGANISATION="org-xXEIzn6NYiho80LJJUG2sI2l"

        # aiClient.api_key = OPEN_API_KEY
        # aiClient.organization = OPENAI_ORGANISATION

        email = req_body.get('email')
        prompt = req_body.get('prompt')

        response = aiClient.chat.completions.create( 
            model='gpt-3.5-turbo',
            messages = [
                {"role":"system","content":prompt},
            ]
        )

        answer = response.choices[0].message.content

        if not (email and prompt):
            return func.HttpResponse(
                "Please provide both email and prompt.",
                status_code=400
            )
        
        user = users.find_one({"email": email})
        if user:
            new_prompt = {
                'user':email,
                'prompt':prompt,
                'response':answer,
                'createdAt':datetime.datetime.now()
            }
            created_prompt = prompts.insert_one(new_prompt)

            return func.HttpResponse(
                json.dumps(new_prompt, indent=4, sort_keys=True, default=str),
                mimetype="application/json",
                status_code=201
            )
        else:
             return func.HttpResponse(
                "Invalid user email",
                status_code=401
            )
    
    except Exception as e:
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )

@app.route('prompts/get-records')
async def getPromptRecords(req:func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()

        email = req_body.get('email')
        # logging.info(email)
        # prompt = req_body.get('prompt')

        # response = "qwertyuiop1234567"

        if not (email):
            return func.HttpResponse(
                "Please provide valid user email.",
                status_code=400
            )
        
        prompts_list = prompts.find({"user":email})

        if prompts_list is not None:
            prompts_list = list(prompts_list)
            # logging.info(prompts_list)
            return func.HttpResponse(
                json.dumps(prompts_list, indent=4, sort_keys=True, default=str),
                mimetype="application/json",
                status_code=201
            )
        else:
             return func.HttpResponse(
                "No prompt history",
                status_code=401
            )
    
    except Exception as e:
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )