import requests
import json
from datetime import datetime, timedelta
from math import ceil, floor

resp = requests.get('https://www.politico.com/2020-national-results/president-overall.json').json()

with open('history.json', 'r') as f:
    history = json.load(f)

with open('state_info.json', 'r') as f:
    state_info = json.load(f)

def print_update_time(resp):
    last_updated = datetime.strptime(resp.get('lastUpdated'),'%Y-%m-%dT%H:%M:%S+00:00')
    now = datetime.now() + timedelta(hours=5)

    print(f'last updated: {ceil((now-last_updated).total_seconds()/60)} minute(s) ago')

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

print_update_time(resp)

race_dict = resp['races']
for state in race_dict:
    state_id = state['stateFips']
    
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


    updated = datetime.strptime(history[state_name]['updated'],'%Y-%m-%dT%H:%M:%S')
    minutes_ago = floor((datetime.now()-updated).total_seconds()/60)

    if result['biden_win'] or result['trump_win']:
        winner = 'CALLED FOR BIDEN' if result['biden_win'] else 'CALLED FOR TRUMP'
    else:
        winner = 'Still Counting'

    if result['biden_votes'] > result['trump_votes']:
        print(f'\n- {state_name} @ {result["progress"]}\n-- Biden by {"{:,d}".format(diff)}\n-- {winner}\n-- new votes {minutes_ago} minute(s) ago\n-- change: {"{:,d}".format(change)}')
    else:
        print(f'\n- {state_name} @ {result["progress"]}\n-- Trump by {"{:,d}".format(0-diff)}\n-- {winner}\n-- new votes {minutes_ago} minute(s) ago\n-- change: {"{:,d}".format(change)}')

with open('history.json', 'w') as f:
    json.dump(history, f)