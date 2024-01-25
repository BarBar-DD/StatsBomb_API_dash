import pandas as pd
import requests

#################################################################################
#                                                                               #
#        ne pas RUN si non nécessaire (durée du run = 40 à 60 min)              #
#                                                                               #
#################################################################################

def check_data_availability(match_id, data_type):
    url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/{data_type}/{match_id}.json"
    response = requests.head(url)
    return response.status_code == 200

def competitions_table(competitions):
    data_filtered = []
    data_all = []
    for competition in competitions:
        competition_name = competition['competition_name']
        season_name = competition['season_name']
        competition_id = competition['competition_id']
        season_id = competition['season_id']
        matches_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/{competition_id}/{season_id}.json"
        matches_response = requests.get(matches_url)
        matches = matches_response.json()
        teams = set()
        has_events_data = False
        has_three_sixty_data = False
        for match in matches:
            teams.add(match['home_team']['home_team_name'])
            teams.add(match['away_team']['away_team_name'])
            match_id = match['match_id']
            if check_data_availability(match_id, 'events'):
                has_events_data = True
            if check_data_availability(match_id, 'three-sixty'):
                has_three_sixty_data = True
            data_all.append({
                "Compétition": competition_name,
                "Saison": season_name,
                "Match ID": match_id,
                "Events Data": "Available" if check_data_availability(match_id, 'events') else "No Data",
                "Three-Sixty Data": "Available" if check_data_availability(match_id, 'three-sixty') else "No Data",
                "Équipe": match['home_team']['home_team_name']
            })
        
        if has_events_data and has_three_sixty_data:
            data_filtered.append({
                "Compétition": competition_name,
                "Saison": season_name,
                "Équipes": ", ".join(teams)
            })

    df_filtered = pd.DataFrame(data_filtered)
    df_all = pd.DataFrame(data_all)
    return df_filtered, df_all

def fetch_competitions_data():
    url = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json"
    response = requests.get(url)
    return response.json()

competitions_data = fetch_competitions_data()
glossaire_filtered_df, glossaire_all_df = competitions_table(competitions_data)

with pd.ExcelWriter("glossaire.xlsx") as writer:
    glossaire_filtered_df.to_excel(writer, sheet_name='Filtered', index=False)
    glossaire_all_df.to_excel(writer, sheet_name='All', index=False)
print("Le glossaire à été enregistré dans 'glossaire.xlsx'.")

