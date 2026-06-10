import json

with open("data/master_profile.json", "r") as file:
    profile = json.load(file)

print("Profile Loaded Successfully!")
print(profile)