import info

# parameters for custom kinch scores used to determine German State Cup participants
TEAM_SIZE = 3
EVENTS_IN_STATECUP = ['222', '333', '444', '333bf', '333oh', 'pyram', 'skewb', 'sq1', 'clock']
#EVENT_WEIGHTS = [0.5, 2.0, 1.0, 2.0, 1.0, 0.5, 0.5, 1.0, 1.0]
EVENT_WEIGHTS = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
RES_TYPE = ['a','a','a','s','a','a','a','a','a']
FOR_COMPETITION = 'RubiksGermanNationals2024'
# this will come from a google form that anyone willing to participate
# needs to fill out and submit with their consent
with open('../assets/list_ids/statecup_enthusiasts.txt', 'r') as file:
    STATECUP_ENTHUSIASTS = [line.rstrip('\n') for line in file]

# hard-coding extra people (newcomers w/o WCA ID) who could participate
# if their state is otherwise not filled
# this comes from private or public messages directed to the responsible (AS)
CUSTOM_NEWCOMERS = {st : [] for st in info.name_state.keys()}
CUSTOM_NEWCOMERS['bay'] = ['Mika Spielvogel']
CUSTOM_NEWCOMERS['ber'] = ['Claudio Favino']
CUSTOM_NEWCOMERS['br'] = ['Emil Krause','Johanna Gerhardt','Leonard Maas']
CUSTOM_NEWCOMERS['sh'] = ['Gesa Seifert']
