# tool to write html in a pythonic way
import dominate
from dominate.util import raw, text
from dominate.tags import *

# get remote files with urls
import urllib.request as libreq
# tool to read in the response as json
import json

# for multi-sorting by priorities in nested lists
from operator import itemgetter

# WCA German State Ranks custom modules
import info
import statecup
import statecup_info
import util

from argparse import ArgumentParser

parser = ArgumentParser(description='Generate new WCA German State Ranks.')
parser.add_argument('-d', '--debug', default = False,
                    help='Get detailed printouts')
parser.add_argument('-l', '--local', default = False,
                    help='Use locally available json data')
parser.add_argument('-a', '--automate', default = False,
                    help='Do not write json data to local dir')
parser.add_argument('-s', '--test_statecup', default = False,
                    help='Create teams for statecup assuming everyone wants to compete')
parser.add_argument('-e', '--via_expectation_values', default = True,
                    help='Create teams for statecup with expectation values for optimal teams')

args = parser.parse_args()

print()
print('>> Running with options:')
print('>>   debug =', args.debug)
print('>>   local =', args.local)
print('>>   automate =', args.automate)
print('>>   test_statecup =', args.test_statecup)
print('>>   via_expectation_values =', args.via_expectation_values)

# if you want a bunch of printouts to understand what's going on -> True,
# default -> False (just get very few printouts)
debug = args.debug

# Use local copies to limit traffic
local = args.local

# Don't save downloaded jsons when running on schedule (GitHub Action)
automate = args.automate

# Everyone who is registered is also willing to compete if this is True
test_statecup = args.test_statecup

# Optimize initial team composition via expectation values over all possible combinations
# ... of teams
# ... of chosen events
# ... of cubers doing different events in the team
via_expectation_values = args.via_expectation_values

# unofficial api, returns version of data
if local:
    with open('../local/version.json') as file:
        # the file is understood as json
        json_data_v = json.load(file)
else:
    with libreq.urlopen('https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/version.json') as file:
        # the file is understood as json
        json_data_v = json.load(file)
        if not automate:
            with open('../local/version.json', 'w') as f:
                json.dump(json_data_v, f)

version_y = json_data_v['export_date'][:4]
version_m = info.month_map[json_data_v['export_date'][5:7]]
version_d = json_data_v['export_date'][8:10]

# unofficial api, returns events
if local:
    with open('../local/events.json') as file:
        # the file is understood as json
        json_data_e = json.load(file)
else:
    with libreq.urlopen('https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/events.json') as file:
        # the file is understood as json
        json_data_e = json.load(file)
        if not automate:
            with open('../local/events.json', 'w') as f:
                json.dump(json_data_e, f)
e_list = [it['id'] for it in json_data_e['items']]

# model state dictionary with singles and averages, for each state, for each event
state_r = {k : {'single' : {e : [] for e in e_list}, 'average' : {e : [] for e in e_list if e not in info.no_avg}} for k in info.id_state.keys()}
state_r_DE = {k : {'single' : {e : [] for e in e_list}, 'average' : {e : [] for e in e_list if e not in info.no_avg}} for k in info.id_state.keys()}

print()
# where the magic happens -> reading the ranks once per WCA ID and writing what we need into the dictionary
for s in info.id_state.keys():
    wca_ids_s = info.id_state[s]
    print('>> Processing', wca_ids_s)
    for wca_id in wca_ids_s:
        if local:
            with open(f'../local/persons/{wca_id}.json') as file:
                json_data_p = json.load(file)
        else:
            with libreq.urlopen(f'https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/persons/{wca_id}.json') as file:
                json_data_p = json.load(file)
                if not automate:
                    with open(f'../local/persons/{wca_id}.json', 'w') as f:
                        json.dump(json_data_p, f)

        # collect single / average results per person for each event they have a result in
        # WCA ID, full name, best result (numerical value as in DB, not yet human-readable) and NR, CR, WR, country
        # inclusive version for DE and nonDE
        for e in json_data_p['rank']['singles']:
            state_r[s]['single'][e['eventId']].append([json_data_p['id'],
                                                       json_data_p['name'],
                                                       e['best'],
                                                       e['rank']['country'],
                                                       e['rank']['continent'],
                                                       e['rank']['world'],
                                                       json_data_p['country']])
        for e in json_data_p['rank']['averages']:
            state_r[s]['average'][e['eventId']].append([json_data_p['id'],
                                                        json_data_p['name'],
                                                        e['best'],
                                                        e['rank']['country'],
                                                        e['rank']['continent'],
                                                        e['rank']['world'],
                                                        json_data_p['country']])
        if json_data_p['country'] == 'DE':
            # The same but with strict cut on person country from DE
            for e in json_data_p['rank']['singles']:
                state_r_DE[s]['single'][e['eventId']].append([json_data_p['id'],
                                                           json_data_p['name'],
                                                           e['best'],
                                                           e['rank']['country'],
                                                           e['rank']['continent'],
                                                           e['rank']['world'],
                                                           json_data_p['country']])
            for e in json_data_p['rank']['averages']:
                state_r_DE[s]['average'][e['eventId']].append([json_data_p['id'],
                                                            json_data_p['name'],
                                                            e['best'],
                                                            e['rank']['country'],
                                                            e['rank']['continent'],
                                                            e['rank']['world'],
                                                            json_data_p['country']])

# the rankings need to be sorted,
# otherwise we just have them as they appear in the discord reaction roles
for st,dicts in zip(state_r.keys(),state_r.values()):
    if debug:
        print('Sorting', st, 'now.')
    for s,sd in zip(dicts['single'].keys(),dicts['single'].values()):
        if debug:
            print(s)
            print(sd)
        # if tied on best result (index 2 in inner list), sort by name instead (index 1 in inner list)
        sd.sort(key=itemgetter(2,1))
        if debug:
            print(sd)
        state_r[st]['single'][s] = sd
    for s,sd in zip(dicts['average'].keys(),dicts['average'].values()):
        if debug:
            print(s)
            print(sd)
        # same here, just for averages (more precise: mean or average)
        sd.sort(key=itemgetter(2,1))
        if debug:
            print(sd)
        state_r[st]['average'][s] = sd

