import os
import time
import re
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.errors import HttpError

from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient({SLACK_API_KEY})
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
KEY_FILE_LOCATION = '{GOOGLE_KEY_FILE}'
VIEW_ID = '{GOOGLE_ANALYTICS_VIEW_ID}'

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    if command.startswith("count"):
        response = '`{} pageviews!`'.format(count(command))
    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

def initialize_analyticsreporting():
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      KEY_FILE_LOCATION, SCOPES)
  analytics = build('analytics', 'v4', credentials=credentials)
  return analytics
  

# def count():
#   analytics = initialize_analyticsreporting()
#   response = analytics.reports().batchGet(
#       body={
#         'reportRequests': [
#         {
#           'viewId': VIEW_ID,
#           'dateRanges': [{'startDate': '7daysAgo', 'endDate': 'today'}],
#           'metrics': [{'expression': 'ga:pageviews'}]
#         }]
#       }
#   ).execute()
#   answer = response['reports'][0]['data']['totals'][0]['values'][0]
#   return answer

def count(command):
    start_date = "7daysAgo"
    end_date = "today"
    words = command.split(' ')
    if 'from' in command:
        pos = words.index('from')
        start_date = command.split()[pos+1]
    if 'to' in command:
        pos = words.index('to')
        end_date = command.split()[pos+1]
    analytics = initialize_analyticsreporting()
    response = analytics.reports().batchGet(
        body={
            'reportRequests': [
            {
                'viewId': VIEW_ID,
                'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                'metrics': [{'expression': 'ga:pageviews'}]
            }]
        }
    ).execute()
    answer = response['reports'][0]['data']['totals'][0]['values'][0]
    return answer

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")


