#!/usr/bin/env python

from flask import Flask
from slackclient import SlackClient
from slackeventsapi import SlackEventAdapter

import wolframalpha

client = wolframalpha.Client('{WOLFRAM_API_KEY}')

# This is the Flask instance that our event handler will be bound to
# If you don't have an existing Flask app, the events api adapter
# will instantiate it's own Flask instance for you
app = Flask(__name__)

# Our app's Slack Event Adapter for receiving actions via the Events API
SLACK_VERIFICATION_TOKEN = "{SLACK_VERIFICATION_TOKEN}"
slack_events_adapter = SlackEventAdapter(SLACK_VERIFICATION_TOKEN, "/slack/events", app)

# Create a SlackClient for your bot to use for Web API requests
SLACK_BOT_TOKEN = "{SLACK_API_KEY}"
slack_client = SlackClient(SLACK_BOT_TOKEN)
# ------------------------------------------------------------------------------

@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]

    if message.get("subtype") is None:
        # Initialize the answer variable
        answer = ""

        # Input/Question from the user
        text = message.get('text')[13:]
        try:
            # Query Wolfram for user's question
            res = client.query(text)
            answer = next(res.results).text
        except UnicodeEncodeError:
            # If Wolfram didn't understand the user's question, show default text
            answer = 'Sorry I did\'t get you. Would you please simplify your query? %s is not valid input.' % text

        channel = message["channel"] 
       
        # Send the message to the user
        slack_client.api_call("chat.postMessage", channel=channel, text=answer)


# Start the Flask server on port 3000
if __name__ == '__main__':
    app.run(port=3000)