if debug:
    print('Sorting strict DE represents only now')
for st,dicts in zip(state_r_DE.keys(),state_r_DE.values()):
    if debug:
        print('Sorting', st, 'now.')
    for s,sd in zip(dicts['single'].keys(),dicts['single'].values()):
        if debug:
            print(s)
            print(sd)
        # if tied on best result (index 2 in inner list), sort by name instead (index 1 in inner list)
        sd.sort(key=itemgetter(2,1))
        if debug:
            print(sd)
        state_r_DE[st]['single'][s] = sd
    for s,sd in zip(dicts['average'].keys(),dicts['average'].values()):
        if debug:
            print(s)
            print(sd)
        # same here, just for averages (more precise: mean or average)
        sd.sort(key=itemgetter(2,1))
        if debug:
            print(sd)
        state_r_DE[st]['average'][s] = sd
#print(state_r_DE)
# now, for the combination we start over again with an empty dict
overview = {'single' : {e : [] for e in e_list}, 'average' : {e : [] for e in e_list if e not in info.no_avg}}
overview_DE = {'single' : {e : [] for e in e_list}, 'average' : {e : [] for e in e_list if e not in info.no_avg}}

# collecting the best of all 16 states, for each event, for single / avg
for e in e_list:
    if debug:
        print(e)
    for it, st in enumerate(state_r.keys()):
        if debug:
            print('>>', it, st)
            print('>> Doing Singles')
        # checking if something exists for that state
        if len(state_r[st]['single'][e]) > 0:
            # modeling ties within a federal state
            this_states_best_value = state_r[st]['single'][e][0][2]
            this_states_best_list = [v for v in state_r[st]['single'][e] if v[2] == this_states_best_value]

            if debug:
                print(this_states_best_list)
            # checking if it's the first state with a result here
            if len(overview['single'][e]) == 0:
                # first result for this evt/single -> collect!
                overview['single'][e] = []
                for v in this_states_best_list:
                    overview['single'][e].append([st] + v)
            else:
                # could be interesting, check if better or equal than already existing ones
                if this_states_best_list[0][2] <= overview['single'][e][0][3]:
                    # better -> collect as the only state
                    if this_states_best_list[0][2] < overview['single'][e][0][3]:
                        # currently best -> write state + who achieved that
                        overview['single'][e] = []
                        for v in this_states_best_list:
                            overview['single'][e].append([st] + v)
                    # just equal -> append
                    else:
                        # currently tied
                        for v in this_states_best_list:
                            overview['single'][e].append([st] + v)

        # same stuff again, just for averages
        if e not in info.no_avg:
            if debug:
                print('>> Doing Averages')
            if len(state_r[st]['average'][e]) > 0:
                # modeling ties within a federal state
                this_states_best_value = state_r[st]['average'][e][0][2]
                this_states_best_list = [v for v in state_r[st]['average'][e] if v[2] == this_states_best_value]
                if debug:
                    print(this_states_best_list)
                if len(overview['average'][e]) == 0:
                    overview['average'][e] = []
                    for v in this_states_best_list:
                        overview['average'][e].append([st] + v)
                else:
                    if this_states_best_list[0][2] <= overview['average'][e][0][3]:
                        if this_states_best_list[0][2] < overview['average'][e][0][3]:
                            # currently best
                            overview['average'][e] = []
                            for v in this_states_best_list:
                                overview['average'][e].append([st] + v)
                        else:
                            # currently tied
                            for v in this_states_best_list:
                                overview['average'][e].append([st] + v)

if debug:
    print('Building overview for strict DE represents only now')
for e in e_list:
    if debug:
        print(e)
    for it, st in enumerate(state_r_DE.keys()):
        if debug:
            print('>>', it, st)
            print('>> Doing Singles')
        # checking if something exists for that state
        if len(state_r_DE[st]['single'][e]) > 0:
            # modeling ties within a federal state
            this_states_best_value = state_r_DE[st]['single'][e][0][2]
            this_states_best_list = [v for v in state_r_DE[st]['single'][e] if v[2] == this_states_best_value]

            if debug:
                print(this_states_best_list)
            # checking if it's the first state with a result here
            if len(overview_DE['single'][e]) == 0:
                # first result for this evt/single -> collect!
                overview_DE['single'][e] = []
                for v in this_states_best_list:
                    overview_DE['single'][e].append([st] + v)
            else:
                # could be interesting, check if better or equal than already existing ones
                if this_states_best_list[0][2] <= overview_DE['single'][e][0][3]:
                    # better -> collect as the only state
                    if this_states_best_list[0][2] < overview_DE['single'][e][0][3]:
                        # currently best -> write state + who achieved that
                        overview_DE['single'][e] = []
                        for v in this_states_best_list:
                            overview_DE['single'][e].append([st] + v)
                    # just equal -> append
                    else:
                        # currently tied
                        for v in this_states_best_list:
                            overview_DE['single'][e].append([st] + v)

        # same stuff again, just for averages
        if e not in info.no_avg:
            if debug:
                print('>> Doing Averages')
            if len(state_r_DE[st]['average'][e]) > 0:
                # modeling ties within a federal state
                this_states_best_value = state_r_DE[st]['average'][e][0][2]
                this_states_best_list = [v for v in state_r_DE[st]['average'][e] if v[2] == this_states_best_value]
                if debug:
                    print(this_states_best_list)
                if len(overview_DE['average'][e]) == 0:
                    overview_DE['average'][e] = []
                    for v in this_states_best_list:
                        overview_DE['average'][e].append([st] + v)
                else:
                    if this_states_best_list[0][2] <= overview_DE['average'][e][0][3]:
                        if this_states_best_list[0][2] < overview_DE['average'][e][0][3]:
                            # currently best
                            overview_DE['average'][e] = []
                            for v in this_states_best_list:
                                overview_DE['average'][e].append([st] + v)
                        else:
                            # currently tied
                            for v in this_states_best_list:
                                overview_DE['average'][e].append([st] + v)
