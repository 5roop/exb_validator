# exb_validator
A streamlit app for validating manual IRISS EXB files.

*** EXB format validation ***

The following rules will be checked:

    Added tiers: additional, nonverbalDisfluency, verbalDisfluency, disfluencyStructure, for each speaker!
    nonverbalDisfluency contains only timeline items that are used in tier1 as well
    verbalDisfluency contains only timeline items that are used in tier1 as well
    disfluencyStructure contains only timeline items that are used in tier1 as well
    disfluencyStructure has to be aligned 1
    to verbalDisfluency - additional timeline items are allowed in disfluencyStructure, but not in verbalDisfluency
    Tier1 is to have the text with spaces removed unchanged to the original text of that tier
