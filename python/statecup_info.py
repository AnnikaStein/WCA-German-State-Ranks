import info

# parameters for custom kinch scores used to determine German State Cup participants
EVENTS_IN_STATECUP = ['222', '333', '444', '333bf', '333oh', 'pyram', 'skewb', 'sq1', 'clock']
FOR_COMPETITION = 'RubiksGermanNationals2024'
with open('../assets/list_ids/statecup_enthusiasts.txt', 'r') as file:
    STATECUP_ENTHUSIASTS = [line for line in file]

# hard-coding extra people (newcomers w/o WCA ID) who could participate
# if their state is otherwise not filled
CUSTOM_NEWCOMERS = {st : [] for st in info.name_state.keys()}
CUSTOM_NEWCOMERS['br'] = ['Emil Krause']
