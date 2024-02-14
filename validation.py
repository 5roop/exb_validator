import datetime
from pathlib import Path
from lxml import etree as ET
import pandas as pd
import numpy as np
from tqdm import tqdm
import subprocess

file_passes = True
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s-%(levelname)s - %(message)s"
)
rule1 = "1. Added tiers: additional, disfluencyType1, disfluencyType2, disfluencyStructure, for each speaker!"
rule2 = "2. disfluencyType1 contains only timeline items that are used in tier1 as well"
rule3 = "3. disfluencyType2 contains only timeline items that are used in tier1 as well"
rule4 = (
    "4. disfluencyStructure contains only timeline items that are used in tier1 as well"
)
rule5 = "5. Additional has to be aligned 1:1 to disfluencyType1"
rule6 = "6. disfluencyStructure has to be aligned n:1 to disfluencyType1 - additional timeline items are allowed in disfluencyStructure, but not in disfluencyType1"
rule7 = "7. Tier1 is to have the text with spaces removed unchanged to the original text of that tier"
rule8 = "8. disfluencyType2 should timewise be fully contained inside disfluencyType1 "

logging.info(
    f"""
*** EXB format validation ***

The following rules will be checked:
{rule1}
{rule2}
{rule3}
{rule4}
{rule5}
{rule6}
{rule7}
{rule8}
"""
)


def find_candidates_for_original(doc: ET.Element) -> list[str]:
    longest_start = sorted(
        [i.get("start") for i in doc.findall(".//{*}event")], key=lambda s: -1 * len(s)
    )[0]
    candidates = Path("/home/peter/mezzanine/iriss_debug_and_salvage/iriss_with_w_and_pauses").glob("*.exb.xml")
    hits = []
    for c in candidates:
        r = subprocess.run(["grep", f'"{longest_start}"', str(c)], capture_output=True)
        if r.returncode == 0:
            hits.append(c)
    return hits


def find_all_speakers(doc: ET.Element) -> set[str]:
    all_speakers = {i.get("id") for i in doc.findall(".//{*}speaker")}
    speakers_with_at_least_one_turn = [i for i in all_speakers if doc.find(f".//{'{*}'}tier[@speaker='{i}']") is not None]
    return speakers_with_at_least_one_turn


def get_timeline(doc: ET.Element) -> ET.Element:
    return doc.find(".//{*}common-timeline")


def rule1_test_tiers_present(doc: ET.Element) -> bool:
    speakers = find_all_speakers(doc)
    tiers = list(doc.findall(".//{*}tier"))
    tier_display_names = [i.get("display-name") for i in tiers]
    for speaker in speakers:
        transcription_tiers = doc.findall(f".//{'{*}'}tier[@display-name='{speaker}']")
        if (l := len(list(transcription_tiers))) != 2:
            raise ValueError(
                f"For speaker {speaker} 2 transcription tiers were expected, but {l} were found"
            )

        if not len(list(doc.findall(f".//{'{*}'}tier[@speaker='{speaker}']"))) == 6:
            raise ValueError(f"For speaker {speaker} there aren't exactly 6 tiers! ")

    tier_naming_suffices = [
        "",
        "",
        " [additional]",
        " [nonverbalDisfluency]",
        " [verbalDisfluency]",
        " [disfluencyStructure]",
    ]
    expected_tier_display_names = [
        f"{speaker}{suffix}" for speaker in speakers for suffix in tier_naming_suffices
    ]
    for ex in expected_tier_display_names:
        try:
            tier_display_names.remove(ex)
        except ValueError:
            raise ValueError(f"Expected tier named {ex} was not found")
    if tier_display_names != []:
        raise ValueError(f"Found extra tiers: {tier_display_names}")
    return True


