import streamlit as st

with st.sidebar:
    rule1 = "1. Added tiers: additional, nonverbalDisfluency, verbalDisfluency, disfluencyStructure, for each speaker!"
    rule2 = "2. nonverbalDisfluency contains only timeline items that are used in tier1 as well"
    rule3 = "3. verbalDisfluency contains only timeline items that are used in tier1 as well"
    rule4 = "4. disfluencyStructure contains only timeline items that are used in tier1 as well"
    rule5 = "5. disfluencyStructure has to be aligned 1:n to verbalDisfluency - additional timeline items are allowed in disfluencyStructure, but not in verbalDisfluency"
    rule6 = "6. Tier1 is to have the text with spaces removed unchanged to the original text of that tier"

    st.markdown(
        f"""
 *** EXB format validation ***

The following rules will be checked:
{rule1}
{rule2}
{rule3}
{rule4}
{rule5}
{rule6}
"""
    )


st.markdown("# EXB Validator")
uploaded_file = st.file_uploader("EXB file upload:")
if uploaded_file is not None:
    EXB_bytes = uploaded_file.getvalue()

    from pathlib import Path
    from lxml import etree as ET
    import pandas as pd
    import numpy as np
    from tqdm import tqdm
    import subprocess

    file_passes = True

    st.divider()
    doc = ET.fromstring(EXB_bytes)
    from validation import find_candidates_for_original

    hits = find_candidates_for_original(doc)
    if len(hits) > 1:
        st.error("Found multiple candidates for original file")
        raise AttributeError("Can't continue with multiple candidates.")
    elif len(hits) == 0:
        st.error("Found no candidates for original file")
        raise AttributeError("Can't continue with no candidates.")
    else:
        st.write(f"Found the original file for this annotation: {hits[0].name}")
        original = ET.fromstring(hits[0].read_bytes())

    from validation import find_all_speakers

    speakers = find_all_speakers(doc)
    st.write(f"Found speakers: {speakers}")
    from validation import rule1_test_tiers_present

    try:
        rule1_test_tiers_present(doc)
        st.write("Rule 1 validated.")
    except Exception as e:
        st.error(f"Rule 1: {e.args[0]}")

    from validation import get_timeline

    timeline = get_timeline(doc)
    if timeline is None:
        st.error("Timeline seems not to be present!")
        file_passes = False

    from validation import rule2_check_nonverbal, rule3_check_verbal

    try:
        rule2_check_nonverbal(doc)
        st.write("Rule 2 validated")
    except Exception as e:
        st.error(f"Rule 2: {e.args[0]}")
    try:
        rule3_check_verbal(doc)
        st.write("Rule 3 validated")
    except Exception as e:
        st.error(f"Rule 3: {e.args[0]}")

    from validation import rule4_check_disfluencyStructure

    try:
        rule4_check_disfluencyStructure(doc)
        st.write("Rule 4 validated")
    except Exception as e:
        st.error(f"Rule 4: {e.args[0]}")

    from validation import (
        rule5_disStruct_n_to_one_to_verbal,
        rule5_disStruct_n_to_one_to_verbal_allow_gaps,
    )

    try:
        rule5_disStruct_n_to_one_to_verbal_allow_gaps(doc)
        st.write("Rule 5 validated")
    except Exception as e:
        st.error(f"Rule 5: {e.args[0]}")

    from validation import rule6_check_text

    try:
        rule6_check_text(doc, original)
        st.write("Rule 6 validated.")
    except Exception as e:
        st.error(e.args[0])
