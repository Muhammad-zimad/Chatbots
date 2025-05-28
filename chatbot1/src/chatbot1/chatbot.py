 # Importing the necessary dependences
import chainlit as cl
from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from my_secret import Secrets   # Loading the Custom module where api key, model and baseurl are stored
from typing import cast
import json

# Load secrets credentials from environment
secrets = Secrets()

# This function runs when a new chat session starts

@cl.on_chat_start
async def start():
    msg = cl.Message(content="Welcome to the Zimad chatbot!, I am here to help you.")
    await msg.send()

 # Initialize the external client
    external_client = AsyncOpenAI(
        base_url=secrets.gemini_api_url,
        api_key=secrets.gemini_api_key,
    )
    set_tracing_disabled(True)

  # Creating Agent 
    agent = Agent(
        name="Chatbot",
        instructions="You are a helpful assistant. Which can precisely answer questions in a single sentence.",
        model=OpenAIChatCompletionsModel(
            openai_client=external_client,
            model=secrets.gemini_api_model,
        ),
    )

 # Save the agent and an empty chat history to the user's session
    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_history", [])

# Handling incoming user messages
@cl.on_message
async def main(message: cl.Message):
    # Create and send a placeholder message while processing
    msg = cl.Message(content="Thinking...")
    await msg.send()

     # Retrieve the AI agent from the session
    agent = cast(Agent, cl.user_session.get("agent"))
     # Get the chat history from the session
    chat_history: list = cl.user_session.get("chat_history") or []
     # Add the current user message to the history
    chat_history.append(
        {
            "role": "user",
            "content": message.content,
        }
    )

    try:
        result = Runner.run_sync(
            starting_agent=agent,
            input=chat_history,
        )
         # Update the placeholder message with the agent's response
        msg.content = result.final_output
        cl.user_session.set("chat_history", result.to_input_list())
        await msg.update()
    except Exception as e:
        
        msg.content = (
            "An error occurred while processing your request. Please try again."
        )
        await msg.update()
        print(e)
        
@cl.on_chat_end
def end():
    chat_history: list = cl.user_session.get("chat_history") or []
    with open("chat_history.json", "w") as f:
        json.dump(chat_history, f, indent=4)
    