#!/usr/bin/env python

import csv
import sys
import re
import json
import os



# get the file signature
def extract_file_signature(filename: str) -> str:
    print(f"[+] Extracting File Signature: {filename}")
    try:
        signature = re.search(r"[A-Z]{4}", filename)
        signature = signature[0]
    except:
        try:
            signature = re.search(r"[A-Z]{3}_[0-9]{1,3}", filename)
            signature = signature[0].replace("_", "-")
        except:
            signature = re.search(r"[A-Z]{3}", filename)
            signature = signature[0].replace("_", "-")
    return signature

def create_assets(filename: str) -> list:
    print("[+] Creating Assets list")
    assets = list()
    with open(filename, encoding="utf-8", errors="ignore") as f:
        rows = csv.reader(f)
        # find index of the asset column
        print("[+] Parsing csv file and finding index of 'Asset Name Description'")
        for row in rows:
            for column_index, column_name in enumerate(row):
                if column_name.lower() == "asset name description":
                    asset_column_index = column_index

                if "specification" in column_name.lower():
                    model_column_index = column_index
            break

        # create list of assets 
        print("[+] Parsing csv file and creating list of assets")
        for row in rows:
                match = re.search(r"^R\d+.*-.*", row[asset_column_index])
                if match:
                    assets.append([row[asset_column_index], row[model_column_index]])
    return assets

def create_records(assets: list) -> list:
    # create records of rack number, columns, rows and maps
    print("[+] Creating Records")
    records = list()
    for asset in assets:
        rack_num = re.search(r"^R\d+", asset[0])
        asset[0] = asset[0].replace(rack_num[0], "", 1)
        column = re.search(r"\d+", asset[0])
        rack_row = re.search(r"^[a-zA-Z]", asset[0])
        key = column[0] + "_" + rack_row[0]
        # fix for multiple hyphens
        asset[0] = asset[0].split("-", 1)
        rack_name = "rack_" + re.search(r"\d+", rack_num[0])[0]
        if "-" in asset[0][1]:
            asset[0][1] = asset[0][1].replace("-", "_")
        record = [rack_name, column[0], rack_row[0], key, asset[0][1], asset[1]]
        records.append(record)
    return records

def create_output_dictionary(records: list) -> dict:
    print("[+] Creating Output dictionary")
    output_dict = dict()
    # Create output dictionary 
    for rack, col, row_in_rack, k, v, spare in records:
        if rack not in output_dict:
            output_dict[rack] = dict()
        
        if "cols" not in output_dict[rack]:
            output_dict[rack]["cols"] = list()

        if int(col) not in output_dict[rack]["cols"]:
            output_dict[rack]["cols"].append(int(col))

        if "rows" not in output_dict[rack]:
            output_dict[rack]["rows"] = list()

        if row_in_rack not in output_dict[rack]["rows"]:
            output_dict[rack]["rows"].append(row_in_rack) 

        if "map" not in output_dict[rack]:
            output_dict[rack]["map"] = dict()

        # if muliple value of v, store it in a list
        if "," in v:
            v = v.replace(" ", "")
            v = v.split(",")
            output_dict[rack]["map"].update({k: v})
        elif "NN1" in spare or "NNA1" in spare:
            output_dict[rack]["map"].update({k: [v, "SPARE"]})
        else:
            output_dict[rack]["map"].update({k: v})

    output_dict[rack]["cols"].sort()
    signature = extract_file_signature(filename)
    output = {signature: output_dict}
    return output


if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print("Error: No folder path Specified\nUsage: rackjuice.py folder_path")
        answer = input("Parsing files in the Current folder?(y/n)")
        if answer == "y":
            file_list = os.listdir()
        else:
            raise SytemExit("No files are parsed")
    else:
        folder_path = sys.argv[1]
        if not os.path.exists(folder_path):
            raise SystemExit(f"Error: Invalid Folder path name: {folder_path}")
        else:
            file_list = os.listdir(folder_path)

    final_output = dict()
    for filename in file_list:
        if ".csv" in filename:
            print(f"[:.] Parsing file: {filename}")
            file_path = os.path.join(folder_path, filename)
            assets = create_assets(file_path)
            records = create_records(assets)
            output = create_output_dictionary(records)
            final_output.update(output)

    with open("RELAY_RACK_CONFIG.json", "x") as out:
        out.write(json.dumps(final_output, indent=4))
    print(f"[+] Successfully parsed files to output RELAY_RACK_CONFIG.json")