def rule2_check_nonverbal(doc: ET.Element) -> bool:
    speakers = find_all_speakers(doc)
    for speaker in speakers:
        tier1 = doc.find(f".//{'{*}'}tier[@speaker='{speaker}']")
        tier1timestamps = [
            event.get("start") for event in tier1.find(".//{*}event")
        ] + [event.get("end") for event in tier1.find(".//{*}event")]
        disfluency_type_tier = doc.find(
            f".//{'{*}'}tier[@speaker='{speaker}'][@category='nonverbalDisfluency'][@display-name='{speaker} [nonverbalDisfluency]']"
        )
        assert disfluency_type_tier is not None, "nonverbal tier not found"
        disfluencytimestamps = [
            event.get("start") for event in disfluency_type_tier.find(".//{*}event")
        ] + [event.get("end") for event in disfluency_type_tier.find(".//{*}event")]
        for tli in disfluencytimestamps:
            if not tli in tier1timestamps:
                raise ValueError(
                    f"For speaker {speaker} nonverbalDisfluency tier contains timestamps that are not in the first tier! (Rule 2 violation)"
                )
    return True


def rule3_check_verbal(doc: ET.Element) -> bool:
    speakers = find_all_speakers(doc)
    for speaker in speakers:
        tier1 = doc.find(f".//{'{*}'}tier[@speaker='{speaker}']")
        if tier1 is None:
            raise ValueError(f"No tiers found for speaker {speaker}, is that OK?")
        tier1timestamps = [
            event.get("start") for event in tier1.find(".//{*}event")
        ] + [event.get("end") for event in tier1.find(".//{*}event")]
        disfluency_type_tier = doc.find(
            f".//{'{*}'}tier[@speaker='{speaker}'][@category='verbalDisfluency'][@display-name='{speaker} [verbalDisfluency]']"
        )
        # if not disfluency_type_tier:
        #     raise ValueError(f"Could not find tier for disfluencyType{i}!")
        if list(disfluency_type_tier.getchildren()) == []:
            return True
        disfluencytimestamps = [
            event.get("start") for event in disfluency_type_tier.find(".//{*}event")
        ] + [event.get("end") for event in disfluency_type_tier.find(".//{*}event")]
        for tli in disfluencytimestamps:
            if not tli in tier1timestamps:
                raise ValueError(
                    f"For speaker {speaker} verbalDisfluency tier contains timestamps that are not in the first tier! (Rule 3 violation)"
                )
    return True


def rule4_check_disfluencyStructure(doc: ET.Element) -> bool:
    timeline = get_timeline(doc)
    speakers = find_all_speakers(doc)
    for speaker in speakers:
        tier1 = doc.find(f".//{'{*}'}tier[@speaker='{speaker}']")
        tier1timestamps = [
            event.get("start") for event in tier1.findall(".//{*}event")
        ] + [event.get("end") for event in tier1.findall(".//{*}event")]
        disfluency_structure_tier = doc.find(
            f".//{'{*}'}tier[@speaker='{speaker}'][@category='disfluencyStructure'][@display-name='{speaker} [disfluencyStructure]']"
        )
        if disfluency_structure_tier is None:
            raise ValueError(
                f"Speaker {speaker} does not have a disfluencyStructure tier!"
            )
        disfluency_structure_timestamps = [
            event.get("start")
            for event in disfluency_structure_tier.findall(".//{*}event")
        ] + [
            event.get("end")
            for event in disfluency_structure_tier.findall(".//{*}event")
        ]
        for tli in disfluency_structure_timestamps:
            if not tli in tier1timestamps:
                raise ValueError(
                    f"Disfluency Structure tier for speaker {speaker} contains timestamp {tli} that are not in the first tier! (Rule 4 violation)\n\n"
                )
    return True


def test_one_to_one_alignment(tier1: ET.Element, tier2: ET.Element) -> bool:
    events_in_tier1 = list(tier1.findall(".//{event}"))
    events_in_tier2 = list(tier2.findall(".//{event}"))

    timestamps_in_tier1 = [i.get("start") for i in events_in_tier1] + [
        i.get("end") for i in events_in_tier1
    ]
    timestamps_in_tier2 = [i.get("start") for i in events_in_tier2] + [
        i.get("end") for i in events_in_tier2
    ]

    if set(timestamps_in_tier1) - set(timestamps_in_tier2):
        raise ValueError(f"Found timestamps in tier1 that are not in tier2")
    return True


