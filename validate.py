import argparse
import fnmatch
import json
import os
import re
from pathlib import Path
from enum import Enum


class Dataset(Enum):
    DEFECTS4J = "Defects4J"
    QUIXBUGS = "QuixBugs"
    BEARS = "Bears"
    BUGSWARM = "BugSwarm"

DEFECTS4J_CATEGORY = ["Chart", "Cli", "Closure", "Codec", "Collections", "Compress", "Csv", "Gson", "JacksonCore",
                      "JacksonDatabind", "JacksonXml", "Jsoup", "JxPath", "Lang", "Math", "Mockito", "Time"]

QUIXBUGS_SET = set()
BUGSWARM_SET = set()


def read_dataset_files():
    global QUIXBUGS_SET, BUGSWARM_SET
    with open("QuixBugs.txt") as file:
        QUIXBUGS_SET = set(file.read().splitlines())

    with open("Export.json") as file:
        BugSwarm_json = json.load(file)
        BUGSWARM_SET = {bugswarm_bug["image_tag"] for bugswarm_bug in BugSwarm_json}


def list_bug_candidates(dataset_path, dataset):
    if dataset == Dataset.DEFECTS4J.value:
        pattern = re.compile(r'(' + '|'.join(DEFECTS4J_CATEGORY) + r')_\d+')
        return [folder for folder in dataset_path.iterdir() if folder.is_dir() and pattern.match(folder.name)]
    elif dataset == Dataset.QUIXBUGS.value:
        return [folder for folder in dataset_path.iterdir() if folder.is_dir() and folder.name in QUIXBUGS_SET]
    elif dataset == Dataset.BEARS.value:
        return [folder for folder in dataset_path.iterdir() if folder.is_dir() and folder.name.startswith("Bears-")]
    elif dataset == Dataset.BUGSWARM.value:
        return [folder for folder in dataset_path.iterdir() if folder.is_dir() and folder.name in BUGSWARM_SET]
    else:
        raise ValueError(f"Unknown dataset: {dataset}")


def find_randoop_test_files(path):
    matches = []
    for root, dirs, files in os.walk(path):
        for filename in fnmatch.filter(files, 'Randoop*.java'):
            matches.append(os.path.join(root, filename))
    return matches


def find_evosuite_test_files(path):
    matches = []
    for root, dirs, files in os.walk(path):
        for filename in fnmatch.filter(files, 'Evosuite*.java'):
            matches.append(os.path.join(root, filename))
    return matches


def validate(repo_path: Path):
    read_dataset_files()

    validate_pass = True
    dataset_requirements = {
        Dataset.DEFECTS4J: 68,
        Dataset.QUIXBUGS: 20,
        Dataset.BEARS: 20,
        Dataset.BUGSWARM: 20
    }

    for dataset in Dataset:
        dataset_path = repo_path / dataset.value

        if not dataset_path.exists():
            print(f"[FAIL] No {dataset.value} folder")
            return

        candidates = list_bug_candidates(dataset_path, dataset.value)
        min_bugs = dataset_requirements[dataset]

        if len(candidates) < min_bugs:
            print(f"[FAIL] Missing {min_bugs - len(candidates)} bugs in {dataset.value}")
            validate_pass = False

        for folder in candidates:
            if not all((folder / subfolder).exists() for subfolder in ["Buggy-Version", "Patched-Version"]):
                print(f"[FAIL] Incomplete versions in {dataset.value}-{folder.name}")
                validate_pass = False

            if not (folder / "test.txt").exists():
                print(f"[FAIL] No failed test file in {dataset.value}-{folder.name}")
                validate_pass = False

            if not validate_pass:
                return

            if len(find_randoop_test_files(folder / "Buggy-Version")) == 0:
                print(f"[FAIL] No Randoop test files in {dataset.value}-{folder.name}/Buggy-Version")
                validate_pass = False
            if len(find_randoop_test_files(folder / "Patched-Version")) == 0:
                print(f"[FAIL] No Randoop test files in {dataset.value}-{folder.name}/Patched-Version")
                validate_pass = False
            if len(find_evosuite_test_files(folder / "Buggy-Version")) == 0:
                print(f"[FAIL] No Evosuite test files in {dataset.value}-{folder.name}/Buggy-Version")
                validate_pass = False
            if len(find_evosuite_test_files(folder / "Patched-Version")) == 0:
                print(f"[FAIL] No Evosuite test files in {dataset.value}-{folder.name}/Patched-Version")
                validate_pass = False

            if not validate_pass:
                return

            if not (folder / "Coverage").exists():
                print(f"[FAIL] No coverage folder in {dataset.value}-{folder.name}")
                return

            if not (folder / "Coverage" / "Buggy-version-Randoop").exists():
                print(f"[FAIL] No coverage folder for Randoop in {dataset.value}-{folder.name}")
                return

            if not (folder / "Coverage" / "Buggy-version-Evosuite").exists():
                print(f"[FAIL] No coverage folder for Evosuite in {dataset.value}-{folder.name}")
                return

            if not (folder / "Coverage" / "Patched-version-Randoop").exists():
                print(f"[FAIL] No coverage folder for Randoop in {dataset.value}-{folder.name}")
                return

            if not (folder / "Coverage" / "Patched-version-Evosuite").exists():
                print(f"[FAIL] No coverage folder for Evosuite in {dataset.value}-{folder.name}")
                return

            if not (folder / "Coverage" / "Buggy-version-All").exists():
                print(f"[FAIL] No coverage folder for All in {dataset.value}-{folder.name}")
                return

            if not (folder / "Coverage" / "Patched-version-All").exists():
                print(f"[FAIL] No coverage folder for All in {dataset.value}-{folder.name}")
                return

    if validate_pass:
        print("[PASS] Validation pass")


def main():
    parser = argparse.ArgumentParser(description="Validate repository structure for bug datasets.")
    parser.add_argument("repo_path", type=str, help="Path to the repository")
    args = parser.parse_args()

    validate(Path(args.repo_path))


if __name__ == '__main__':
    main()
