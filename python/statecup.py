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
def get_average_kinch(kinch_dict, events = statecup_info.EVENTS_IN_STATECUP, weights = statecup_info.EVENT_WEIGHTS):
    nevents = len(events)
    sum = 0.0
    for i, event in enumerate(events):
        sum += kinch_dict[event] * weights[i]
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

# state level
def get_state_avg_kinch(state_df, all_registered = False):
    if all_registered:
        return state_df[state_df['registered_at_comp'] == True].loc[:,
                'average_kinch'].mean()
    else:
        return state_df[(state_df['registered_at_comp'] == True) & (state_df['willing_to_compete'] == True)].loc[:,
                'average_kinch'].mean()

# state level
def create_state_teams(all_states_df, state_order, all_registered = False, debug = False):
    # state_order shall be combined, pointing from back and from front
    pairing_for_missing = {}
    reverse_state_order = list(state_order.keys())[::-1]
    for i, item in enumerate(state_order.keys()):
        pairing_for_missing[item] = reverse_state_order[i]

    # take the up to three best people from each state to form preliminary team
    # this is the "first pass"
    state_ids = state_order.keys()
    assigned_names = {k : [] for k in state_ids}
    n_assigned_names = {k : 0 for k in state_ids}
    all_assigned_names = []
    available_names = {k : [] for k in state_ids}
    n_avail_names = {k : 0 for k in state_ids}
    for k in state_ids:
        state_df = all_states_df[k]
        extra_avail = []
        n_avail = 0
        if all_registered:
            n_in_state = len(state_df[state_df['registered_at_comp'] == True].index)
            take_up_to = min(n_in_state, statecup_info.TEAM_SIZE)
            preliminary_people = state_df[state_df['registered_at_comp'] == True]['name'].head(take_up_to).tolist()
            if n_in_state > statecup_info.TEAM_SIZE:
                extra_avail = state_df[state_df['registered_at_comp'] == True]['name'].tolist()[statecup_info.TEAM_SIZE:]
                n_avail = len(extra_avail)
        else:
            n_in_state = len(state_df[(state_df['registered_at_comp'] == True) & (state_df['willing_to_compete'] == True)].index)
            take_up_to = min(n_in_state, statecup_info.TEAM_SIZE)
            preliminary_people = state_df[(state_df['registered_at_comp'] == True) & (state_df['willing_to_compete'] == True)]['name'].head(take_up_to).tolist()
            if n_in_state > statecup_info.TEAM_SIZE:
                extra_avail = state_df[(state_df['registered_at_comp'] == True) & (state_df['willing_to_compete'] == True)]['name'].tolist()[statecup_info.TEAM_SIZE:]
                n_avail = len(extra_avail)
        if debug:
            print(preliminary_people)
        available_names[k] = extra_avail
        n_avail_names[k] = n_avail
        assigned_names[k] = preliminary_people
        n_assigned_names[k] = take_up_to
        all_assigned_names = all_assigned_names + preliminary_people

    if debug:
        print('>> Done with first pass.')
        print('>> available_names', available_names)
        print()
        print('>> n_avail_names', n_avail_names)
        print()
        print('>> assigned_names', assigned_names)
        print()
        print('>> n_assigned_names', n_assigned_names)
        print()
        print('>> all_assigned_names', all_assigned_names)
        print()

    # filling up missing spots
    # this is the "second pass"
    for m in pairing_for_missing.keys():
        needed_n = statecup_info.TEAM_SIZE - n_assigned_names[m]
        if needed_n > 0:
            # needs extra people
            # find the corresponding pair state
            pair_with = pairing_for_missing[m]
            if n_avail_names[pair_with] > needed_n:
                # grab the first needed_n names
                working_with = available_names[pair_with][:needed_n]
                available_names[pair_with] = available_names[pair_with][needed_n:]
                n_avail_names[pair_with] = len(available_names[pair_with])
            elif n_avail_names[pair_with] <= needed_n:
                # grab the available names
                working_with = available_names[pair_with]
                available_names[pair_with] = []
                n_avail_names[pair_with] = 0
            assigned_names[m] += working_with
            n_assigned_names[m] = len(assigned_names[m])
            all_assigned_names = all_assigned_names + working_with

    if debug:
        print('>> Done with second pass.')
        print('>> available_names', available_names)
        print()
        print('>> n_avail_names', n_avail_names)
        print()
        print('>> assigned_names', assigned_names)
        print()
        print('>> n_assigned_names', n_assigned_names)
        print()
        print('>> all_assigned_names', all_assigned_names)
        print()

    # filling up missing spots
    # this is the "third pass"
    all_still_avail = sum(available_names.values(), [])
    for m in pairing_for_missing.keys():
        needed_n = statecup_info.TEAM_SIZE - n_assigned_names[m]
        if needed_n > 0:
            # needs extra people
            # grab the first needed_n names
            working_with = all_still_avail[:needed_n]
            all_still_avail = all_still_avail[needed_n:]
            assigned_names[m] += working_with
            n_assigned_names[m] = len(assigned_names[m])
            all_assigned_names = all_assigned_names + working_with

    if debug:
        print('>> Done with third pass.')
        print('>> assigned_names', assigned_names)
        print()
        print('>> n_assigned_names', n_assigned_names)
        print()
        print('>> all_assigned_names', all_assigned_names)
        print()
    return assigned_names

# using all available info and the algorithm
def create_state_info(for_testing_only = False, deb = False):
    # to compare against, country level
    relevant_NRs = get_relevant_NRs()
    # people, competition level
    registered_returners = get_registered_returners()
    other_interested = statecup_info.CUSTOM_NEWCOMERS
    all_states = {}
    states_by_mean_avg_kinch = {st : 0.0 for st in info.name_state.keys()}
    for st in info.id_state.keys():
        state_kinch_df = sort_by_kinch(create_state_kinch_df(st,
                                        registered_returners,
                                        relevant_NRs))
        for o in other_interested[st]:
            new_row = pd.Series({'average_kinch' : 0.0,
                                    'wca_id' : 'Newcomer',
                                    'name' : o,
                                    'registered_at_comp' : True,
                                    'willing_to_compete' : True})
            state_kinch_df = pd.concat([state_kinch_df, new_row.to_frame().T],
                ignore_index=True)

        state_mean_avg_kinch = get_state_avg_kinch(state_kinch_df,
                                                   all_registered = for_testing_only)
        states_by_mean_avg_kinch[st] = state_mean_avg_kinch

        all_states[st] = state_kinch_df

    # we now know the overall state level (how good a state is on average)
    # that way we can sort the states by their allrounder quality
    # the first entry has the lowest mean kinch, last entry is best
    sorted_states = dict(sorted(states_by_mean_avg_kinch.items(),
                                key=lambda item: item[1]))
    if deb:
        print(sorted_states)

    # now build the proposed team composition,
    # from registered (+ willing) competitors
    state_teams = create_state_teams(all_states,
                                     sorted_states,
                                     all_registered = for_testing_only,
                                     debug = deb)

    return all_states, state_teams, states_by_mean_avg_kinch

if __name__ == "__main__":
    print("Testing statecup functionality independently.")
    main_func_output_scores, main_func_output_teams, main_func_output_mean_avg_kinch = create_state_info(for_testing_only = True,
                                                                        deb = True)
    print(main_func_output_scores, '\n\n', main_func_output_teams, '\n\n', main_func_output_mean_avg_kinch)
