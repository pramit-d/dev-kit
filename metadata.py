import sys
import os
import json
import urllib.request
import requests
from rich import print
import datetime
import subprocess
import shutil


def write_project_repos_data(project_data):
    """
        Create json report for repository related content
        like: main_github_url, main_bes_url etc...
    """
    project_repos = {
        "main_github_url": "",
        "main_bes_url": "",
        "all_projects": [
            {
                "id": 0,
                "name": "",
                "url": ""
            }
        ],
        "all_bes_repos": [
            {
                "id": 0,
                "name": "",
                "url": ""
            }

        ]
    }
    project_repos.update(
        {"main_github_url": project_data["html_url"]})
    project_repos.update({"main_bes_url": project_data["html_url"]})
    project_repos["all_projects"][0]["id"] = project_data["id"]
    project_repos["all_projects"][0]["name"] = project_data["full_name"]
    project_repos["all_projects"][0]["url"] = project_data["html_url"]
    project_repos["all_bes_repos"][0]["id"] = project_data["id"]
    project_repos["all_bes_repos"][0]["name"] = project_data["full_name"]
    project_repos["all_bes_repos"][0]["url"] = project_data["html_url"]
    return project_repos

def write_languages(name, org):
    """
        fetch the languages from github URL
    """
    url = f"https://api.github.com/repos/{org}/{name}/languages"
    with urllib.request.urlopen(url) as raw_data:
        data = json.loads(raw_data.read())
    return data

def write_to_ossp_master(file_pointer, ossp_master_json, data):
    """
        Add or override the project details in ossp_master
    """
   
    ossp_master_json["items"].append(data)
    file_pointer.seek(0)
    file_pointer.write(json.dumps(ossp_master_json, indent=4))
    file_pointer.truncate()
   
    print("Added project!!")

def generate_ossp_master(pid, name, org, bes_technology_stack, tags):
    """
        Generate ossp master json report
        name, id, bes_technology_stack, org
    """
    
    write_flag = True
    besecure_assets_store = "/home/ubuntu/besecure-assets-store/projects/project-metadata.json" ## update besecure-assets-store path
    with open(besecure_assets_store, "r+", encoding="utf-8") as file_pointer:
        ossp_master_json = json.load(file_pointer)
        if write_flag:
            url = f"https://api.github.com/repos/{org}/{name}"
            with urllib.request.urlopen(url) as url_data:
                project_data = json.loads(url_data.read())
            ossp_data = json.loads('{}')
            repo_keys = [
                "id", "bes_tracking_id", "issue_url", "name",
                "full_name", "description", "bes_technology_stack",
                "watchers_count", "forks_count", "stargazers_count",
                "size", "open_issues", "created_at", "updated_at",
                "pushed_at", "git_url", "clone_url", "html_url",
                "homepage", "owner", "project_repos", "license",
                "language", "tags"
            ]
            for i in repo_keys:
                if i in ('id', 'bes_tracking_id'):
                    ossp_data[i] = pid
                elif i == "issue_url":
                    ossp_data[i] = ""
                elif i == "bes_technology_stack":
                    ossp_data[i] = bes_technology_stack
                elif i == "project_repos":
                    ossp_data[i] = write_project_repos_data(project_data)
                elif i == "tags": 
                    ossp_data[i] = tags
                elif i == "language":
                    ossp_data[i] = write_languages(name, org)
                elif i == "owner":
                    ossp_data[i] = {
                        "login": "O31E",
                        "type": "Lab",
                        "site_admin": False
                    }
                else:
                    ossp_data[i] = project_data[i]

            write_to_ossp_master(file_pointer, ossp_master_json, ossp_data)
        file_pointer.close()

def get_release_date(version, name, org):
    """Get release date of project

    Args:
        version (str): project version
        name (str): project name

    Returns:
        str: date in dd-mmm-yyyy format
    """
    cleanup(name)
    os.system('git clone -q https://github.com/' + org + '/' + name + '.git' + ' /tmp/' + name)
    os.chdir('/tmp/' + name)
    proc = subprocess.Popen([
        'git log --tags --simplify-by-decoration --pretty="format:%ci %d" | grep -w "' +
        version + '"'
    ], stdout=subprocess.PIPE, shell=True)
    (out) = proc.communicate()
    try:
        date = str(out).split(" ", maxsplit=1)[0]
        raw_date = date.split("'")[1]
        split_date = raw_date.split("-")
        yyyy = int(split_date[0])
        mmm = int(split_date[1])
        dd = int(split_date[2])
        format_datetime = datetime.datetime(yyyy, mmm, dd)
        final_date = str(format_datetime.strftime("%d-%b-%Y"))
        return final_date
    except (ValueError, IndexError):
        print(f"Version {version} not found, ignoring release date")

def cleanup(name):
    """
        remove the file/directory from tmp
    """
    if os.path.exists(f'/tmp/{name}'):
        shutil.rmtree('/tmp/' + name)

def generate_version_data(pid, name, version_tag, org):
    """
        generate version details page in osspoi_datastore
    """
    version_data_new = {
        "version": "",
        "release_date": "",
        "criticality_score": "Not Available",
        "scorecard": "Not Available",
        "cve_details": "Not Available"
    }
    version_data_new["version"] = version_tag
    date = get_release_date(version_tag, name, org)
    if date is None:
        version_data_new["release_date"] = "Not Available"
    else:
        version_data_new["release_date"] = date
    
    base_directory = "/home/ubuntu/besecure-assets-store/projects/project-version" ## update besecure-assets-store path
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)
    
    path = os.path.join(base_directory, f"{pid}-{name}-Versiondetails.json")
    
    try:
        with open(path, "w", encoding="utf-8") as file:
            data = []
            data.append(version_data_new)
            file.write(json.dumps(data, indent=4))
            print("[bold red]Alert! [green]Created version details file for" +
                    f"[yellow] {pid}-{name} " +
                    f"[green]with version:[yellow]{version_tag}")
    except Exception as e:
        print(f"Error writing to {path}: {e}")
    
    if os.path.exists(path):
        print(f"File {path} created successfully.")
    else:
        print(f"Failed to create file {path}.")
    
    cleanup(name)

## --------------------- Modify input --------------------
pid = 48
name = "guardrails"
org = "guardrails-ai"
version_tag = "v0.5.9"
bes_technology_stack = "A"
tags = [
    "A",
    "SD-AS",
    "SD-DS",
    "TD-U-ApD",
    "ALL",
    "TD-C-S",
    "TD-C-WA",
    "TD-C-A",
    "COM-C"
]

## --------------------------------------------------------

generate_ossp_master(pid, name, org, bes_technology_stack, tags)
generate_version_data(pid, name, version_tag, org)


'''
    1. Update besecure-assets-store path in the code.
    2. Update input data.Check bes_technology_stack and tags from https://github.com/Be-Secure/BeSLighthouse/blob/main/references.md
    3. Run metadata.py using 'python3 metadata.py'
'''