print('>> Overview:')
print(overview_DE)

# German State Cup section - calculation externalized to statecup.py
print('>> Building State Cup Custom Kinch Ranks. This will take a while.')
statecup_scores, statecup_teams, statecup_mean_scores, statecup_team_scores = statecup.create_state_info(for_testing_only = test_statecup, expect = via_expectation_values)
if debug:
    print('>> State Cup Custom Kinch Ranks:')
    print(statecup_info)
    print(statecup_teams)
    print(statecup_mean_scores)
    print(statecup_team_scores)

# to show that we are only using a subset of all available results in German states,
# i.e. counting how many gave their consent
print()
id_count = 0
for k in info.id_state.keys():
    id_count += len(info.id_state[k])
print(f'>> Using {id_count} WCA IDs.')

# interesting info to fill on each page, as the results are time-dependent
updated = f'{version_m} {version_d}, {version_y}'

def generate_readme():
    md_str = f'''# WCA German State Ranks
[![WCA German State Ranks Automation](https://github.com/AnnikaStein/WCA-German-State-Ranks/actions/workflows/automate.yml/badge.svg)](https://github.com/AnnikaStein/WCA-German-State-Ranks/actions/workflows/automate.yml)
[![pages-build-deployment](https://github.com/AnnikaStein/WCA-German-State-Ranks/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/AnnikaStein/WCA-German-State-Ranks/actions/workflows/pages/pages-build-deployment)

Displaying the PRs of people who have given *explicit consent* (opt-in) to appear in German WCA state rankings. PRs taken from the WCA database via the [unofficial API](https://github.com/robiningelbrecht/wca-rest-api).

## How to appear in these rankings?
Fill out the form here: [link to enter the ranks](https://docs.google.com/forms/d/e/1FAIpQLSdoLLgBLfTxZIwKJx9QC5XywuMRBreKU4ElbLTvMEZqxRHFcw/viewform).

## You want to participate in the state cup?
Fill out the form here: [link](https://docs.google.com/forms/d/e/1FAIpQLSdqA8dWufte8_KMMjQVvB0JpeQgKIzr1FH1Dk2-MgjFVEZjdw/viewform).

## Data statement
> This information is based on competition results owned and maintained by the
> World Cube Assocation, published at https://worldcubeassociation.org/results
> as of {updated}.

## Support
Enjoy what you see? Feel free to support my projects here: [at my Cuboss-Affiliate page](https://cuboss.com/affiliate/?affiliate=hugacuba&r=hugacuba) and save 5% off your order! Direct donations can be made to: [your developer](https://www.paypal.com/paypalme/hugacuba).

'''

    with open('../README.md', 'w') as f:
        f.write(md_str)

