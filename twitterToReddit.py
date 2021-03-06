# Import required libraries/files
import praw
import tweepy
import re
import time
import os
print("********************************")
print("Running")
# Reddit REST API connection initialization
reddit = praw.Reddit(client_id = os.environ['REDDIT_CLIENT_ID'], 
    client_secret = os.environ['REDDIT_CLIENT_SECRET'], 
    user_agent = os.environ['REDDIT_USER_AGENT'], 
    username = os.environ['REDDIT_USERNAME'], 
    password = os.environ['REDDIT_PASSWORD']
)

reddit.validate_on_submit = True
# Twitter API connection
auth = tweepy.OAuthHandler(os.environ['TWITTER_CONSUMER_KEY'], os.environ['TWITTER_CONSUMER_SECRET'])
auth.set_access_token(os.environ['TWITTER_ACCESS_TOKEN'], os.environ['TWITTER_ACCESS_TOKEN_SECRET'])
api = tweepy.API(auth, wait_on_rate_limit = True)

# Intialize variables
errors = 0
copyFrom = os.environ['TWITTER_USERNAME']
postTo = os.environ['REDDIT_SUB']
expanded_url=''
post_text = ''
title = ''

# Method to only get tweets posted by the user
def from_creator(status):
    if hasattr(status, 'retweeted_status'):
        return False
    elif status.in_reply_to_status_id != None:
        return False
    elif status.in_reply_to_screen_name != None:
        return False
    elif status.in_reply_to_user_id != None:
        return False
    else:
        return True

# Stream intialization
class listener(tweepy.StreamListener):
    global expanded_url
    global post_text
    global title

    # When stream finds a new tweet do the following
    def on_status(self, status):
        if from_creator(status):
            newTweet = status
            
            title = "Courtesy of Fortnite's Official Twitter: "
            # Remove URL from title
            if 'extended_tweet' in newTweet._json:
                tweet = newTweet._json['extended_tweet']['full_text']
                title += re.sub(r'http\S+', '', tweet)
            else:
                tweet = newTweet._json['text']
                title += re.sub(r'http\S+', '', tweet)

            # Prepare reddit post
            mediaUrl = []

            # If tweet has URL
            if newTweet.entities['urls']!=[]:
                print("********************************")
                print("Tweet has URL")
                expanded_url = newTweet.entities['urls'][0].get('expanded_url')
                url = newTweet.entities['urls'][0].get('url')

            # If tweet has media
            elif 'media' in newTweet.entities:
                print("********************************")
                print("Tweet has Media")
                for media in newTweet.extended_entities['media']:
                    mediaUrl.append(media['media_url'])

                if len(mediaUrl) == 1:
                    expanded_url = mediaUrl
                    url = None
                elif len(mediaUrl) > 1:
                    post_text = ""
                    for item in mediaUrl:
                        post_text += item + "\n\n"
                    expanded_url = None
                    url = None

            # If tweet is only text
            else:
                print("********************************")
                print("Tweet has Only Text")
                post_text = ""
                expanded_url = "https://twitter.com/" + status.user.screen_name + "/status/" + str(status.id)
                url = None

            # If title would be blank
            if title == url:
                title = "Fortnite Twitter"

            global postTo
            global errors

            try:

                # ID for DISCUSSION flair
                flair_id = '9c53efac-cd94-11e7-8824-0eba7e80ccec'
                
                # If there is a URL in the tweet
                if expanded_url != None:
                    subreddit = reddit.subreddit(postTo)
                    post = subreddit.submit(title, url = expanded_url, flair_id = flair_id)
                    print("Posted to " + postTo)
                    print("Title: " + title)

                # If there is no URL in the tweet
                else:
                    subreddit = reddit.subreddit(postTo)
                    post = subreddit.submit(title, selftext = post_text, flair_id = flair_id)
                    print("Posted to " + postTo)
                    print("Title: " + title)


            # Given a rate limit exception
            except praw.exceptions.APIException as e:
                print(e.message)

                if(e.error_type == "RATELIMIT"):
                    delay = re.search("(\d+) minutes?", e.message)

                    if delay:
                        delay_seconds = float(int(delay.group(1)) * 60)
                        time.sleep(delay_seconds)
                        post()
                    else:
                        delay = re.search("(\d+) seconds", e.message)
                        delay_seconds = float(int(delay.group(1)))
                        time.sleep(delay_seconds)
                        post()

            except:
                errors = errors + 1
                if (errors > 5):
                    print("Crashed")
                    exit(1)

if __name__ == "__main__":

    # Sets up listener to monitor @FortniteGame continuously for new tweets
    myListener = listener()
    stream = tweepy.Stream(auth = api.auth, listener = myListener, tweet_mode = 'extended')
    stream.filter(follow=[copyFrom])
