import streamlit as st
import requests
import jwt
import datetime
import json
from graphlit_client import Graphlit

# Initialize session state variables if not already done
if 'client' not in st.session_state:
    st.session_state['client'] = None
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'summary_result' not in st.session_state:
    st.session_state['summary_result'] = None
if 'summarize_id' not in st.session_state:
    st.session_state['summarize_id'] = None
if 'session_conversation_id' not in st.session_state:
    st.session_state['session_conversation_id'] = None
if 'environment_id' not in st.session_state:
    st.session_state['environment_id'] = ""
if 'organization_id' not in st.session_state:
    st.session_state['organization_id'] = ""
if 'secret_key' not in st.session_state:
    st.session_state['secret_key'] = ""


def prompt_conversation(prompt, conversation_id):
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

    # Send the GraphQL request with the JWT token in the headers
    response = st.session_state['client'].request(query=mutation, variables=variables)
    st.session_state['session_conversation_id'] = response['data']['promptConversation']['conversation']['id']
    return response

st.title("Graphlit, Chat with Feed!")
if st.session_state['token'] is None:
    st.info("Generate token to get started!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
try:
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.sidebar:
            st.write("Conversation Id: {}".format(st.session_state["session_conversation_id"]))
        with st.chat_message("assistant"):
            result = prompt_conversation(prompt=prompt, conversation_id=st.session_state["session_conversation_id"])
            
            response = result['data']['promptConversation']['message']['message']
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
except:
    st.warning("Generate token to get started!")
    
with st.sidebar:
    with st.form("credentials_form"):
        st.info("Look into App Settings in Graphlit to get info!")
        st.session_state['secret_key'] = st.text_input("Secret Key", type="password")
        st.session_state['environment_id'] = st.text_input("Environment ID")
        st.session_state['organization_id'] = st.text_input("Organization ID")
        submit_credentials = st.form_submit_button("Generate Token")
    
if submit_credentials:
    if st.session_state['secret_key'] and st.session_state['environment_id'] and st.session_state['organization_id']:
        st.session_state['client'] = Graphlit(environment_id=st.session_state['environment_id'], organization_id=st.session_state['organization_id'], secret_key=st.session_state['secret_key'])
        st.session_state['token'] = st.session_state['client'].token
        print(st.session_state['token'])
        st.success("Token generated successfully!")
    else:
        st.error("Please fill in all the credentials.")

