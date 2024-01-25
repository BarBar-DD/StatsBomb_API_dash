import requests
import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import  Circle
from mplsoccer import Pitch


################################################################################
# https://github.com/statsbomb/open-data                                       #
# Look the glossaire.xlsx sheet"Filtred" to find what you can take             #
# You must have 3 conditions (competition; team_name; year)                    #
# take time to :                                                               #
# pip install mplsoccer                                                        #
# brew install ffmpeg                                                          #
################################################################################

competition = "FIFA World Cup"
team_name = "France"
year = "2022"

#########################
# création des dossiers #
#########################
Lib_folder_path = 'Lib'
Lineups_folder_path = 'Lineups'
video_folder_path = 'Video'
graph_folder_path = 'Graph'
if not os.path.exists(Lib_folder_path):
    os.makedirs(Lib_folder_path)  
Lineups_folder_path = os.path.join(Lib_folder_path, Lineups_folder_path)
if not os.path.exists(Lineups_folder_path):
    os.makedirs(Lineups_folder_path)
video_folder_path = os.path.join(Lib_folder_path, video_folder_path)
if not os.path.exists(video_folder_path):
        os.makedirs(video_folder_path)     
graph_folder_path = os.path.join(Lib_folder_path, graph_folder_path)
if not os.path.exists(graph_folder_path):
        os.makedirs(graph_folder_path)

################################################################################
base_url = "https://raw.githubusercontent.com/statsbomb/open-data/master/data" #
################################################################################

def find_matches(competition_id, team_name, year, base_url):
    team_matches = []
    seasons = requests.get(f"{base_url}/competitions.json").json()
    season_id = None
    for season in seasons:
        if season['competition_id'] == competition_id and str(season['season_name']) == year:
            season_id = season['season_id']
            break

    if season_id is not None:
        matches_url = f"{base_url}/matches/{competition_id}/{season_id}.json"
        matches = requests.get(matches_url).json()
        for match in matches:
            if match['home_team']['home_team_name'] == team_name or match['away_team']['away_team_name'] == team_name:
                team_matches.append(match)

    return team_matches

def display_match_info_html(match_info, base_url, match_id):

    match_id = match_info['match_id']
    lineups_url = f"{base_url}/lineups/{match_id}.json"
    response = requests.get(lineups_url)
    lineups_data = response.json()
    data_for_df = []
    for team in lineups_data:
        team_name = team["team_name"]
        for player in team["lineup"]:
            positions = player.get("positions", [])
            for position in positions:
                player_info = {
                    "Équipe": team_name,
                    "Nom": player["player_name"],
                    "Numéro de Maillot": player["jersey_number"],
                    "Position sur le Terrain": position["position"],
                    "Début de Jeu": position.get("from", ""),  
                    "Fin de Jeu": position.get("to", "")  
                }
                data_for_df.append(player_info)

    #excel
    excel_filename_path = os.path.join('Lib', 'Lineups', f'lineups_{match_id}.xlsx')
    if not os.path.exists(excel_filename_path):
        df = pd.DataFrame(data_for_df)
        excel_filename = f"lineups_{match_id}.xlsx"
        df.to_excel(f'{excel_filename_path}', index=False)

    # config HTML
    home_team = match_info['home_team']['home_team_name']
    away_team = match_info['away_team']['away_team_name']
    home_score = match_info['home_score']
    away_score = match_info['away_score']
    competition = match_info['competition']['competition_name']
    match_date = match_info['match_date']
    stadium = match_info.get('stadium', {}).get('name', 'Unknown Stadium')
    lineups_download_link = f"<a href='{excel_filename_path}' download>Lineups.xlsx</a>"
    #si la ressources existe on l'affiche si on a pas de fichier events associé => pas de graphique 
    graph_image_filename = f'Lib/Graph/graph_{match_id}.png'
    if os.path.exists(graph_image_filename):
        graph = f"<img src='{graph_image_filename}' alt='Graphique du Match {match_id}' height='400' />"
    else:
        graph = ""
    
    video = f"<video height='400' controls><source src='Lib/Video/Video_{match_id}.mp4' type='video/mp4'>pas de ressources</video>"

    html_output = (
        "<style>"
        "body { font-family: Arial, sans-serif; margin: 0; padding: 0; text-align: center; background-color: #AAABBC; color: white; }"
        ".match-info { background-color: #9495B1; padding: 10px; }"
        ".media-container { margin: 20px 0; }"
        ".downloads { margin-bottom: 20px; }"
        ".downloads h3 { margin: 0; }"
        "img, video { max-width: 100%; height: 400px; box-shadow: rgba(0, 0, 0, 0.3) 0px 19px 38px, rgba(0, 0, 0, 0.22) 0px 15px 12px; }"
        "a { color: white; text-decoration: none; }"
        "a:hover { text-decoration: underline; }"
        "</style>"
        "<body>"
        "<div class='match-info'>"
        f"<h2>Match: {home_team} vs {away_team}</h2>"
        f"<p><strong>Date:</strong> {match_date} | <strong>Lieu:</strong> {stadium}</p>"
        f"<p><strong>Compétition:</strong> {competition} | <strong>Score:</strong> {home_score}-{away_score}</p>"
        f"</div>"
        f"<div class='media-container'>"
        f"{graph}"
        f"{video}"
        f"</div>"
        f"<div class='downloads'>"
        f"<h3>Téléchargements:</h3>"
        f"{lineups_download_link} | "
        f"<a href='https://github.com/statsbomb/open-data/blob/master/data/lineups/{match_id}.json' target='_blank'>Lineups.JSON</a> | "
        f"<a href='https://github.com/statsbomb/open-data/blob/master/data/events/{match_id}.json' target='_blank'>Events.JSON</a> | "
        f"<a href='https://github.com/statsbomb/open-data/blob/master/data/three-sixty/{match_id}.json' target='_blank'>360.JSON</a>"
        f"</div>"
        "</body>"
    )
    return html_output 