# called multiple times, for different purposes, however with some equal parts across pages
def generate_html(variant = 'by-state', choice = 'bw'):
    # four types of pages to generate, each coming with different setups here
    if variant == 'by-state':
        title_app = f' - {info.name_state[choice]}'
        r = state_r[choice]
        s_dict = r['single']
        a_dict = r['average']
        prefix = '../pages/'
    if variant == 'overview':
        title_app = ' - Overview'
        prefix = '../pages/'
    if variant == 'state-cup':
        title_app = ' - State Cup Custom Kinch Ranks and Teams'
        prefix = '../pages/'
    if variant == 'index':
        title_app = ''
        prefix = '../'

    # start the DOM
    doc = dominate.document(title='WCA German State Ranks'+title_app)

    with doc.head:
        meta(charset='utf-8')
        meta(name='viewport', content='width=device-width, initial-scale=1')
        link(rel='stylesheet', href='https://www.w3schools.com/w3css/4/w3.css')
        link(rel='stylesheet', href='https://www.w3schools.com/lib/w3-theme-light-blue.css')
        link(rel='stylesheet', href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css')
        if variant == 'index':
            link(rel='stylesheet', href='./css/style.css')
        else:
            link(rel='stylesheet', href='../css/style.css')

    with doc:
        # body ('what the user sees')

        # how to write comments in the dominate library
        comment(' Content container ')

        # individual content per type, here from all states combined
        if variant == 'state-cup':
            event_str = ', '.join(statecup_info.EVENTS_IN_STATECUP)
            with div():
                # give class attribute, don't use python reserved keywords
                attr(cls = 'container')
                with div():
                    attr(style = 'overflow-x:auto;')
                    with div():
                        attr(cls='butn-con')
                        a('Overview',
                          href=f'./overview_all.html',
                          cls='w3-button w3-round w3-theme-d3link',
                          style='width: 5.5rem; padding: 0; text-align: center; font-size: 0.7rem')
                        for st in state_r.keys():
                            a(st,
                              href=f'./by-state_{st}.html',
                              cls='w3-button w3-round w3-theme-d3link',
                              style='width: 2.5rem; padding: 0; text-align: center; font-size: 0.7rem')
                        a('State Cup',
                          href=f'./state-cup.html',
                          cls='w3-button w3-round w3-theme-d3link btn-active',
                          style='width: 5.5rem; padding: 0; text-align: center; font-size: 0.7rem')
                h3('WCA German State Ranks'+title_app)
                with div():
                    attr(cls = 'w3-container')
                    with div():
                        attr(cls = 'card')
                        button("Details for Rubik's German Nationals 2024", type = 'button', cls = 'collapsible')
                        with div():
                            attr(cls = 'content')
                            p(f'The state cup is set to draw three out of those events randomly per match: {event_str}.' \
                            + ' These events are used to determine custom national average kinch scores per person, and a mean score per state. A person\'s kinch score is obtained from NR/PR * 100, with 0.0 if no result for the event, 100.0 if German NR-holder.')
                            p('Teams are obtained from: 1. state ranks info / scores, 2. registration data, 3. willingness to compete (with another google form to fill out) in a first pass. This first pass determines the team by optimizing the expected performance in the state cup, simulating all possible teams per state, all event combinations, and all permutations of team members. The three highest ranked (via average_kinch) are not necessarily also optimal via expectation value.' \
                            + ' States with too few eligible members are filled up with honorary cubers from other states.' \
                            + ' For that we use: mean score per state to sort states, combine best with worst and so on (second pass).' \
                            + ' In a third pass, if still not all states have enough members, we add available cubers (first from states with lowest mean custom kinch).')

                for st in state_r.keys():
                    scores = statecup_scores[st]
                    team = statecup_teams[st]
                    mean_avg_score = round(statecup_mean_scores[st], 2)
                    team_score = round(statecup_team_scores[st], 2)
                    long_name = info.name_state[st]
                    h4(long_name)
                    extra_text_team_score = f', (winning likelihood team score if multiple teams from this state were possible: {team_score})' if team_score > 0 else ''
                    p('Preliminary state cup team (must have stated willing_to_compete):' \
                    + f' 1. {team[0]}, 2. {team[1]}, 3. {team[2]}{extra_text_team_score}')
                    h6(f'Current state custom kinch scores, mean of this state (willing_to_compete only): {mean_avg_score}')
                    with div():
                        attr(style = 'overflow-x:auto')
                        with table():
                            with thead():
                                with tr():
                                    th('average_kinch', style = 'text-align: center;')
                                    th('WCA Id', style = 'text-align: center;')
                                    th('Name', style = 'text-align: left;')
                                    th('registered_at_comp', style = 'text-align: center;')
                                    th('willing_to_compete', style = 'text-align: center;')
                            with tbody():
                                for av, wc, na, re, wi in zip(scores['average_kinch'],
                                                            scores['wca_id'],
                                                            scores['name'],
                                                            scores['registered_at_comp'],
                                                            scores['willing_to_compete']):
                                    with tr():
                                        td(av, style = 'text-align: center;')
                                        if wc == 'Newcomer':
                                            td(wc, style = 'text-align: center;')
                                        else:
                                            td(a(wc, href=f'https://www.worldcubeassociation.org/persons/{wc}'), style = 'text-align: center;')
                                        td(na, style = 'text-align: left;')
                                        td('Yes' if re else 'No', style = 'text-align: center;')
                                        td('Yes' if wi else 'No', style = 'text-align: center;')

        # individual content from all states combined
        elif variant == 'overview':
            with div():
                # give class attribute, don't use python reserved keywords
                attr(cls = 'container')
                with div():
                    attr(style = 'overflow-x:auto;')
                    with div():
                        attr(cls='butn-con')
                        a('Overview',
                          href=f'./overview_all.html',
                          cls='w3-button w3-round w3-theme-d3link btn-active',
                          style='width: 5.5rem; padding: 0; text-align: center; font-size: 0.7rem')
                        for st in state_r.keys():
                            a(st,
                              href=f'./by-state_{st}.html',
                              cls='w3-button w3-round w3-theme-d3link',
                              style='width: 2.5rem; padding: 0; text-align: center; font-size: 0.7rem')
                        a('State Cup',
                          href=f'./state-cup.html',
                          cls='w3-button w3-round w3-theme-d3link',
                          style='width: 5.5rem; padding: 0; text-align: center; font-size: 0.7rem')

                h3('WCA German State Ranks'+title_app)
                with label():
                    attr(cls = 'switch')
                    span('Show Non-DE')
                    input_(type='checkbox', checked = True, value='allRepr', id='allReprSwitch')
                    span(cls = 'slider round')
                br()
                with label():
                    attr(cls = 'toggleSwitch nolabel', onclick='')
                    input_(type='checkbox', checked = False, value='single', id='sinAvgSwitch')
                    a()
                    with span():
                        span('Single', cls='left-span')
                        span('Average', cls='right-span')
                br()
                # DE-only
                # combined sin table
                with div():
                    attr(style = 'overflow-x:auto;display:none;', cls='deRepr single ov-hidden siav-active')
                    with table():
                        with thead():
                            with tr():
                                th('Event', style = 'text-align: center;')
                                th('Federal State', style = 'text-align: center;')
                                th('Name', style = 'text-align: left;')
                                th('WCA Id', style = 'text-align: center;')
                                th('Value', style = 'text-align: right;')
                                th('WR', style = 'text-align: right;')
                                th('CR', style = 'text-align: right;')
                                th('NR', style = 'text-align: right;')
                                th('Country', style = 'text-align: center;')
                        with tbody():
                            for es, s in zip(overview_DE['single'].keys(),overview_DE['single'].values()):
                                len_s = len(s)
                                if debug:
                                    print(es, s)
                                    print('len(s)', len_s)
                                if len_s > 1:
                                    for si, sid in enumerate(s):
                                        with tr():
                                            if si == 0:
                                                td(img(src=f'../assets/event-svg/{es}.svg',
                                                       style='text-align: center; height: 1.6rem; width: 1.6rem;'),
                                                   rowspan=f'{len_s}',
                                                   style = 'text-align: center; position: relative;')
                                            td(sid[0], style = 'text-align: center;')
                                            td(sid[2], style = 'text-align: left;')
                                            td(a(sid[1], href=f'https://www.worldcubeassociation.org/persons/{sid[1]}'), style = 'text-align: center;')
                                            if es not in ['333fm', '333mbf', '333mbo']:
                                                td(util.centiseconds_to_human(sid[3]), style = 'text-align: right;')
                                            elif es == '333mbf':
                                                td(util.mbf_to_human(sid[3]), style = 'text-align: right;')
                                            elif es == '333mbo':
                                                td(util.mbo_to_human(sid[3]), style = 'text-align: right;')
                                            else:
                                                td(sid[3], style = 'text-align: right;')
                                            td(sid[6], style = 'text-align: right;')
                                            td(sid[5], style = 'text-align: right;')
                                            td(sid[4], style = 'text-align: right;')
                                            td(sid[7], style = 'text-align: center;')
                                elif len_s == 1:
                                    sid = s[0]
                                    if debug:
                                        print(sid)
                                    with tr():
                                        td(img(src=f'../assets/event-svg/{es}.svg',
                                               style='text-align: center; height: 1.6rem; width: 1.6rem;'),
                                           rowspan=f'{len_s}',
                                           style = 'text-align: center; position: relative;')
                                        td(sid[0], style = 'text-align: center;')
                                        td(sid[2], style = 'text-align: left;')
                                        td(a(sid[1], href=f'https://www.worldcubeassociation.org/persons/{sid[1]}'), style = 'text-align: center;')
                                        if es not in ['333fm', '333mbf', '333mbo']:
                                            td(util.centiseconds_to_human(sid[3]), style = 'text-align: right;')
                                        elif es == '333mbf':
                                            td(util.mbf_to_human(sid[3]), style = 'text-align: right;')
                                        elif es == '333mbo':
                                            td(util.mbo_to_human(sid[3]), style = 'text-align: right;')
                                        else:
                                            td(sid[3], style = 'text-align: right;')
                                        td(sid[6], style = 'text-align: right;')
                                        td(sid[5], style = 'text-align: right;')
                                        td(sid[4], style = 'text-align: right;')
                                        td(sid[7], style = 'text-align: center;')
                # combined avg table
                with div():
                    attr(style = 'overflow-x:auto;display:none;', cls='deRepr average ov-hidden siav-hidden')
                    with table():
                        with thead():
                            with tr():
                                th('Event', style = 'text-align: center;')
                                th('Federal State', style = 'text-align: center;')
                                th('Name', style = 'text-align: left;')
                                th('WCA Id', style = 'text-align: center;')
                                th('Value', style = 'text-align: right;')
                                th('WR', style = 'text-align: right;')
                                th('CR', style = 'text-align: right;')
                                th('NR', style = 'text-align: right;')
                                th('Country', style = 'text-align: center;')
                        with tbody():
                            for ea, aa in zip(overview_DE['average'].keys(),overview_DE['average'].values()):
                                len_a = len(aa)
                                if debug:
                                    print(ea, aa)
                                    print('len(a)', len_a)
                                if len_a > 1:
                                    for ai, aid in enumerate(aa):
                                        with tr():
                                            if ai == 0:
                                                td(img(src=f'../assets/event-svg/{ea}.svg',
                                                       style='text-align: center; height: 1.6rem; width: 1.6rem;'),
                                                   rowspan=f'{len_a}',
                                                   style = 'text-align: center; position: relative;')
                                            td(aid[0], style = 'text-align: center;')
                                            td(aid[2], style = 'text-align: left;')
                                            td(a(aid[1], href=f'https://www.worldcubeassociation.org/persons/{aid[1]}'), style = 'text-align: center;')
                                            if es not in ['333fm']:
                                                td(util.centiseconds_to_human(aid[3]), style = 'text-align: right;')
                                            else:
                                                td(aid[3], style = 'text-align: right;')
                                            td(aid[6], style = 'text-align: right;')
                                            td(aid[5], style = 'text-align: right;')
                                            td(aid[4], style = 'text-align: right;')
                                            td(aid[7], style = 'text-align: center;')
                                elif len_a == 1:
                                    aid = aa[0]
                                    if debug:
                                        print(aid)
                                    with tr():
                                        td(img(src=f'../assets/event-svg/{ea}.svg',
                                               style='text-align: center; height: 1.6rem; width: 1.6rem;'),
                                           rowspan=f'{len_a}',
                                           style = 'text-align: center; position: relative;')
                                        td(aid[0], style = 'text-align: center;')
                                        td(aid[2], style = 'text-align: left;')
                                        td(a(aid[1], href=f'https://www.worldcubeassociation.org/persons/{aid[1]}'), style = 'text-align: center;')
                                        if es not in ['333fm']:
                                            td(util.centiseconds_to_human(aid[3]), style = 'text-align: right;')
                                        else:
                                            td(aid[3], style = 'text-align: right;')
                                        td(aid[6], style = 'text-align: right;')
                                        td(aid[5], style = 'text-align: right;')
                                        td(aid[4], style = 'text-align: right;')
                                        td(aid[7], style = 'text-align: center;')
                # DE and nonDE
                # combined sin table
                with div():
                    attr(style = 'overflow-x:auto;display:block;', cls='allRepr single ov-active siav-active')
                    with table():
                        with thead():
                            with tr():
                                th('Event', style = 'text-align: center;')
                                th('Federal State', style = 'text-align: center;')
                                th('Name', style = 'text-align: left;')
                                th('WCA Id', style = 'text-align: center;')
                                th('Value', style = 'text-align: right;')
                                th('WR', style = 'text-align: right;')
                                th('CR', style = 'text-align: right;')
                                th('NR', style = 'text-align: right;')
                                th('Country', style = 'text-align: center;')
                        with tbody():
                            for es, s in zip(overview['single'].keys(),overview['single'].values()):
                                len_s = len(s)
                                if debug:
                                    print(es, s)
                                    print('len(s)', len_s)
                                if len_s > 1:
                                    for si, sid in enumerate(s):
                                        with tr():
                                            if si == 0:
                                                td(img(src=f'../assets/event-svg/{es}.svg',
                                                       style='text-align: center; height: 1.6rem; width: 1.6rem;'),
                                                   rowspan=f'{len_s}',
                                                   style = 'text-align: center; position: relative;')
                                            td(sid[0], style = 'text-align: center;')
                                            td(sid[2], style = 'text-align: left;')
                                            td(a(sid[1], href=f'https://www.worldcubeassociation.org/persons/{sid[1]}'), style = 'text-align: center;')
                                            if es not in ['333fm', '333mbf', '333mbo']:
                                                td(util.centiseconds_to_human(sid[3]), style = 'text-align: right;')
                                            elif es == '333mbf':
                                                td(util.mbf_to_human(sid[3]), style = 'text-align: right;')
                                            elif es == '333mbo':
                                                td(util.mbo_to_human(sid[3]), style = 'text-align: right;')
                                            else:
                                                td(sid[3], style = 'text-align: right;')
                                            td(sid[6], style = 'text-align: right;')
                                            td(sid[5], style = 'text-align: right;')
                                            td(sid[4], style = 'text-align: right;')
                                            td(sid[7], style = 'text-align: center;')
                                elif len_s == 1:
                                    sid = s[0]
                                    if debug:
                                        print(sid)
                                    with tr():
                                        td(img(src=f'../assets/event-svg/{es}.svg',
                                               style='text-align: center; height: 1.6rem; width: 1.6rem;'),
                                           rowspan=f'{len_s}',
                                           style = 'text-align: center; position: relative;')
                                        td(sid[0], style = 'text-align: center;')
                                        td(sid[2], style = 'text-align: left;')
                                        td(a(sid[1], href=f'https://www.worldcubeassociation.org/persons/{sid[1]}'), style = 'text-align: center;')
                                        if es not in ['333fm', '333mbf', '333mbo']:
                                            td(util.centiseconds_to_human(sid[3]), style = 'text-align: right;')
                                        elif es == '333mbf':
                                            td(util.mbf_to_human(sid[3]), style = 'text-align: right;')
                                        elif es == '333mbo':
                                            td(util.mbo_to_human(sid[3]), style = 'text-align: right;')
                                        else:
                                            td(sid[3], style = 'text-align: right;')
                                        td(sid[6], style = 'text-align: right;')
                                        td(sid[5], style = 'text-align: right;')
                                        td(sid[4], style = 'text-align: right;')
                                        td(sid[7], style = 'text-align: center;')
                # combined avg table
                with div():
                    attr(style = 'overflow-x:auto;display:none;', cls='allRepr average ov-active siav-hidden')
                    with table():
                        with thead():
                            with tr():
                                th('Event', style = 'text-align: center;')
                                th('Federal State', style = 'text-align: center;')
                                th('Name', style = 'text-align: left;')
                                th('WCA Id', style = 'text-align: center;')
                                th('Value', style = 'text-align: right;')
                                th('WR', style = 'text-align: right;')
                                th('CR', style = 'text-align: right;')
                                th('NR', style = 'text-align: right;')
                                th('Country', style = 'text-align: center;')
                        with tbody():
                            for ea, aa in zip(overview['average'].keys(),overview['average'].values()):
                                len_a = len(aa)
                                if debug:
                                    print(ea, aa)
                                    print('len(a)', len_a)
                                if len_a > 1:
                                    for ai, aid in enumerate(aa):
                                        with tr():
                                            if ai == 0:
                                                td(img(src=f'../assets/event-svg/{ea}.svg',
                                                       style='text-align: center; height: 1.6rem; width: 1.6rem;'),
                                                   rowspan=f'{len_a}',
                                                   style = 'text-align: center; position: relative;')
                                            td(aid[0], style = 'text-align: center;')
                                            td(aid[2], style = 'text-align: left;')
                                            td(a(aid[1], href=f'https://www.worldcubeassociation.org/persons/{aid[1]}'), style = 'text-align: center;')
                                            if es not in ['333fm']:
                                                td(util.centiseconds_to_human(aid[3]), style = 'text-align: right;')
                                            else:
                                                td(aid[3], style = 'text-align: right;')
                                            td(aid[6], style = 'text-align: right;')
                                            td(aid[5], style = 'text-align: right;')
                                            td(aid[4], style = 'text-align: right;')
                                            td(aid[7], style = 'text-align: center;')
                                elif len_a == 1:
                                    aid = aa[0]
                                    if debug:
                                        print(aid)
                                    with tr():
                                        td(img(src=f'../assets/event-svg/{ea}.svg',
                                               style='text-align: center; height: 1.6rem; width: 1.6rem;'),
                                           rowspan=f'{len_a}',
                                           style = 'text-align: center; position: relative;')
                                        td(aid[0], style = 'text-align: center;')
                                        td(aid[2], style = 'text-align: left;')
                                        td(a(aid[1], href=f'https://www.worldcubeassociation.org/persons/{aid[1]}'), style = 'text-align: center;')
                                        if es not in ['333fm']:
                                            td(util.centiseconds_to_human(aid[3]), style = 'text-align: right;')
                                        else:
                                            td(aid[3], style = 'text-align: right;')
                                        td(aid[6], style = 'text-align: right;')
                                        td(aid[5], style = 'text-align: right;')
                                        td(aid[4], style = 'text-align: right;')
                                        td(aid[7], style = 'text-align: center;')

        # main page
        elif variant == 'index':
            with div():
                attr(cls = 'container')
                h3('WCA German State Ranks'+title_app)
                br()
                with div():
                    with div():
                        attr(cls='links-container')
                        a('Overview', href=f'pages/overview_all.html', cls='w3-button w3-round w3-theme-d3link')
                        for st in state_r.keys():
                            a(info.name_state[st], href=f'pages/by-state_{st}.html', cls='w3-button w3-round w3-theme-d3link')
                        a('State Cup', href='pages/state-cup.html', cls='w3-button w3-round w3-theme-d3link')

        # individual states
        else:
            with div():
                attr(cls = 'container')
                with div():
                    attr(style = 'overflow-x:auto;')
                    with div():
                        attr(cls='butn-con')
                        a('Overview',
                          href=f'./overview_all.html',
                          cls='w3-button w3-round w3-theme-d3link navi-btn',
                          style='width: 5.5rem;padding:0;text-align: center;font-size: 0.7rem')
                        for st in state_r.keys():
                            if st == choice:
                                a(st,
                                  href=f'./by-state_{st}.html',
                                  cls='w3-button w3-round w3-theme-d3link btn-active navi-btn',
                                  style='width: 2.5rem;padding:0;text-align: center;font-size: 0.7rem')
                            else:
                                a(st,
                                  href=f'./by-state_{st}.html',
                                  cls='w3-button w3-round w3-theme-d3link navi-btn',
                                  style='width: 2.5rem;padding:0;text-align: center;font-size: 0.7rem')
                        a('State Cup',
                          href=f'./state-cup.html',
                          cls='w3-button w3-round w3-theme-d3link',
                          style='width: 5.5rem; padding: 0; text-align: center; font-size: 0.7rem')
                h3('WCA German State Ranks'+title_app)
                with label():
                    attr(cls = 'switch')
                    span('Show Non-DE')
                    input_(type='checkbox', checked = True, value='nonDE', id='nonDEswitch')
                    span(cls = 'slider round')
                br()
                with div():
                    attr(style = 'overflow-x:auto;')
                    with div():
                        attr(cls='btn-con')
                        for ev in e_list:
                            if ev == '333':
                                with button(cls='btn btn-active', onclick=f'showEvt(evt=\'{ev}\')', id=f'btn-{ev}'):
                                    img(src=f'../assets/event-svg/{ev}.svg', cls='ebdSVG', style='height: 1.6rem; width: 1.6rem;')
                            else:
                                with button(cls='btn', onclick=f'showEvt(evt=\'{ev}\')', id=f'btn-{ev}'):
                                    img(src=f'../assets/event-svg/{ev}.svg', cls='ebdSVG', style='height: 1.6rem; width: 1.6rem;')
                with label():
                    attr(style='display:block;', cls = 'toggleSwitch nolabel', onclick='', id='sinAvgLabelPerS')
                    input_(type='checkbox', checked = False, value='single', id='sinAvgSwitchPerS')
                    a()
                    with span():
                        span('Single', cls='left-span')
                        span('Average', cls='right-span')
                for es, s in zip(s_dict.keys(),s_dict.values()):
                    with div():
                        if es == '333':
                            attr(cls=f'evt-active single siav-active sin-{es}', style='display:block;')
                        else:
                            attr(cls=f'evt-hidden single siav-active sin-{es}', style='display:none;')
                        #text(es + ' (Single)')
                        with div():
                            attr(style = 'overflow-x:auto;')
                            with table():
                                with thead():
                                    with tr():
                                        th('Name', style = 'text-align: left;')
                                        th('WCA Id', style = 'text-align: center;')
                                        th('Value', style = 'text-align: right;')
                                        th('WR', style = 'text-align: right;')
                                        th('CR', style = 'text-align: right;')
                                        th('NR', style = 'text-align: right;')
                                        th('Country', style = 'text-align: center;')
                                with tbody():
                                    for sid in s:
                                        if sid[6] == 'DE':
                                            with tr():
                                                attr(cls='bgColRow')
                                                td(sid[1], style = 'text-align: left;')
                                                td(a(sid[0],
                                                     href=f'https://www.worldcubeassociation.org/persons/{sid[0]}'),
                                                   style='text-align: center;')
                                                if es not in ['333fm', '333mbf', '333mbo']:
                                                    td(util.centiseconds_to_human(sid[2]),
                                                    style='text-align: right;')
                                                elif es == '333mbf':
                                                    td(util.mbf_to_human(sid[2]),
                                                       style='text-align: right;')
                                                elif es == '333mbo':
                                                    td(util.mbo_to_human(sid[2]),
                                                       style='text-align: right;')
                                                else:
                                                    td(sid[2], style='text-align: right;')
                                                td(sid[5], style='text-align: right;')
                                                td(sid[4], style='text-align: right;')
                                                td(sid[3], style='text-align: right;')
                                                td(sid[6], style='text-align: center;')
                                        else:
                                            with tr():
                                                attr(cls='bgColRow nonDE')
                                                td(sid[1],
                                                   style='font-style:italic;color:#A4A4A4;text-align: left;')
                                                td(a(sid[0],
                                                     href=f'https://www.worldcubeassociation.org/persons/{sid[0]}'),
                                                   style='font-style:italic;color:#A4A4A4;text-align: center;')
                                                if es not in ['333fm', '333mbf', '333mbo']:
                                                    td(util.centiseconds_to_human(sid[2]),
                                                       style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                elif es == '333mbf':
                                                    td(util.mbf_to_human(sid[2]),
                                                       style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                elif es == '333mbo':
                                                    td(util.mbo_to_human(sid[2]),
                                                       style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                else:
                                                    td(sid[2],
                                                       style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                td(sid[5],
                                                   style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                td(sid[4],
                                                   style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                td(sid[3],
                                                   style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                td(sid[6],
                                                   style='font-style:italic;color:#A4A4A4;text-align: center;')
                for ea, aa in zip(a_dict.keys(),a_dict.values()):
                    with div():
                        if ea == '333':
                            attr(cls=f'evt-active average siav-hidden avg-{ea}', style='display:none;')
                        else:
                            attr(cls=f'evt-hidden average siav-hidden avg-{ea}', style='display:none;')
                        #text(ea + ' (Average)')
                        with div():
                            attr(style = 'overflow-x:auto;')
                            with table():
                                with thead():
                                    with tr():
                                        th('Name', style = 'text-align: left;')
                                        th('WCA Id', style = 'text-align: center;')
                                        th('Value', style = 'text-align: right;')
                                        th('WR', style = 'text-align: right;')
                                        th('CR', style = 'text-align: right;')
                                        th('NR', style = 'text-align: right;')
                                        th('Country', style = 'text-align: center;')
                                with tbody():
                                    for aid in aa:
                                        if aid[6] == 'DE':
                                            with tr():
                                                attr(cls='bgColRow')
                                                td(aid[1], style = 'text-align: left;')
                                                td(a(aid[0], href=f'https://www.worldcubeassociation.org/persons/{aid[0]}'),
                                                   style='text-align: center;')
                                                if es not in ['333fm']:
                                                    td(util.centiseconds_to_human(aid[2]), style='text-align: right;')
                                                else:
                                                    td(aid[2], style='text-align: right;')
                                                td(aid[5], style='text-align: right;')
                                                td(aid[4], style='text-align: right;')
                                                td(aid[3], style='text-align: right;')
                                                td(aid[6], style='text-align: center;')
                                        else:
                                            with tr():
                                                attr(cls='bgColRow nonDE')
                                                td(aid[1], style='font-style:italic;color:#A4A4A4;text-align: left;')
                                                td(a(aid[0], href=f'https://www.worldcubeassociation.org/persons/{aid[0]}'),
                                                   style='font-style:italic;color:#A4A4A4;text-align: center;')
                                                if es not in ['333fm']:
                                                    td(util.centiseconds_to_human(aid[2]),
                                                       style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                else:
                                                    td(aid[2],
                                                       style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                td(aid[5], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                td(aid[4], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                td(aid[3], style='font-style:italic;color:#A4A4A4;text-align: right;')
                                                td(aid[6], style='font-style:italic;color:#A4A4A4;text-align: center;')

        with div():
            attr(cls = 'container')
            with footer():
                attr(style='text-align: center;height:10rem;clear:both;display:block;')
                br()
                h4('How to appear in these rankings?')
                text('Fill out the form here:')
                a('link to enter the ranks',
                  href='https://docs.google.com/forms/d/e/1FAIpQLSdoLLgBLfTxZIwKJx9QC5XywuMRBreKU4ElbLTvMEZqxRHFcw/viewform',
                  target='_blank')
                text('.')
                br()
                h4('You want to participate in the state cup?')
                text('Fill out the form here:')
                a('link',
                  href='https://docs.google.com/forms/d/e/1FAIpQLSdqA8dWufte8_KMMjQVvB0JpeQgKIzr1FH1Dk2-MgjFVEZjdw/viewform',
                  target='_blank')
                text('.')
                br()
                h4('Data statement')
                text(f'From {id_count} WCA IDs.')
                br()
                text(f'This information is based on competition results owned and maintained by the World Cube Assocation, published at https://worldcubeassociation.org/results as of {updated}.')
                br()
                a('© Annika Stein, 2024.',
                  href='https://annikastein.github.io/',
                  target='_blank')
                br()
                text('Source code for this project: ')
                a(i(cls='fab fa-github fa-fw w3-large w3-text-grey'),
                  href='https://github.com/AnnikaStein/WCA-German-State-Ranks',
                  target='_blank')
                br()
                br()
                text('Enjoy what you see? Feel free to support my projects here: ')
                a('at my Cuboss-Affiliate page',
                  href ='https://cuboss.com/affiliate/?affiliate=hugacuba&r=hugacuba',
                  target='_blank')
                text(' and save 5% off your order! Direct donations can be made to: ')
                a('your developer',
                  href ='https://www.paypal.com/paypalme/hugacuba',
                  target='_blank')
                text('.')
                br()
                br()

        if variant == 'index':
            script(src='./js/script.js')
        else:
            script(src='../js/script.js')
        script(data_id='101446349', _async=True, src='//static.getclicky.com/js')

    if debug:
        print()
        print('#'*8)
        print()
        print('>> Writing HTML file:')
        #print(doc.render())
        print()
        print('#'*8)
        print()
    if variant == 'index' or variant == 'state-cup':
        with open(f"{prefix}{variant}.html", "w") as text_file:
            print(doc, file=text_file)
    else:
        with open(f"{prefix}{variant}_{choice}.html", "w") as text_file:
            print(doc, file=text_file)


# now we know the relevant info to steer the UI
print()
print('#'*8)
print()
print('>> Finished reading competitor information and matched with state')
print()
print('#'*8)
print()

print('>> Writing index to UI.')
generate_html(variant = 'index', choice = 'all')

print('>> Writing updated state rank overview to UI.')
generate_html(variant = 'overview', choice = 'all')

# to be commented out on the afternoon of October 5th, 2024 to preserve
# the state in which this page was before the first German State Cup
print('>> Writing statecup info and teams to UI.')
generate_html(variant = 'state-cup', choice = 'all')

for st in state_r.keys():
    print(f'>> Writing {st} ranks to UI.')
    generate_html(variant = 'by-state', choice = st)

print()
print('>> Writing version to README.md')
generate_readme()
print()
print('#'*8)
print()
print('>> Finished UI update. Have fun!')
print()
print('#'*8)
print()
