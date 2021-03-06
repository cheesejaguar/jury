import httplib
import re
from bs4 import BeautifulSoup
from datetime import datetime
import twitter
import cPickle as pickle
import time

def crawl():
    url = '/online_services/jury/jury_duty_weekly_status.shtml'
    connection = httplib.HTTPConnection('www.scscourt.org')
    connection.request('GET', url)
    response = connection.getresponse()
    result_str = response.read()
    connection.close()
    if result_str == "":
        print "Error."
        return
    else:
        return result_str

def concat(string):
    result = ''
    for each in string:
            result+=each
    return result

def atMe(input):
    try:
        mentions = api.GetMentions()
    except:
        print "API Error?"
    toRespond = []
    responseStr = ''
    for each in mentions:
        try:
            toRespond.append({'id' : each.id, 'groupNo' : int(each.text.split(' ')[2].encode('ascii','ignore')), 'username' : each.user.screen_name.encode('ascii','ignore')})
        except:
            print "Oops"
    for each in toRespond:
        #responseStr = "@" + each['username'] + " Group number " + str(each['groupNo']) + " reports at BLAH BLAH BLAH"
        #print responseStr
        success = 0
        for group in input:
            if each['groupNo'] in range(int(group.groupRange[0]), int(group.groupRange[1])+1):
                responseStr = "@" + each['username'] + " " + group.report()
                api.PostUpdate(responseStr,in_reply_to_status_id=each['id'])
                success = 1
        if success == 0:
            responseStr = "@" + each['username'] + " Sorry, we cant find that group number, or our web robot had a problem"
            api.PostUpdate(responseStr,in_reply_to_status_id=each['id'])
        time.sleep(60) #Don't spam twitter API
    return toRespond[-1]['id'] #returns ID of most recent @


class juryGroup:
    def __init__(self,input):
        self.columns = input.find_all('td')
        groupRange = self.columns[0].text.encode('ascii')
        self.groupRange = groupRange.split(' thru ')
        self.instructions = self.columns[1].text.encode('ascii')
        rawTime = self.columns[3].text.encode('ascii','ignore').split(' ')
        self.called = 0
        if len(rawTime) is 2: #time
            Time = concat(rawTime)
            self.called = 1
        elif len(rawTime) is 3:
            Time = concat(rawTime[1:]) #After time
            self.called = 0
        elif len(rawTime) is 6: #Between 11 and noon BS
            Time = concat(rawTime[1:3])
            self.called = 0
        else:
            Time = 0
        Date = self.columns[2].text.encode('ascii')
        timestamp = str(Time) + ' ' + Date
        self.datetime = datetime.strptime(timestamp, '%I:%M%p %m-%d-%y')
        self.Location = self.columns[4].text.encode('ascii')
    def belongs(self, myGroup):
        if myGroup in range(int(self.groupRange[0]),int(self.groupRange[1])+1):
            return 1
        else:
            return 0
    def report(self):
        if self.called is 1:
            return 'Groups ' + str(self.groupRange[0]) + ' to ' + str(self.groupRange[1]) + ' please report to ' + self.Location + ' at ' + self.datetime.strftime('%A, %B %d')
        else:
            return 'Groups ' + str(self.groupRange[0]) + ' to ' + str(self.groupRange[1]) + ' please check again after ' + self.datetime.strftime('%I:%M%p') + ' on ' + self.datetime.strftime('%A, %B %d')

#Load twitter keys, this file is NOT in github
with open('key.pickle', 'rb') as fp:
    keys = pickle.load(fp)

#Initialize twitter API access
api = twitter.Api(consumer_key=keys['consumer_key'],
                  consumer_secret=keys['consumer_secret'],
                  access_token_key=keys['access_token'],
                  access_token_secret=keys['access_token_secret'])

#main garbage
soup = BeautifulSoup(crawl())
table_rows = soup.find_all('tr')
output = []
queue = []
badrow = []
for each in table_rows:
    try:
        output.append(juryGroup(each))
        if datetime.now() < output[-1].datetime:
            queue.append(output[-1].report())
    except ValueError:
        badrow.append(each)
#Tweet all report times in the future
for each in queue:
    api.PostUpdate(each)
    time.sleep(60) #Don't spam twitter API
print "Queue Complete"

#Respond to GetMentions
recentID = atMe(output)