def get_competition_id(competition_name):
    url = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json"
    response = requests.get(url)
    competitions = response.json()
    for competition in competitions:
        if competition['competition_name'] == competition_name:
            return competition['competition_id']
    return None

competition_id = get_competition_id(competition)
if competition_id is not None:
    matches = find_matches(competition_id, team_name, year, base_url)
else:
    print("ID de compétition non trouvé ")
#############
#sotie html #
#############
html_output = "<html><body>"
for match in matches:
    match_id = match['match_id']
    video_file = f'Video_{match_id}.mp4'
    graph_file = f'graph_{match_id}.png'
    video_file_path = os.path.join('Lib', 'Video', f'Video_{match_id}.mp4')
    graph_file_path = os.path.join('Lib', 'Graph', f'graph_{match_id}.png')

    #############################
    #création du graph des passes
    if not os.path.exists(graph_file_path):
        events_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json"

        response = requests.get(events_url)
        events_data = json.loads(response.text)
        df_events = pd.DataFrame(events_data)


        passes = df_events[df_events['type'].apply(lambda x: x['name'] == 'Pass')]
        team_passes = passes['team'].apply(lambda x: x['name'])
        successful_passes = passes[passes['pass'].apply(lambda x: x.get('outcome') is None)]['team'].apply(lambda x: x['name'])
        total_passes_count = team_passes.value_counts()
        successful_passes_count = successful_passes.value_counts()

        colors = ['blue', 'red']
        fig, axs = plt.subplots(2, 3, figsize=(12, 8), facecolor='#2D3135')
        text_color = 'white'
        for ax in axs.flat:
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)
            ax.title.set_color(text_color)
            for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                        ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_color(text_color)
        
        axs[0, 0].axis('off')
        axs[0, 2].axis('off')
        axs[1, 1].axis('off')

        # diag circu
        axs[0, 1].pie(total_passes_count, labels=total_passes_count.index, colors=colors, autopct='%1.1f%%', startangle=90, radius=1.3, textprops={'color': 'white'})
        axs[0, 1].set_title('Passes Totales')
        axs[1, 0].pie([successful_passes_count[0], total_passes_count[0] - successful_passes_count[0]], labels=['Réussies', 'Échouées'], colors=['green', 'grey'], autopct='%1.1f%%', startangle=90, radius=0.9, textprops={'color': 'white'})
        axs[1, 0].set_xlabel('Passes Réussies - ' + total_passes_count.index[0])
        axs[1, 2].pie([successful_passes_count[1], total_passes_count[1] - successful_passes_count[1]], labels=['Réussies', 'Échouées'], colors=['green', 'grey'], autopct='%1.1f%%', startangle=90, radius=0.9, textprops={'color': 'white'})
        axs[1, 2].set_xlabel('Passes Réussies - ' + total_passes_count.index[1])

        # Histo
        axs[1, 1].bar(['1', '2'], [successful_passes_count[0], successful_passes_count[1]], color=colors, width=0.7)
        axs[1, 1].set_facecolor('#2D3135')
        for i, val in enumerate([successful_passes_count[0], successful_passes_count[1]]):
            axs[1, 1].text(i, val, str(val), ha='center', va='bottom', color='white')

        plt.savefig(f'Lib/Graph/{graph_file}')

    #####################
    #création de la video 
    if not os.path.exists(video_file_path):
        event_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json"
        three_sixty_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/three-sixty/{match_id}.json"

        event_data = requests.get(event_url).json()
        three_sixty_data = requests.get(three_sixty_url).json()
        freeze_frames = {}
        for data in three_sixty_data:
            event_uuid = data["event_uuid"]
            freeze_frames[event_uuid] = data["freeze_frame"]

        #timestamp en secondes (plus precis que dans l'api avec min et sec)
        def timestamp_to_seconds(timestamp):
            h, m, s = map(float, timestamp.split(':'))
            return h * 3600 + m * 60 + s

        events_with_positions = []

        for event in event_data:
            event_id = event["id"]
            if "location" in event:
                ball_position = event["location"]
                timestamp = event["timestamp"]
                seconds = timestamp_to_seconds(timestamp)

                # faire que 5 min pour simplifier le temps de calcul
                if seconds > 300:
                    break

                player_positions = []
                if event_id in freeze_frames:
                    for player in freeze_frames[event_id]:
                        player_id = player.get("player_id", "Inconnu")
                        player_position = player["location"]
                        is_teammate = player["teammate"]
                        player_positions.append((player_id, player_position, is_teammate))

                event_info = {
                    'event_id': event_id,
                    'time': seconds,
                    'ball_position': ball_position,
                    'player_positions': player_positions
                }
                events_with_positions.append(event_info)

        def createPitch(ax):
            # terrain de foot avec mplsoccer
            pitch = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='#c7d5cc')
            pitch.draw(ax=ax)

        fig, ax = plt.subplots(figsize=(10, 7))  # 1000x700 px
        createPitch(ax)

        def animate(i):
            ax.clear()
            createPitch(ax)

            event = events_with_positions[i]
            ball_pos = event['ball_position']
            player_positions = event['player_positions']

            ball = Circle((ball_pos[0], ball_pos[1]), 1.2, color='white') #balle plus grosse et blanche pour la voir
            ax.add_patch(ball)

            for player in player_positions:
                player_id, pos, is_teammate = player
                color = 'blue' if is_teammate else 'red'  
                player_circle = Circle((pos[0], pos[1]), 0.6, color=color)  
                ax.add_patch(player_circle)

            minutes = int(event['time'] // 60)
            seconds = int(event['time'] % 60)
            ax.set_title(f"Temps: {minutes:02d}:{seconds:02d}")

        # animation que 5min
        ani = animation.FuncAnimation(fig, animate, frames=min(len(events_with_positions), 300), interval=1000)

        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=5, metadata=dict(artist='Me'), bitrate=1800)
        ani.save(f'Lib/Video/{video_file}', writer=writer)


    html_output += display_match_info_html(match, base_url, match_id)
html_output += "</body></html>"

with open(f"{competition}_{team_name}_{year}.html", "w") as file:
    file.write(html_output)

print(f"Les informations des matches de {competition} {year} ont été enregistrées dans '{competition}_{team_name}_{year}.html'.")