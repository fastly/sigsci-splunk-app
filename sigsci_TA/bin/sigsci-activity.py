import sys, requests, os, calendar, json
from datetime import datetime, timedelta

# Initial setup
api_host = 'https://dashboard.signalsciences.net'
email = os.environ.get('SIGSCI_EMAIL')
password = os.environ.get('SIGSCI_PASSWORD')
corp_name = os.environ.get('SIGSCI_CORP')
site_name = corp_name = os.environ.get('SIGSCI_SITE_NAME')
showPassword = False

# Calculate UTC timestamps for the previous full hour
# E.g. if now is 9:05 AM UTC, the timestamps will be 8:00 AM and 9:00 AM
until_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
from_time = until_time - timedelta(minutes=60)
until_time = calendar.timegm(until_time.utctimetuple())
from_time = calendar.timegm(from_time.utctimetuple())


#Definition for error handling on the response code

def checkResponse(code, responseText):
    if code == 400:
        print("Bad API Request (ResponseCode: %s)" % (code))
        print("ResponseError: %s" % responseText)
        print('url: %s' % url)
        print('from: %s' % from_time)
        print('until: %s' % until_time)
        print('email: %s' % email)
        if showPassword is True:
            print('password: %s' % password)
        print('Corp: %s' % corp_name)
        print('SiteName: %s' % site_name)
        exit(code)
    elif code == 500:
        print("Caused an Internal Server error (ResponseCode: %s)" % (code))
        print("ResponseError: %s" % responseText)
        print('url: %s' % url)
        print('from: %s' % from_time)
        print('until: %s' % until_time)
        print('email: %s' % email)
        if showPassword is True:
            print('password: %s' % password)
        print('Corp: %s' % corp_name)
        print('SiteName: %s' % site_name)
        exit(code)
    elif code == 401:
        print("Unauthorized, likely bad credentials or site configuration, or lack of permissions (ResponseCode: %s)" % (code))
        print("ResponseError: %s" % responseText)
        print('email: %s' % email)
        if showPassword is True:
            print('password: %s' % password)
        print('Corp: %s' % corp_name)
        print('SiteName: %s' % site_name)
        exit(code)
    elif code >= 400 and code <= 599:
        print("ResponseError: %s" % responseText)
        print('url: %s' % url)
        print('from: %s' % from_time)
        print('until: %s' % until_time)
        print('email: %s' % email)
        if showPassword is True:
            print('password: %s' % password)
        print('Corp: %s' % corp_name)
        print('SiteName: %s' % site_name)
        exit(code)

# Authenticate
auth = requests.post(
    api_host + '/api/v0/auth/login',
    data = {"email": email, "password": password},
    allow_redirects=False
)
cookies = auth.cookies
location = auth.headers['Location']

authCode = auth.status_code
authError = auth.text

checkResponse(authCode, authError)

#print(auth.status_code)
#print(location)
#exit(0)

if location == '/login?p=invalid':
    print('Invalid login.')
    sys.exit()
elif location != '/':
    print('Unexpected error (location = {0})'.format(location))
    sys.exit()
    
#print(from_time)
# Loop across all the data and output it in one big JSON object
headers = {'Content-type': 'application/json'}
url = api_host + ('/api/v0/corps/%s/sites/%s/analytics/events?from=%s&until=%s' % (corp_name, site_name, from_time, until_time))
#url = api_host + ('/api/v0/corps/%s/sites/%s/feed/requests?from=%s' % (corp_name, site_name, from_time))
first = True



while True:
    response_raw = requests.get(url, cookies=cookies, headers=headers)
    responseCode = response_raw.status_code
    responseError = response_raw.text

    checkResponse(responseCode, responseError)


    response = json.loads(response_raw.text)
    
    # print(response['data'])

    for request in response['data']:
        output = json.dumps(request)
        print("%s" % output)

    if "next" in response:
        next_url = response['next']['uri']
        if next_url == '':
            break
        url = api_host + next_url
    else:
        break

