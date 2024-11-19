from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx

STATS_TO_NORMALIZE = ['MIN', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
STATS_TO_NOT_NORMALIZE = ['FG_PCT', 'FG3_PCT', 'FT_PCT']
USEFUL_STAT_CATEGORIES = ['GP', 'GS', 'MIN', 'FGM', 'FGA', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3M', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
FANTASY_STAT_CATEGORIES = ['FG_PCT', 'FT_PCT', 'FG3M', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']

class Player:
    def __init__(self, name):
        self.name_user_inputted = name
        self.get_player_stats()
    
    def get_player_stats(self):
        player = players.find_players_by_full_name(self.name_user_inputted)
        if len(player) == 0:
            raise ValueError(f"No player found with name '{self.name}'")
        if len(player) > 1:
            raise ValueError(f"Multiple players found with name '{self.name}'")
        self.player_info = player[0]
        player_stats = playercareerstats.PlayerCareerStats(player_id=self.player_info['id'])
        player_df = player_stats.get_data_frames()[0]
        if player_df.empty:
            raise ValueError(f"Player '{self.name}' has not played in any seasons")
        self.player_current_season_stats = player_df.loc[player_df.index[[-1]]]
        if self.player_current_season_stats['GP'].values[0] == 0:
            raise ValueError("Player has not played this season")
        for stat in STATS_TO_NORMALIZE:
            self.player_current_season_stats[stat] = self.player_current_season_stats[stat] / self.player_current_season_stats['GP']

class Trade_Analyzer:
    def __init__(self, my_players, away_players):
        self.my_player_names = my_players
        self.away_player_names = away_players
        self.create_players()
        self.create_combined_stats()
        self.evaluate_trade()
    
    def create_players(self):
        self.my_players = []
        for player_name in self.my_player_names:
            self.my_players.append(Player(player_name))
        self.away_players = []
        for player_name in self.away_player_names:
            self.away_players.append(Player(player_name))
        
        # for player in self.my_players:
        #     print(player.player_info['full_name'])
        #     print(player.player_current_season_stats)
        #     print()
        # for player in self.away_players:
        #     print(player.player_info['full_name'])
        #     print(player.player_current_season_stats)
        #     print()

    def create_combined_stats(self):
        self.combined_stats_my_players = {stat: 0 for stat in USEFUL_STAT_CATEGORIES}
        self.combined_stats_away_players = {stat: 0 for stat in USEFUL_STAT_CATEGORIES}

        for player in self.my_players:
            for stat in USEFUL_STAT_CATEGORIES:
                if stat in STATS_TO_NORMALIZE + ['GP', 'GS']:
                    self.combined_stats_my_players[stat] += player.player_current_season_stats[stat].values[0]
        num_my_players = len(self.my_players)
        for stat in USEFUL_STAT_CATEGORIES:
            if stat in STATS_TO_NORMALIZE + ['GP', 'GS']:
                self.combined_stats_my_players[stat] /= num_my_players
        if self.combined_stats_my_players['FGA'] == 0:
            self.combined_stats_my_players['FG_PCT'] = 0
        else:
            self.combined_stats_my_players['FG_PCT'] = self.combined_stats_my_players['FGM'] / self.combined_stats_my_players['FGA']
        if self.combined_stats_my_players['FG3A'] == 0:
            self.combined_stats_my_players['FG3_PCT'] = 0
        else:
            self.combined_stats_my_players['FG3_PCT'] = self.combined_stats_my_players['FG3M'] / self.combined_stats_my_players['FG3A']
        if self.combined_stats_my_players['FTA'] == 0:
            self.combined_stats_my_players['FT_PCT'] = 0
        else:
            self.combined_stats_my_players['FT_PCT'] = self.combined_stats_my_players['FTM'] / self.combined_stats_my_players['FTA']

        for player in self.away_players:
            for stat in USEFUL_STAT_CATEGORIES:
                if stat in STATS_TO_NORMALIZE + ['GP', 'GS']:
                    self.combined_stats_away_players[stat] += player.player_current_season_stats[stat].values[0]
        num_away_players = len(self.away_players)
        for stat in USEFUL_STAT_CATEGORIES:
            if stat in STATS_TO_NORMALIZE + ['GP', 'GS']:
                self.combined_stats_away_players[stat] /= num_away_players
        if self.combined_stats_away_players['FGA'] == 0:
            self.combined_stats_away_players['FG_PCT'] = 0
        else:
            self.combined_stats_away_players['FG_PCT'] = self.combined_stats_away_players['FGM'] / self.combined_stats_away_players['FGA']
        if self.combined_stats_away_players['FG3A'] == 0:
            self.combined_stats_away_players['FG3_PCT'] = 0
        else:
            self.combined_stats_away_players['FG3_PCT'] = self.combined_stats_away_players['FG3M'] / self.combined_stats_away_players['FG3A']
        if self.combined_stats_away_players['FTA'] == 0:
            self.combined_stats_away_players['FT_PCT'] = 0
        else:
            self.combined_stats_away_players['FT_PCT'] = self.combined_stats_away_players['FTM'] / self.combined_stats_away_players['FTA']

        # for stat in self.combined_stats_my_players:
        #     print(f"{stat}\n  My Players: {self.combined_stats_my_players[stat]:.5f}\n  Away Players: {self.combined_stats_away_players[stat]:.5f}\n")


    def evaluate_trade(self):
        self.evaluation = {
            'diff': {stat: 0 for stat in self.combined_stats_my_players},
            'percent_diff': {stat: 0 for stat in self.combined_stats_my_players}
        }

        stats = list(self.combined_stats_my_players.keys())
        my_values = [self.combined_stats_my_players[stat] for stat in stats]
        away_values = [self.combined_stats_away_players[stat] for stat in stats]

        # Calculate differences and percent differences
        for stat in stats:
            home_stat = self.combined_stats_my_players[stat]
            away_stat = self.combined_stats_away_players[stat]
            stat_diff = home_stat - away_stat
            self.evaluation['diff'][stat] = stat_diff
            if home_stat == 0:
                self.evaluation['percent_diff'][stat] = 0
            else:
                self.evaluation['percent_diff'][stat] = (stat_diff / home_stat) * 100  # Percent difference

        diff_values = [self.evaluation['diff'][stat] for stat in stats]
        percent_diff_values = [self.evaluation['percent_diff'][stat] for stat in stats]

        # Modify autolabel function to rotate text labels
        def autolabel(rects, ax, rotation=22):
            """Attach a text label above each bar in *rects*, displaying its height."""
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.2f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # Offset
                            textcoords="offset points",
                            ha='center', va='bottom', rotation=rotation)

        # First Bar Graph: Side-by-side comparison (All Stats)
        x = np.arange(len(stats))  # the label locations
        width = 0.35  # the width of the bars

        fig1, ax1 = plt.subplots(figsize=(14, 7))
        rects1 = ax1.bar(x - width/2, my_values, width, label='My Players', color='blue')
        rects2 = ax1.bar(x + width/2, away_values, width, label='Away Players', color='orange')

        # Add labels and title
        ax1.set_ylabel('Stat Values')
        ax1.set_title('Comparison of Player Stats (All Categories)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(stats, rotation=90)
        ax1.legend()

        # Annotate bars with rotated labels
        autolabel(rects1, ax1)
        autolabel(rects2, ax1)

        # Adjust y-axis limit to accommodate text labels
        # Find the maximum height among all bars
        all_heights = [rect.get_height() for rect in rects1 + rects2]
        max_height = max(all_heights)
        ax1.set_ylim(top=max_height * 1.15)  # Increase upper limit by 15%

        fig1.tight_layout()
        plt.show()

        # Second Bar Graph: Percent Differences with color coding (All Stats)
        fig2, ax2 = plt.subplots(figsize=(14, 7))
        bar_positions = np.arange(len(stats))

        # Normalize the percent differences for color mapping
        max_percent_diff = max(abs(min(percent_diff_values)), abs(max(percent_diff_values)))
        norm = colors.Normalize(vmin=-max_percent_diff, vmax=max_percent_diff)

        # Create a colormap that goes from red (negative) to green (positive)
        cmap = plt.get_cmap('RdYlGn')
        scalarMap = cmx.ScalarMappable(norm=norm, cmap=cmap)

        # Map the percent difference values to colors
        bar_colors = [scalarMap.to_rgba(value) for value in percent_diff_values]

        bars = ax2.bar(bar_positions, percent_diff_values, color=bar_colors, edgecolor='black')

        # Add labels and title
        ax2.set_ylabel('Percent Difference (%)')
        ax2.set_title('Percent Difference in Stats (All Categories)')
        ax2.set_xticks(bar_positions)
        ax2.set_xticklabels(stats, rotation=90)

        # Draw a horizontal line at y=0
        ax2.axhline(0, color='black', linewidth=0.8)

        # Annotate bars with rotated labels (rotation reduced to 22 degrees)
        for rect in bars:
            height = rect.get_height()
            ax2.annotate(f'{height:.2f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 5 if height >= 0 else -15),
                        textcoords="offset points",
                        ha='center', va='bottom' if height >= 0 else 'top', rotation=22)

        # Adjust y-axis limits to accommodate text labels
        max_height = max([rect.get_height() for rect in bars])
        min_height = min([rect.get_height() for rect in bars])

        # Increase the limits more significantly (50% increase)
        if max_height >= 0:
            ax2.set_ylim(top=max_height * 1.5)
        else:
            ax2.set_ylim(top=max_height * 0.85)

        if min_height < 0:
            ax2.set_ylim(bottom=min_height * 1.5)
        else:
            ax2.set_ylim(bottom=min_height * 0.85)

        # Add colorbar
        scalarMap.set_array([])
        cbar = plt.colorbar(scalarMap, ax=ax2)
        cbar.set_label('Percent Difference (%)')

        fig2.tight_layout()
        plt.show()

        # Additional Bar Graphs for Fantasy Stat Categories

        # Filter stats for Fantasy Categories
        fantasy_stats = FANTASY_STAT_CATEGORIES
        my_values_fantasy = [self.combined_stats_my_players[stat] for stat in fantasy_stats]
        away_values_fantasy = [self.combined_stats_away_players[stat] for stat in fantasy_stats]
        diff_values_fantasy = [self.evaluation['diff'][stat] for stat in fantasy_stats]
        percent_diff_values_fantasy = [self.evaluation['percent_diff'][stat] for stat in fantasy_stats]

        # Third Bar Graph: Side-by-side comparison (Fantasy Stats)
        x_fantasy = np.arange(len(fantasy_stats))
        width = 0.35

        fig3, ax3 = plt.subplots(figsize=(10, 6))
        rects1_fantasy = ax3.bar(x_fantasy - width/2, my_values_fantasy, width, label='My Players', color='blue')
        rects2_fantasy = ax3.bar(x_fantasy + width/2, away_values_fantasy, width, label='Away Players', color='orange')

        # Add labels and title
        ax3.set_ylabel('Stat Values')
        ax3.set_title('Comparison of Player Stats (Fantasy Categories)')
        ax3.set_xticks(x_fantasy)
        ax3.set_xticklabels(fantasy_stats, rotation=90)
        ax3.legend()

        # Annotate bars with rotated labels
        autolabel(rects1_fantasy, ax3)
        autolabel(rects2_fantasy, ax3)

        # Adjust y-axis limit to accommodate text labels
        all_heights_fantasy = [rect.get_height() for rect in rects1_fantasy + rects2_fantasy]
        max_height_fantasy = max(all_heights_fantasy)
        ax3.set_ylim(top=max_height_fantasy * 1.15)

        fig3.tight_layout()
        plt.show()

        # Fourth Bar Graph: Percent Differences with color coding (Fantasy Stats)
        fig4, ax4 = plt.subplots(figsize=(10, 6))
        bar_positions_fantasy = np.arange(len(fantasy_stats))

        # Normalize the percent differences for color mapping
        max_percent_diff_fantasy = max(abs(min(percent_diff_values_fantasy)), abs(max(percent_diff_values_fantasy)))
        norm_fantasy = colors.Normalize(vmin=-max_percent_diff_fantasy, vmax=max_percent_diff_fantasy)

        # Create a colormap that goes from red (negative) to green (positive)
        scalarMap_fantasy = cmx.ScalarMappable(norm=norm_fantasy, cmap=cmap)

        # Map the percent difference values to colors
        bar_colors_fantasy = [scalarMap_fantasy.to_rgba(value) for value in percent_diff_values_fantasy]

        bars_fantasy = ax4.bar(bar_positions_fantasy, percent_diff_values_fantasy, color=bar_colors_fantasy, edgecolor='black')

        # Add labels and title
        ax4.set_ylabel('Percent Difference (%)')
        ax4.set_title('Percent Difference in Stats (Fantasy Categories)')
        ax4.set_xticks(bar_positions_fantasy)
        ax4.set_xticklabels(fantasy_stats, rotation=90)

        # Draw a horizontal line at y=0
        ax4.axhline(0, color='black', linewidth=0.8)

        # Annotate bars with rotated labels (rotation reduced to 22 degrees)
        for rect in bars_fantasy:
            height = rect.get_height()
            ax4.annotate(f'{height:.2f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 5 if height >= 0 else -15),
                        textcoords="offset points",
                        ha='center', va='bottom' if height >= 0 else 'top', rotation=22)

        # Adjust y-axis limits to accommodate text labels
        max_height_fantasy = max([rect.get_height() for rect in bars_fantasy])
        min_height_fantasy = min([rect.get_height() for rect in bars_fantasy])

        # Increase the limits more significantly (50% increase)
        if max_height_fantasy >= 0:
            ax4.set_ylim(top=max_height_fantasy * 1.5)
        else:
            ax4.set_ylim(top=max_height_fantasy * 0.85)

        if min_height_fantasy < 0:
            ax4.set_ylim(bottom=min_height_fantasy * 1.5)
        else:
            ax4.set_ylim(bottom=min_height_fantasy * 0.85)

        # Add colorbar
        scalarMap_fantasy.set_array([])
        cbar_fantasy = plt.colorbar(scalarMap_fantasy, ax=ax4)
        cbar_fantasy.set_label('Percent Difference (%)')

        fig4.tight_layout()
        plt.show()