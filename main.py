import requests
import json
from datetime import datetime, timedelta
from math import ceil, floor

# get results from the 6x/minute updated politico results, bypassing the need for an AP elections API key
resp = requests.get('https://www.politico.com/2020-national-results/president-overall.json').json()

# load json that holds previous results
with open('history.json', 'r') as f:
    history = json.load(f)

# load file that contains mapping information to transalte the results json to useful numbers
# {
#   {{state_id}}: {
#     state_name: {{2 letter state ID}},
#     t_id: {{5 digit candidate ID for trump}},
#     b_id: {{5 digit candidate ID for biden}}
#   }, ...
# }
with open('state_info.json', 'r') as f:
    state_info = json.load(f)

# given a state ID and the candidate ids, return the nummber of votes for each, whether that state has been called, and the percentage of votes received
def get_votes(t_id, b_id, state):
    progress = state['progressPct']
    for candidate in state['candidates']:
        if candidate['candidateID'] == t_id:
            trump_votes = int(candidate['vote'])
            trump_win = bool(candidate['winner'])
        elif candidate['candidateID'] == b_id:
            biden_votes = int(candidate['vote'])
            biden_win = bool(candidate['winner'])
    
    result = {
        'progress': progress,
        'trump_votes': trump_votes,
        'trump_win': trump_win,
        'biden_votes': biden_votes,
        'biden_win': biden_win
    }
    return result

# print out the last time that votes were received, converting the files date_stamp to a standard dt object 
last_updated = datetime.strptime(resp.get('lastUpdated'),'%Y-%m-%dT%H:%M:%S+00:00')
now = datetime.now() + timedelta(hours=5)
print(f'last updated: {ceil((now-last_updated).total_seconds()/60)} minute(s) ago')


race_dict = resp['races']
for state in race_dict:
    state_id = state['stateFips']
    
    # skip irrelevant states
    if state_id not in state_info.keys():
        continue

    state_details = state_info[state_id]
    state_name = state_details['state_name']

    result = get_votes(state_details['t_id'], state_details['b_id'], state)
    
    diff = result['biden_votes'] - result['trump_votes']
    last_diff = history[state_name]['margin']
    
    change = diff - last_diff
    if change != 0:
        history[state_name]['margin'] = diff
        history[state_name]['updated'] = datetime.now().strftime(format='%Y-%m-%dT%H:%M:%S')

    # convert date strings to datetime objects
    updated = datetime.strptime(history[state_name]['updated'],'%Y-%m-%dT%H:%M:%S')
    minutes_ago = floor((datetime.now()-updated).total_seconds()/60)

    if result['biden_win']:
        status = 'CALLED FOR BIDEN'
    elif result['trump_win']:
        status = 'CALLED FOR TRUMP'
    else:
        status = 'Still Counting'

    leader_name = "Biden" if result['biden_votes'] > result['trump_votes'] else "Trump"
    
    print(
        f'\n- {state_name} @ {result["progress"]}\n\
        -- {leader_name} by {"{:,d}".format(abs(diff))}\n\
        -- {status}\n\
        -- new votes {minutes_ago} minute(s) ago\n\
        -- change: {"{:,d}".format(change)}'
    )
    
# store relevant results
with open('history.json', 'w') as f:
    json.dump(history, f)