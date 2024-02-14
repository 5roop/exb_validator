from pathlib import Path

file_to_check = Path(
    "/home/peter/mezzanine/iriss_debug_and_salvage/Iriss-disfl-anno-phase1/Iriss-J-Gvecg-P580002.exb.xml"
)
assert file_to_check.exists(), "File doesn't exist"
EXB_bytes = file_to_check.read_bytes()


from lxml import etree as ET
import pandas as pd
import numpy as np
from tqdm import tqdm
import subprocess

file_passes = True


doc = ET.fromstring(EXB_bytes)
from validation import find_candidates_for_original

hits = find_candidates_for_original(doc)
if len(hits) > 1:
    print("Found multiple candidates for original file")
    raise AttributeError("Can't continue with multiple candidates.")
elif len(hits) == 0:
    print("Found no candidates for original file")
    raise AttributeError("Can't continue with no candidates.")
else:
    print(f"Found the original file for this annotation: {hits[0].name}")
    original = ET.fromstring(hits[0].read_bytes())

from validation import find_all_speakers

speakers = find_all_speakers(doc)
print(f"Found speakers: {speakers}")
from validation import rule1_test_tiers_present

try:
    rule1_test_tiers_present(doc)
    print("Rule 1 validated.")
except Exception as e:
    print(f"Rule 1: {e.args[0]}")

from validation import get_timeline

timeline = get_timeline(doc)
if timeline is None:
    print("Timeline seems not to be present!")
    file_passes = False

from validation import rule2_check_nonverbal, rule3_check_verbal

# try:
rule2_check_nonverbal(doc)
print("Rule 2 validated")
# except Exception as e:
    # print(f"Rule 2: {e.args[0]}")
# try:
rule3_check_verbal(doc)
print("Rule 3 validated")
# except Exception as e:
    # print(f"Rule 3: {e.args[0]}")

from validation import rule4_check_disfluencyStructure

# try:
rule4_check_disfluencyStructure(doc)
print("Rule 4 validated")
# except Exception as e:
    # print(f"Rule 4: {e.args[0]}")

from validation import (
    rule5_disStruct_n_to_one_to_verbal,
    rule5_disStruct_n_to_one_to_verbal_allow_gaps,
)

# try:
rule5_disStruct_n_to_one_to_verbal_allow_gaps(doc)
print("Rule 5 validated")
# except Exception as e:
    # print(f"Rule 5: {e.args[0]}")

from validation import rule6_check_text

# try:
rule6_check_text(doc, original)
print("Rule 6 validated.")
# except Exception as e:
    # print(e.args[0])
