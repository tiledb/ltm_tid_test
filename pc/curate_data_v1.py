#!/usr/bin/env python3

import argparse
import ast
import csv
import glob
import os


CHANNELS = [
    "v_e1",
    "pg_e",
    "c_e1",
    "pg_d",
    "v_e2",
    "pg_c",
    "c_e2",
    "c_d1",
    "c_d2",
    "v_d1",
    "v_d2",
    "c_c1",
    "v_c1",
    "c_c2",
    "v_c2",
    "v_12v",
    "v_b1",
    "c_b1",
    "v_b2",
    "pg_b",
    "pg_a",
    "v_a1",
    "c_b2",
    "c_a1",
    "v_a2",
    "c_a2",
    "pg_12v",
]

EXPECTED_VALUES = [
    3.3,
    5.0,
    2.0,
    5.0,
    3.3,
    5.0,
    2.0,
    2.0,
    2.0,
    3.3,
    3.3,
    2.0,
    3.3,
    2.0,
    3.3,
    12.0,
    3.3,
    2.0,
    3.3,
    5.0,
    5.0,
    3.3,
    2.0,
    2.0,
    3.3,
    2.0,
    3.3,
]


def average(values):
    return sum(values) / len(values)


def find_calibration(csv_file):

    with open(csv_file, newline="") as f:

        reader = csv.reader(f, delimiter="\t")

        for row in reader:

            if len(row) < 4:
                continue

            msg = row[3].strip()

            if not msg.startswith("MB calibration factors:"):
                continue

            factors = ast.literal_eval(
                msg.split(":", 1)[1].strip()
            )

            if len(factors) != len(CHANNELS):
                raise RuntimeError(
                    "Wrong number of calibration values."
                )

            return factors

    raise RuntimeError("Calibration factors not found.")


def find_measurements(csv_file):

    rows = []

    with open(csv_file, newline="") as f:

        reader = csv.reader(f, delimiter="\t")

        for line_num, row in enumerate(reader, start=1):

            if len(row) < 5 + len(CHANNELS):
                continue

            #
            # Only ON/ON rows are used to COMPUTE
            # the calibration.
            #

            if row[3] != "ON":
                continue

            if row[4] != "ON":
                continue

            try:
                values = [
                    float(x)
                    for x in row[5:5 + len(CHANNELS)]
                ]
            except Exception:
                continue

            if any(v == 0.0 for v in values):
                continue

            rows.append((line_num, values))

            if len(rows) == 3:
                break

    if len(rows) != 3:
        raise RuntimeError(
            "Could not find three valid measurement rows."
        )

    return rows


def show(current):

    print()
    print("Current calibration factors")
    print("-" * 40)

    for c, v in zip(CHANNELS, current):
        print(f"{c:7s}: {v:.2f}")


def compute(csv_file):

    old_cal = find_calibration(csv_file)

    rows = find_measurements(csv_file)

    print("Using rows:")

    for line, _ in rows:
        print(f"  line {line}")

    averages = []

    for i in range(len(CHANNELS)):
        averages.append(
            average(
                [row[1][i] for row in rows]
            )
        )

    new_cal = []

    print()

    print(
        f"{'Channel':7s}"
        f"{'Avg':>10s}"
        f"{'Expected':>10s}"
        f"{'Old':>10s}"
        f"{'New':>10s}"
    )

    print("-" * 60)

    for ch, avg, exp, old in zip(
        CHANNELS,
        averages,
        EXPECTED_VALUES,
        old_cal,
    ):

        new = round(old * (avg / exp), 2)

        new_cal.append(new)

        print(
            f"{ch:7s}"
            f"{avg:10.2f}"
            f"{exp:10.2f}"
            f"{old:10.2f}"
            f"{new:10.2f}"
        )

    with open(csv_file, "r", newline="") as f:
        lines = f.readlines()
    #
    # Update calibration line
    #

    replaced = False

    for i, line in enumerate(lines):

        if "MB calibration factors:" not in line:
            continue

        parts = line.rstrip("\n").split("\t", 3)

        new_string = (
            "MB calibration factors: ["
            + ", ".join(f"{v:.2f}" for v in new_cal)
            + "]"
        )

        lines[i] = (
            f"{parts[0]}\t"
            f"{parts[1]}\t"
            f"{parts[2]}\t"
            f"{new_string}\n"
        )

        replaced = True
        break

    if not replaced:
        raise RuntimeError(
            "Calibration line not found."
        )

    #
    # Recompute ALL measurement rows
    # (ON and OFF)
    #

    for i, line in enumerate(lines):

        row = line.rstrip("\n").split("\t")

        if len(row) < 5 + len(CHANNELS):
            continue

        try:
            values = [
                float(v)
                for v in row[5:5 + len(CHANNELS)]
            ]
        except Exception:
            continue

        for ch in range(len(CHANNELS)):

            #
            # Remove previous calibration
            #

            raw = values[ch] * old_cal[ch]

            #
            # Apply new calibration
            #

            values[ch] = round(
                raw / new_cal[ch],
                2
            )

        for ch in range(len(CHANNELS)):
            row[5 + ch] = f"{values[ch]:.2f}"

        lines[i] = "\t".join(row) + "\n"

    with open(csv_file, "w", newline="") as f:
        f.writelines(lines)

    print()
    print(f"Updated '{csv_file}'.")

    print()
    print("New calibration factors:\n")
    print("MB calibration factors: [")

    for i, value in enumerate(new_cal):

        if i != len(new_cal) - 1:
            print(f"    {value:.2f},")
        else:
            print(f"    {value:.2f}")

    print("]")


