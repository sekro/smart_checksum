#!/usr/bin/env python3
"""
wrapper for convenient checksum checking & tracking
Written for usage on HUNT cloud but should work on all linux systems
Sebastian Krossa
sebastian.krossa@ntnu.no
NTNU, Trondheim, Norway March 2021
"""

import subprocess as sp
import argparse
import json
import os
import sys
from datetime import datetime

# adjust to binaries on your system
checksum_tools = {
    'md5': 'md5sum',
    'sha256': 'sha256sum'
}

defaults = {
    'checksums': 'md5',
    'db': 'smart_sums_db.json'
}


def get_checksum(filename, tool):
    # wrap the filename into "" to cover all those spaces...
    filename = '\"' + filename + '\"'
    shell_cmd = ' '.join([tool, filename])
    checksum_return_val = None
    # capture errors
    try:
        # it's possible to explicitly tell check_call to use a shell and set env vars via env parameter
        checksum_return_val = sp.check_output(shell_cmd, shell=True)
    except sp.CalledProcessError as error:
        print(error.output)
        return None
    if checksum_return_val is not None:
        checksum_return_val = checksum_return_val.decode("utf-8").split(' ')[0]
    return checksum_return_val


def save_db(json_rp, checksum_dict):
    with open(json_rp, 'w') as json_file:
        json.dump(checksum_dict, json_file, sort_keys=True, indent=4)


def run_checksum_calculations(args, json_rp, checksum_dict):
    n_skipped = 0
    n_calc = 0
    for current_d, dirs, files in os.walk(args.target):
        for file in files:
            current_rel_path = os.path.join(current_d, file)
            # skip DB file
            if not current_rel_path == json_rp:
                if not current_rel_path in checksum_dict:
                    checksum_dict[current_rel_path] = {}
                if args.checksum in checksum_dict[current_rel_path] and not args.force:
                    if args.verbose:
                        print("skipping file {} - checksum already calculated".format(current_rel_path))
                    n_skipped += 1
                else:
                    checksum_dict[current_rel_path][args.checksum] = get_checksum(current_rel_path, checksum_tools[args.checksum])
                    if args.verbose:
                        print("{} - {}: {}".format(current_rel_path, args.checksum, checksum_dict[current_rel_path][args.checksum]))
                    n_calc += 1
                    if args.save_often:
                        save_db(json_rp, checksum_dict)
    if args.force:
        print('force mode - all existing checksum were overwritten')
    print('Done - calculated {} and skipped {} existing checksums'.format(n_calc, n_skipped))
    if n_skipped > 0:
        print('rerun with flag --force to recalculate and overwrite existing checksums')
    save_db(json_rp, checksum_dict)


def run_checksum_check(args, json_rp, checksum_dict):
    if len(checksum_dict) > 0:
        n_files_to_check = len(checksum_dict)
        n_files_ok = 0
        n_files_wrong = 0
        print("start checking {} files found in DB".format(n_files_to_check))
        for current_d, dirs, files in os.walk(args.target):
            for file in files:
                current_rel_path = os.path.join(current_d, file)
                # skip DB file
                if not current_rel_path == json_rp:
                    if current_rel_path in checksum_dict:
                        if args.checksum in checksum_dict[current_rel_path]:
                            check_dt_str = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                            current_chksum = get_checksum(current_rel_path, checksum_tools[args.checksum])
                            if checksum_dict[current_rel_path][args.checksum] == current_chksum:
                                if "OK" not in checksum_dict[current_rel_path]:
                                    checksum_dict[current_rel_path]["OK"] = {}
                                if args.verbose:
                                    print("checksum for {} - OK".format(current_rel_path))
                                checksum_dict[current_rel_path]["OK"][check_dt_str] = {
                                    args.checksum: current_chksum
                                }
                                n_files_ok += 1
                            else:
                                if "WRONG" not in checksum_dict[current_rel_path]:
                                    checksum_dict[current_rel_path]["WRONG"] = {}
                                print("checksum for {} - WRONG - expected {} but calculated {}".format(current_rel_path, checksum_dict[current_rel_path][args.checksum], current_chksum))
                                checksum_dict[current_rel_path]["WRONG"][check_dt_str] = {
                                    args.checksum: current_chksum
                                }
                                n_files_wrong += 1
        print("Done checking - found {} of {} files in DB - {} OK, {} WRONG".format(n_files_wrong + n_files_ok,
                                                                                              n_files_to_check,
                                                                                              n_files_ok, n_files_wrong))
        if n_files_wrong > 0:
            print("rerun with flag --lastok to see when WRONG files were last seen as OK")
        save_db(json_rp, checksum_dict)
    else:
        print("DB is empty - nothing to do")


def run_find_lastok(args, checksum_dict):
    for filename, file_dict in checksum_dict.items():
        if "WRONG" in file_dict:
            if "OK" in file_dict:
                last_ok = sorted(file_dict["OK"].keys())[-1]
                print("Last OK entry for {} was on {} entry: {}".format(filename, last_ok, file_dict["OK"][last_ok]))
            else:
                print("File {} was never OK".format(filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='smart_checksum - python warpped checksum calc&check')
    parser.add_argument("target", help="base folder with files to be checked")
    parser.add_argument("--checksum",
                        help="Checksum type to use - default {} - possible options: {}".format(defaults['checksums'], list(checksum_tools.keys())),
                        default=defaults['checksums'])
    parser.add_argument("--db", help="Filename for checksum database in json format - default {}".format(defaults['db']),
                        default=defaults['db'])
    parser.add_argument("--check", help="If given check sums in db",
                        action='store_true')
    parser.add_argument("--lastok", help="Run this in case you get WRONG checksum to check for last OK entries",
                        action='store_true')
    parser.add_argument("--force", help="If given all checksum will be recalculated",
                        action='store_true')
    parser.add_argument("--save_often", help="If given DB will be saved every time after a new checksum was calculated",
                        action='store_true')
    parser.add_argument("--verbose", help="spams your screen",
                        action='store_true')
    args = parser.parse_args()
    json_rp = os.path.join(args.target, args.db)
    if not os.path.exists(args.target):
        print("target path does not exist / not found - exiting")
        sys.exit(1)
    if args.checksum not in checksum_tools:
        print("undefined checksum type {} - use one of these {} - exiting".format(args.checksum, list(checksum_tools.keys())))
        sys.exit(1)
    if os.path.exists(json_rp):
        with open(json_rp, 'r') as json_file:
            checksum_dict = json.load(json_file)
    else:
        checksum_dict = {}
    if args.check:
        run_checksum_check(args, json_rp, checksum_dict)
    if args.lastok:
        run_find_lastok(args, checksum_dict)
    # ok this is a bit studpid but only run if flags --check and --lastok are not set
    if not args.check and not args.lastok:
        run_checksum_calculations(args, json_rp, checksum_dict)
    sys.exit(0)
