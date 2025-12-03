#!/usr/bin/env python3

import requests
import csv
from collections import defaultdict
from os import environ

GITHUB_TOKEN = environ.get("GITHUB_TOKEN")
ORG = "NYU-CSE-Software-Engineering"
BRANCH = "main"
REPO_CONFIG_PATH = "config/repo-config.csv"
AUTHOR_CONFIG_PATH = "config/author-config.csv"

def get_contributors():
    """Fetch contributors from GitHub using GraphQL API."""
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    
    query = """
    query ($org: String!) {
      organization(login: $org) {
        repositories(first: 100) {
          nodes {
            name
            url
            collaborators(first: 100) {
              edges {
                permission
                node {
                  login
                  name
                  email
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {"org": ORG}
    
    result = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    data = result.json()
    students = defaultdict(list)
    repos = [repo for repo in data["data"]["organization"]["repositories"]["nodes"] 
             if repo["name"] != "demo-repository"]
    
    for repo in repos:
        edges = repo["collaborators"]["edges"]
        if not edges:
            continue
        for edge in edges:
            if edge['permission'] == "WRITE":
                student = edge["node"]
                students[repo["url"]].append(student)
    
    return students

def write_repo_config(repo_urls):
    """Write repo-config.csv with all repository URLs."""
    with open(REPO_CONFIG_PATH, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow([
            "Repository's Location",
            "Branch",
            "File formats",
            "Find Previous Authors",
            "Ignore Glob List",
            "Ignore standalone config",
            "Ignore Commits List",
            "Ignore Authors List",
            "Shallow Cloning",
            "File Size Limit",
            "Ignore File Size Limit",
            "Skip Ignored File Analysis"
        ])
        
        # Write each repository
        for repo_url in sorted(repo_urls):
            writer.writerow([repo_url, BRANCH, "", "", "", "", "", "", "", "", "", ""])
    
    print(f"✓ Written {len(repo_urls)} repositories to {REPO_CONFIG_PATH}")

def write_author_config(contributors_by_repo):
    """Write author-config.csv with all contributors."""
    with open(AUTHOR_CONFIG_PATH, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow([
            "Repository's Location",
            "Branch",
            "Author's Git Host ID",
            "Author's Emails",
            "Author's Display Name",
            "Author's Git Author Name",
            "Ignore Glob List"
        ])
        
        # Write each contributor for each repository
        total_entries = 0
        for repo_url in sorted(contributors_by_repo.keys()):
            contributors = contributors_by_repo[repo_url]
            for contributor in sorted(contributors, key=lambda x: x['login']):
                writer.writerow([
                    repo_url,
                    BRANCH,
                    contributor['login'],
                    contributor['email'],
                    "",  # Author's Display Name (empty as per current format)
                    "",  # Author's Git Author Name (empty as per current format)
                    ""   # Ignore Glob List (empty as per current format)
                ])
                total_entries += 1
        
        print(f"✓ Written {total_entries} author entries to {AUTHOR_CONFIG_PATH}")

def main():
    """Main function to populate both config files."""
    print("Fetching contributors from GitHub...")
    contributors_by_repo = get_contributors()
    
    if not contributors_by_repo:
        print("⚠ No contributors found. Check your GitHub token and organization name.")
        return
    
    print(f"Found {len(contributors_by_repo)} repositories with contributors")
    
    write_repo_config(contributors_by_repo.keys())
    
    write_author_config(contributors_by_repo)
    
    print("\n✓ Configuration files updated successfully!")

if __name__ == "__main__":
    main()
