# standard libraries
import json
import pandas as pd
import urllib.request as libreq

# WCA German State Ranks custom modules
import info
import statecup_info

# country level
def get_registered_returners(comp_id = statecup_info.FOR_COMPETITION):
    with libreq.urlopen(f'https://worldcubeassociation.org/api/v0/competitions/{comp_id}/wcif/public') as wcif:
        comp_data = json.load(wcif)
    persons = comp_data['persons']
    id_list = []
    for p in persons:
        wcaid = p['wcaId']
        if wcaid != None:
            id_list.append(wcaid)
    return id_list

# country level
def get_relevant_NRs(events = statecup_info.EVENTS_IN_STATECUP):
    nrdict = {ev : -999 for ev in events}
    for event in events:
        with libreq.urlopen(f'https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/rank/DE/average/{event}.json') as file:
            gerranks = json.load(file)
        nrdict[event] = gerranks['items'][0]['best']
    return nrdict

# person level
def get_relevant_PRs(wca_id, events = statecup_info.EVENTS_IN_STATECUP):
    eligible = False
    prdict = {ev : -999 for ev in events}
    with libreq.urlopen(f'https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api/persons/{wca_id}.json') as file:
        person = json.load(file)
    if person['country'] == 'DE':
        eligible = True
        for e in person['rank']['averages']:
            prdict[e['eventId']] = e['best']
    return prdict, person['name'], eligible

# person level
def get_partial_kinch_ranks(nrdict, prdict, events = statecup_info.EVENTS_IN_STATECUP):
    partial_kinch_dict = {ev : 0.0 for ev in events}
    for event in events:
        if prdict[event] != -999:
            # person has results for this event
            partial_kinch_dict[event] = (nrdict[event])/(prdict[event]) * 100.0
    return partial_kinch_dict

# person level
def get_average_kinch(kinch_dict, events = statecup_info.EVENTS_IN_STATECUP):
    nevents = len(events)
    sum = 0.0
    for event in events:
        sum += kinch_dict[event]
    average_kinch = round(sum / nevents, 2)
    return average_kinch

# person level
def check_if_registered_at_comp(wca_id, registration_ids):
    return True if wca_id in registration_ids else False

# person level
def check_if_willing_to_compete(wca_id):
    return True if wca_id in statecup_info.STATECUP_ENTHUSIASTS else False

# state level
def create_state_kinch_df(state_id, registered, NRs):
    # needed:
    # kinch, wca id (if it exists), name, registered_at_comp, willing_to_compete
    wca_id_s = info.id_state[state_id]
    datalist = []
    for entry in wca_id_s:
        relevant_PRs, name, eligibility = get_relevant_PRs(entry)
        if eligibility:
            partial_kinch_ranks = get_partial_kinch_ranks(NRs, relevant_PRs)
            average_kinch = get_average_kinch(partial_kinch_ranks)
            registered_at_comp = check_if_registered_at_comp(entry, registered)
            willing_to_compete = check_if_willing_to_compete(entry)
            datalist.append((average_kinch,
                                entry,
                                name,
                                registered_at_comp,
                                willing_to_compete))
    df = pd.DataFrame(datalist, columns=['average_kinch',
                                            'wca_id',
                                            'name',
                                            'registered_at_comp',
                                            'willing_to_compete'])
    return df

# state level
def sort_by_kinch(state_kinch_dataframe):
    sorted_df = state_kinch_dataframe.sort_values(by=['average_kinch'], ascending=[False])
    return sorted_df

def create_state_info():
    # to compare against, country level
    relevant_NRs = get_relevant_NRs()
    # people, competition level
    registered_returners = get_registered_returners()
    other_interested = statecup_info.CUSTOM_NEWCOMERS
    all_info_for_html = {}
    for st in info.id_state.keys():
        state_kinch_df = sort_by_kinch(create_state_kinch_df(st,
                                        registered_returners,
                                        relevant_NRs))
        all_info_for_html[st] = [state_kinch_df, other_interested[st]]
    return all_info_for_html