def rule5_disStruct_n_to_one_to_verbal(doc: ET.Element) -> bool:
    timeline = get_timeline(doc)
    speakers = find_all_speakers(doc)
    for speaker in speakers:
        disfluency_structure_tier = doc.find(
            f".//{'{*}'}tier[@speaker='{speaker}'][@category='disfluencyStructure'][@display-name='{speaker} [disfluencyStructure]']"
        )
        verbal_disfluency_tier = doc.find(
            f".//{'{*}'}tier[@speaker='{speaker}'][@category='verbalDisfluency'][@display-name='{speaker} [verbalDisfluency]']"
        )

        s_starts = [
            event.get("start")
            for event in disfluency_structure_tier.findall(".//{*}event")
        ]

        s_ends = [
            event.get("end")
            for event in disfluency_structure_tier.findall(".//{*}event")
        ]
        to_remove = []
        for s in s_starts:
            if s in s_ends:
                to_remove.append(s)
        for i in to_remove:
            s_starts.remove(i)
            s_ends.remove(i)
        structure_timestamps = s_starts + s_ends
        verbal_timestamps = [
            event.get("start")
            for event in verbal_disfluency_tier.findall(".//{*}event")
        ] + [
            event.get("end") for event in verbal_disfluency_tier.findall(".//{*}event")
        ]
        if set(structure_timestamps) - set(verbal_timestamps):
            raise ValueError(
                f"Found timestamps in structure that are not in verbal (rule 5 violation)"
            )
    return True


def rule5_disStruct_n_to_one_to_verbal_allow_gaps(doc: ET.Element) -> bool:
    timeline = get_timeline(doc)
    speakers = find_all_speakers(doc)
    for speaker in speakers:
        disfluency_structure_tier = doc.find(
            f".//{'{*}'}tier[@speaker='{speaker}'][@category='disfluencyStructure'][@display-name='{speaker} [disfluencyStructure]']"
        )
        verbal_disfluency_tier = doc.find(
            f".//{'{*}'}tier[@speaker='{speaker}'][@category='verbalDisfluency'][@display-name='{speaker} [verbalDisfluency]']"
        )
        verbal_events = verbal_disfluency_tier.findall(".//{*}event")

        for s in disfluency_structure_tier.findall(".//{*}event"):
            s_start = s.get("start")
            s_start_s = float(timeline.find(f"tli[@id='{s_start}']").get("time"))
            s_end = s.get("end")
            s_end_s = float(timeline.find(f"tli[@id='{s_end}']").get("time"))

            for v in verbal_events:
                # Let's find a v event that fully encompases
                # the s event.
                v_start_s = float(
                    timeline.find(f"tli[@id='{v.get('start')}']").get("time")
                )
                v_end_s = float(timeline.find(f"tli[@id='{v.get('end')}']").get("time"))
                if (v_start_s <= s_start_s) and (s_end_s <= v_end_s):
                    break
            else:
                raise ValueError(
                    "Found an event in structure that is not encompassed in verbal."
                )
    return True


def rule6_check_text(doc, original):
    speakers = find_all_speakers(doc)
    for speaker in speakers:
        tier1_doc = doc.find(f".//{'{*}'}tier[@speaker='{speaker}']")
        tier1_orig = original.find(f".//{'{*}'}tier[@speaker='{speaker}']")

        doctext = "".join([i.text for i in tier1_doc if i.text]).replace(" ", "")
        origtext = "".join([i.text for i in tier1_orig if i.text]).replace(" ", "")
        if doctext != origtext:
            raise ValueError(f"Text for speaker {speaker} does not match original.")