def decalibrate(csv_file):

    old_cal = find_calibration(csv_file)

    with open(csv_file, "r", newline="") as f:
        lines = f.readlines()

    #
    # Replace calibration factors with 1.00
    #

    replaced = False

    for i, line in enumerate(lines):

        if "MB calibration factors:" not in line:
            continue

        parts = line.rstrip("\n").split("\t", 3)

        new_string = (
            "MB calibration factors: ["
            + ", ".join("1.00" for _ in CHANNELS)
            + "]"
        )

        lines[i] = (
            f"{parts[0]}\t"
            f"{parts[1]}\t"
            f"{parts[2]}\t"
            f"{new_string}\n"
        )

        replaced = True
        break

    if not replaced:
        raise RuntimeError(
            "Calibration line not found."
        )

    #
    # Restore raw values on ALL rows
    #

    for i, line in enumerate(lines):

        row = line.rstrip("\n").split("\t")

        if len(row) < 5 + len(CHANNELS):
            continue

        try:
            values = [
                float(v)
                for v in row[5:5 + len(CHANNELS)]
            ]
        except Exception:
            continue

        for ch in range(len(CHANNELS)):

            #
            # Undo calibration
            #

            values[ch] = round(
                values[ch] * old_cal[ch],
                2
            )

        for ch in range(len(CHANNELS)):
            row[5 + ch] = f"{values[ch]:.2f}"

        lines[i] = "\t".join(row) + "\n"
    with open(csv_file, "w", newline="") as f:
        f.writelines(lines)

    print(f"Decalibrated '{csv_file}'.")


def process(path, mode):

    if os.path.isfile(path):

        files = [path]

    elif os.path.isdir(path):

        files = sorted(
            glob.glob(
                os.path.join(path, "*.csv")
            )
        )

        if not files:
            raise RuntimeError(
                f"No CSV files found in '{path}'."
            )

    else:
        raise RuntimeError(
            f"'{path}' does not exist."
        )

    for file in files:

        print("=" * 80)
        print(file)
        print("=" * 80)

        try:

            if mode == "show":

                show(
                    find_calibration(file)
                )

            elif mode == "compute":

                compute(file)

            elif mode == "decalibrate":

                decalibrate(file)

        except Exception as e:

            print(f"ERROR: {e}")

        print()


def main():

    parser = argparse.ArgumentParser(
        description="MB calibration tool"
    )

    parser.add_argument(
        "path",
        help=(
            "CSV file or directory "
            "containing CSV files"
        ),
    )

    group = parser.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="Show calibration factors",
    )

    group.add_argument(
        "-c",
        "--compute",
        action="store_true",
        help=(
            "Compute and update "
            "calibration factors"
        ),
    )

    group.add_argument(
        "-d",
        "--decalibrate",
        action="store_true",
        help=(
            "Set calibration factors "
            "to 1.00 and restore raw values"
        ),
    )

    args = parser.parse_args()

    if args.show:
        mode = "show"

    elif args.compute:
        mode = "compute"

    else:
        mode = "decalibrate"

    process(
        args.path,
        mode,
    )


if __name__ == "__main__":
    main()