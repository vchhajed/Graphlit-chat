import streamlit as st
import requests
import jwt
import datetime
import json


def create_token():
    # Define the issuer and audience
    issuer = "graphlit"
    audience = "https://portal.graphlit.io"

    # Specify the role (Owner, Contributor, Reader)
    role = "Owner"

    # Specify the expiration (one hour from now)
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    # Define the payload
    payload = {
        "https://graphlit.io/jwt/claims": {
            "x-graphlit-environment-id": environment_id,
            "x-graphlit-organization-id": organization_id,
            "x-graphlit-role": role,
        },
        "exp": expiration,
        "iss": issuer,
        "aud": audience,
    }

    # Sign the JWT
    token = jwt.encode(payload, secret_key, algorithm="HS256") 
    return token

def graphlit_request(mutation, variables, func):
    url = 'https://data-scus.graphlit.io/api/v1/graphql'
    graphql_request = {'query': mutation, 'variables': variables}
    headers = {'Authorization': 'Bearer {}'.format(st.session_state['token'])}

    response = requests.post(url, json=graphql_request, headers=headers)

    if response.status_code == 200:
        st.success(f"{func} was successful!")
        # Display some part of the response, e.g., the created feed's ID

        response_data = response.json()
        st.json(response.json())
    else:
        st.error(f"GraphQL request failed with status code: {response.status_code}")
        st.text(f"Response: {response.text}")

def send_request(name, uri):
    url = 'https://data-scus.graphlit.io/api/v1/graphql'
    mutation = """
    mutation CreateFeed($feed: FeedInput!) {
        createFeed(feed: $feed) {
            id
            name
            state
            type
        }
    }
    """
    variables = {
        "feed": {
            "type": "WEB",
            "web": {
                "uri": uri
            },
            "name": name
        }
    }
    graphlit_request(mutation, variables, "feed creation")

def list_feeds():
    # Define the GraphQL mutation
    query = """
    query QueryFeeds($filter: FeedFilter!) {
        feeds(filter: $filter) {
            results {
            id
            name
            creationDate
            state
            owner {
                id
            }
            type
            reddit {
                subredditName
            }
            lastPostDate
            lastReadDate
            readCount
            schedulePolicy {
                recurrenceType
                repeatInterval
            }
            }
        }
    }
    """

    # Define the variables for the mutation
    variables = {
    "filter": {
        "offset": 0,
        "limit": 100
    }
    }
    graphlit_request(query, variables, "show list")


# Initialize session state variables if not already done
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'summary_result' not in st.session_state:
    st.session_state['summary_result'] = None
if 'summarize_id' not in st.session_state:
    st.session_state['summarize_id'] = None
if 'session_conversation_id' not in st.session_state:
    st.session_state['session_conversation_id'] = None

def prompt_conversation(prompt, conversation_id):
    # Define the GraphQL endpoint URL
    url = 'https://data-scus.graphlit.io/api/v1/graphql'

    # Define the GraphQL mutation
    mutation = """
    mutation PromptConversation($prompt: String!, $id: ID) {
    promptConversation(prompt: $prompt, id: $id) {
        conversation {
        id
        }
        message {
        role
        author
        message
        tokens
        completionTime
        }
        messageCount
    }
    }
    """

    # Define the variables for the mutation
    if st.session_state['session_conversation_id']:
        variables = {
            "prompt": prompt,
            "id": conversation_id
        }
    else:
        variables = {
            "prompt": prompt
            }
        

    # Create a dictionary representing the GraphQL request
    graphql_request = {
        'query': mutation,
        'variables': variables
    }

    # Convert the request to JSON format
    graphql_request_json = json.dumps(graphql_request)

    # Include the JWT token in the request headers
    headers = {'Authorization': 'Bearer {}'.format(st.session_state['token'])}

    # Send the GraphQL request with the JWT token in the headers
    response = requests.post(url, json=graphql_request, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the response content
        print(response.json())
        st.session_state['session_conversation_id'] = response.json()['data']['promptConversation']['conversation']['id']
        
    else:
        print('GraphQL request failed with status code:', response.status_code)
        print('Response:', response.text)
    return response.json()

def create_token(secret_key, environment_id, organization_id):
    # Define the issuer and audience
    issuer = "graphlit"
    audience = "https://portal.graphlit.io"

    # Specify the role (Owner, Contributor, Reader)
    role = "Owner"

    # Specify the expiration (one hour from now)
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    # Define the payload
    payload = {
        "https://graphlit.io/jwt/claims": {
            "x-graphlit-environment-id": environment_id,
            "x-graphlit-organization-id": organization_id,
            "x-graphlit-role": role,
        },
        "exp": expiration.timestamp(),  # Ensure this is a Unix timestamp
        "iss": issuer,
        "aud": audience,
    }

    # Sign the JWT
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

st.title("Graphlit, Chat with Feed!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        result = prompt_conversation(prompt=prompt, conversation_id=st.session_state["session_conversation_id"])
        print(result)
        response = result['data']['promptConversation']['message']['message']
        print(response)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    
with st.sidebar:
    with st.form("credentials_form"):
        st.info("Look into App Settings in Graphlit to get info!")
        secret_key = st.text_input("Secret Key", type="password")
        environment_id = st.text_input("Environment ID")
        organization_id = st.text_input("Organization ID")
        submit_credentials = st.form_submit_button("Generate Token")
    
if submit_credentials:
    if secret_key and environment_id and organization_id:
        st.session_state['token'] = create_token(secret_key, environment_id, organization_id)
        st.success("Token generated successfully!")
    else:
        st.error("Please fill in all the credentials.")

