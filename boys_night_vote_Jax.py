import os
import random
import math
import time
import sys
import csv
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple, Callable
import tkinter as tk
from tkinter import (
    Tk, Frame, Label, Button, Canvas, Scrollbar, Listbox, Entry,
    messagebox, ttk, SUNKEN, RAISED, FLAT, BOTH, RIGHT, LEFT, Y, END
)
from PIL import Image, ImageTk, ImageDraw

# Model Classes
class JaxVotingSystem:
    def __init__(self):
        self.games: List[str] = []
        self.votes: List[List[int]] = []
        self.voter_names: List[str] = ["Kade", "Jake", "Paden", "Austin", "Jaxson"]
        self.current_voter: int = 0
        self.ranked_games: List[Optional[str]] = []
        self.game_images: Dict[str, ImageTk.PhotoImage] = {}
        self.next_color_index: int = 0
        self.color_palette: List[str] = [
            '#FF0000', '#FF6D00', '#FFDB00', '#92FF00', '#00FF49',
            '#00FFDB', '#0092FF', '#0049FF', '#4900FF', '#B600FF',
            '#FF6D6D', '#E5E5E5', '#999999', '#666666', '#333333'
        ]
        self.winner: Optional[str] = None
        self.round_results: Optional[Dict[str, Any]] = None
        self.eliminated_points: float = 0.0
        self.original_game_order: List[str] = []
        self.num_voters: int = 0

    def add_game(self, game_name: str) -> bool:
        if game_name and game_name not in self.games and len(self.games) < 15:
            self.games.append(game_name)
            return True
        return False

    def remove_game(self, game_name: str) -> bool:
        if game_name in self.games:
            self.games.remove(game_name)
            if game_name in self.game_images:
                del self.game_images[game_name]
            return True
        return False

    def create_game_icon(self, game_name: str) -> bool:
        if game_name not in self.game_images:
            color = self.color_palette[self.next_color_index]
            self.next_color_index = (self.next_color_index + 1) % len(self.color_palette)
            
            base_width = 150
            base_height = 75
            min_width = 100
            max_width = 500
            
            name_length = len(game_name)
            if name_length <= 10:
                icon_width = min_width
            elif name_length <= 20:
                icon_width = base_width
            else:
                icon_width = min(max_width, base_width + (name_length - 20) * 8)
            
            icon_height = base_height
            
            img = Image.new('RGB', (icon_width, icon_height), color)
            draw = ImageDraw.Draw(img)
            
            try:
                from PIL import ImageFont
                
                if name_length <= 10:
                    font_size = 24
                elif name_length <= 20:
                    font_size = 20
                elif name_length <= 30:
                    font_size = 16
                else:
                    font_size = 14
                
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                text_width = font.getlength(game_name)
                
                max_text_width = icon_width - 20
                if text_width > max_text_width:
                    lines = self._wrap_text(draw, game_name, font, max_text_width)
                    self._draw_multiline_text(draw, lines, icon_width, icon_height, font)
                else:
                    self._draw_single_line_text(draw, game_name, icon_width, icon_height, font, text_width)
            except:
                draw.text((10, 30), game_name, fill='white')
                
            self.game_images[game_name] = ImageTk.PhotoImage(img)
            return True
        return False

    def _wrap_text(self, draw: ImageDraw.Draw, text: str, font: Any, max_width: int) -> List[str]:
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_width = font.getlength(test_line)
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines

    def _draw_multiline_text(self, draw: ImageDraw.Draw, lines: List[str], 
                           width: int, height: int, font: Any) -> None:
        line_height = font.size + 4
        total_height = len(lines) * line_height
        y_start = (height - total_height) // 2
        
        border_width = 2
        for i, line in enumerate(lines):
            line_width = font.getlength(line)
            x_pos = (width - line_width) // 2
            y_pos = y_start + i * line_height
            
            for dx in [-border_width, 0, border_width]:
                for dy in [-border_width, 0, border_width]:
                    if dx != 0 or dy != 0:
                        draw.text((x_pos+dx, y_pos+dy), line, fill='black', font=font)
            
            draw.text((x_pos, y_pos), line, fill='white', font=font)

    def _draw_single_line_text(self, draw: ImageDraw.Draw, text: str, 
                             width: int, height: int, font: Any, text_width: float) -> None:
        x_pos = (width - text_width) // 2
        y_pos = (height - font.size) // 2
        
        border_width = 2
        for dx in [-border_width, 0, border_width]:
            for dy in [-border_width, 0, border_width]:
                if dx != 0 or dy != 0:
                    draw.text((x_pos+dx, y_pos+dy), text, fill='black', font=font)
        
        draw.text((x_pos, y_pos), text, fill='white', font=font)

    def calculate_jax_method_voting(self) -> Tuple[Optional[str], Dict[str, Any]]:
        if not self.games:
            return None, {"error": "No games to evaluate", "round": 0}
        
        if not self.votes:
            return None, {"error": "No votes provided", "round": 0, "total_games": len(self.games)}
        
        # Initialize results structure
        round_results = {
            "metadata": {
                "total_games": len(self.games),
                "total_votes": len(self.votes),
                "method": "Jax Method Voting with 50% cascade redistribution"
            },
            "rounds": []
        }
        
        # Convert vote indices to game names
        vote_ballots = [[self.games[idx] for idx in vote] for vote in self.votes]
        
        # Initialize points for each ballot
        ballot_points = []
        points_debug_info = []
        
        for i, vote in enumerate(vote_ballots):
            ballot_dict = {}
            points_desc = []
            for j, game in enumerate(vote):
                points = len(vote) - j  # Top rank gets highest points
                ballot_dict[game] = points
                points_desc.append(f"{game}:{points}")
            ballot_points.append(ballot_dict)
            points_debug_info.append(f"Ballot {i+1}: {', '.join(points_desc)}")
        
        round_results["metadata"]["initial_points_distribution"] = points_debug_info
        
        # Active games (not eliminated)
        active_games = set(self.games)
        round_num = 1
        
        while len(active_games) > 3:
            round_info = self._process_round(round_num, active_games, ballot_points, vote_ballots)
            round_results["rounds"].append(round_info)
            
            # Check if we have a winner with >50% of total points
            total_points = sum(round_info["game_totals"].values())
            for game, points in round_info["game_totals"].items():
                if points > total_points * 0.51:
                    round_results["winner"] = game
                    round_results["podium"] = [{"position": 1, "game": game, "score": points}]
                    return game, round_results
            
            # Eliminate the lowest scoring game
            eliminated_game = round_info["eliminated"]
            active_games.remove(eliminated_game)
            
            # Redistribute points for the eliminated game
            self._redistribute_points(eliminated_game, active_games, ballot_points, vote_ballots)
            
            round_num += 1
        
        # Final round with 3 or fewer games
        final_round = self._process_final_round(round_num, active_games, ballot_points)
        round_results["rounds"].append(final_round)
        round_results["podium"] = final_round["podium"]
        round_results["winner"] = final_round["podium"][0]["game"]
        
        self.winner = round_results["winner"]
        self.round_results = round_results
        
        return round_results["winner"], round_results

    def _process_round(self, round_num: int, active_games: set, ballot_points: List[Dict[str, float]], 
                      vote_ballots: List[List[str]]) -> Dict[str, Any]:
        # Calculate current totals for each game
        game_totals = {game: 0.0 for game in active_games}
        for ballot in ballot_points:
            for game, points in ballot.items():
                if game in active_games:
                    game_totals[game] += points
        
        # Check for tie at the bottom
        min_score = min(game_totals.values())
        eliminated_candidates = [game for game in game_totals if game_totals[game] == min_score]
        
        # Break tie if necessary
        if len(eliminated_candidates) > 1:
            eliminated_game = self._break_tie(eliminated_candidates, vote_ballots, active_games)
        else:
            eliminated_game = eliminated_candidates[0]
        
        # Calculate percentage of total points
        total_points = sum(game_totals.values())
        percentages = {game: (score / total_points * 100) for game, score in game_totals.items()}
        
        return {
            "round": round_num,
            "game_totals": game_totals,
            "percentages": percentages,
            "eliminated": eliminated_game,
            "active_games": list(active_games)
        }

    def _process_final_round(self, round_num: int, active_games: set, ballot_points: List[Dict[str, float]]) -> Dict[str, Any]:
        # Calculate final totals
        game_totals = {game: 0.0 for game in active_games}
        for ballot in ballot_points:
            for game, points in ballot.items():
                if game in active_games:
                    game_totals[game] += points
        
        # Create podium ranking
        sorted_games = sorted(game_totals.items(), key=lambda x: x[1], reverse=True)
        podium = []
        for i, (game, points) in enumerate(sorted_games):
            podium.append({"position": i+1, "game": game, "score": points})
        
        return {
            "round": round_num,
            "game_totals": game_totals,
            "podium": podium,
            "active_games": list(active_games)
        }

    def _redistribute_points(self, eliminated_game: str, active_games: set, 
                            ballot_points: List[Dict[str, float]], vote_ballots: List[List[str]]):
        for i, ballot in enumerate(ballot_points):
            if eliminated_game not in ballot:
                continue
                
            # Get the points to redistribute
            points_pool = ballot[eliminated_game]
            del ballot[eliminated_game]
            
            # Find the remaining games in this ballot in order
            ballot_order = vote_ballots[i]
            remaining_in_ballot = [game for game in ballot_order if game in active_games and game != eliminated_game]
            
            # Redistribute points with 50% cascade
            for game in remaining_in_ballot:
                allocation = points_pool * 0.5
                ballot[game] = ballot.get(game, 0) + allocation
                points_pool -= allocation
                
                if points_pool < 0.001:  # negligible amount
                    break

    def _break_tie(self, candidates: List[str], vote_ballots: List[List[str]], active_games: set) -> str:
        # Count last place votes for each candidate
        last_place_counts = {candidate: 0 for candidate in candidates}
        
        for ballot in vote_ballots:
            # Find the active game with the worst rank in this ballot
            worst_rank = -1
            worst_game = None
            
            for rank, game in enumerate(ballot):
                if game in candidates and game in active_games:
                    if rank > worst_rank:
                        worst_rank = rank
                        worst_game = game
            
            if worst_game:
                last_place_counts[worst_game] += 1
        
        # Find candidate with most last place votes
        max_last_place = max(last_place_counts.values())
        worst_candidates = [c for c in candidates if last_place_counts[c] == max_last_place]
        
        if len(worst_candidates) == 1:
            return worst_candidates[0]
        
        # If still tied, check second-to-last place votes, etc.
        return self._break_tie_deep(worst_candidates, vote_ballots, active_games, 1)
    
    def _break_tie_deep(self, candidates: List[str], vote_ballots: List[List[str]], 
                       active_games: set, depth: int) -> str:
        if len(candidates) == 1:
            return candidates[0]
        
        # Count nth worst place votes (depth = 1 means second worst, etc.)
        place_counts = {candidate: 0 for candidate in candidates}
        
        for ballot in vote_ballots:
            # Get all active candidate positions in this ballot
            candidate_positions = []
            for rank, game in enumerate(ballot):
                if game in candidates and game in active_games:
                    candidate_positions.append((rank, game))
            
            # Sort by rank (worst first)
            candidate_positions.sort(reverse=True)
            
            # Count the depth-th worst candidate
            if len(candidate_positions) > depth:
                _, worst_game = candidate_positions[depth]
                place_counts[worst_game] += 1
        
        # Find candidate with most votes at this depth
        max_count = max(place_counts.values())
        worst_candidates = [c for c in candidates if place_counts[c] == max_count]
        
        if len(worst_candidates) == 1:
            return worst_candidates[0]
        
        # If still tied, go deeper
        if depth < len(candidates):
            return self._break_tie_deep(worst_candidates, vote_ballots, active_games, depth + 1)
        
        # If all else fails, random choice
        return random.choice(candidates)

    def save_results(self) -> Optional[str]:
        results_dir = "voting_results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        if not hasattr(self, 'round_results') or not self.round_results:
            return None
        
        # Extract rounds and metadata from the new structure
        rounds = self.round_results.get('rounds', [])
        metadata = self.round_results.get('metadata', {})
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_filename = os.path.join(results_dir, f"jax_method_results_{timestamp}.txt")
        csv_filename = os.path.join(results_dir, f"jax_method_results_{timestamp}.csv")
        
        with open(text_filename, 'w', encoding='utf-8') as f:
            if metadata:
                f.write("VOTING RESULTS METADATA\n")
                f.write("=" * 50 + "\n")
                f.write(f"Total Games: {metadata.get('total_games', 'N/A')}\n")
                f.write(f"Total Votes: {metadata.get('total_votes', 'N/A')}\n")
                f.write(f"Method: {metadata.get('method', 'N/A')}\n\n")
                
                if 'initial_points_distribution' in metadata:
                    f.write("Initial Points Distribution:\n")
                    f.write("-" * 30 + "\n")
                    for line in metadata['initial_points_distribution']:
                        f.write(f"{line}\n")
                    f.write("\n")
            
            f.write("JAX METHOD VOTING RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            for round_data in rounds:
                f.write(f"ROUND {round_data['round']}\n")
                f.write("-" * 20 + "\n")
                
                # Write game totals in descending order
                sorted_games = sorted(round_data['game_totals'].items(), 
                                     key=lambda x: x[1], reverse=True)
                for game, score in sorted_games:
                    percentage = round_data.get('percentages', {}).get(game, 0)
                    f.write(f"{game}: {score:.2f} points ({percentage:.1f}%)\n")
                
                # Calculate and write total points
                total_points = sum(round_data['game_totals'].values())
                f.write(f"Total Points: {total_points:.2f}\n")
                
                # Write eliminated game
                if 'eliminated' in round_data:
                    f.write(f"Eliminated: {round_data['eliminated']}\n")
                
                # Write active games count
                active_count = len(round_data.get('active_games', []))
                total_games = metadata.get('total_games', 0)
                progress_percent = ((total_games - active_count) / total_games * 100) if total_games > 0 else 0
                f.write(f"Progress: {total_games - active_count}/{total_games} ({progress_percent:.1f}%)\n")
                
                # Check for 51% winner
                for game, percentage in round_data.get('percentages', {}).items():
                    if percentage > 50:
                        f.write(f"INSTANT WINNER: {game} with {percentage:.1f}% of votes\n")
                        break
                
                f.write("\n")
            
            f.write("FINAL RESULT\n")
            f.write("=" * 50 + "\n")
            
            # Write podium results
            if 'podium' in self.round_results:
                podium = self.round_results['podium']
                f.write("Olympic-Style Podium Results:\n")
                f.write("-" * 30 + "\n")
                for entry in podium:
                    position_suffix = "st" if entry['position'] == 1 else "nd" if entry['position'] == 2 else "rd"
                    f.write(f"{entry['position']}{position_suffix}: {entry['game']} ({entry['score']:.2f} points)\n")
                f.write(f"\nOverall Winner: {self.winner}\n")
            elif self.winner:
                f.write(f"Winner: {self.winner}\n")
            else:
                f.write("No winner determined.\n")

        self._save_results_csv(csv_filename, rounds)
        
        return text_filename
    def _save_results_csv(self, filename: str, rounds: List[Dict[str, Any]]) -> None:
        # Get all unique games across all rounds
        all_games = set()
        for round_data in rounds:
            if 'game_totals' in round_data:
                all_games.update(round_data['game_totals'].keys())
        
        all_games = sorted(all_games)  # Sort for consistent ordering
        
        # Create header row
        headers = ['Game'] + [f'Round {i+1}' for i in range(len(rounds))]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            # Create a row for each game
            for game in all_games:
                row = [game]
                
                # Add values for each round
                for round_data in rounds:
                    if 'game_totals' in round_data and game in round_data['game_totals']:
                        row.append(round(round_data['game_totals'][game], 2))
                    else:
                        row.append('')  # Empty cell if game was eliminated
                        
                writer.writerow(row)

# View Classes
class BaseView:
    def __init__(self, root: Tk, controller: Any):
        self.root = root
        self.controller = controller
        self.frame = Frame(root)
        
    def show(self) -> None:
        self.frame.pack(fill=BOTH, expand=True)
        
    def hide(self) -> None:
        self.frame.pack_forget()


class SuggestionView(BaseView):
    def __init__(self, root: Tk, controller: Any):
        super().__init__(root, controller)
        self.game_entry: Optional[Entry] = None
        self.suggest_button: Optional[Button] = None
        self.game_listbox: Optional[Listbox] = None
        self.create_widgets()
        
    def create_widgets(self) -> None:
        Label(self.frame, 
             text="Enter Game Suggestions (Max 15)", 
             font=('Arial', self.controller.get_scaled_font_size(20))).pack(pady=(20, 10))
        
        input_frame = Frame(self.frame)
        input_frame.pack(pady=10)
        
        self.game_entry = Entry(input_frame, width=30, 
                              font=('Arial', self.controller.get_scaled_font_size(14)))
        self.game_entry.pack(side=LEFT, padx=5)
        self.game_entry.bind('<Return>', lambda event: self.controller.add_game(self.game_entry.get().strip().title()))
        self.game_entry.focus_set()
        
        self.suggest_button = Button(input_frame, text="Add Game", 
                                   font=('Arial', self.controller.get_scaled_font_size(14)), 
                                   command=lambda: self.controller.add_game(self.game_entry.get().strip().title()))
        self.suggest_button.pack(side=LEFT, padx=5)
        
        list_frame = Frame(self.frame)
        list_frame.pack(pady=20, expand=True, fill=BOTH, padx=20)
        
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.game_listbox = Listbox(list_frame, 
                                  width=40,
                                  height=15,
                                  font=('Arial', self.controller.get_scaled_font_size(12)),
                                  yscrollcommand=scrollbar.set)
        self.game_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.game_listbox.yview)
        
        self.game_listbox.bind('<Double-1>', self.on_remove_game)
        
        Button(self.frame, 
              text="Done", 
              font=('Arial', self.controller.get_scaled_font_size(16)),
              command=self.controller.start_voting_phase).pack(pady=20)
    
    def on_remove_game(self, event: Any) -> None:
        selection = self.game_listbox.curselection()
        if selection:
            index = selection[0]
            game = self.game_listbox.get(index)
            self.controller.remove_game(game)
    
    def update_game_list(self, games: List[str]) -> None:
        self.game_listbox.delete(0, END)
        for game in games:
            self.game_listbox.insert(END, game)
        
    def clear_entry(self) -> None:
        if self.game_entry:
            self.game_entry.delete(0, END)
            self.game_entry.focus_set()


class VotingView(BaseView):
    def __init__(self, root: Tk, controller: Any):
        super().__init__(root, controller)
        self.dragged_widget: Optional[Label] = None
        self.drag_start_x: int = 0
        self.drag_start_y: int = 0
        self.original_positions: Dict[str, Tuple[int, int]] = {}
        self.draggable_labels: List[Label] = []
        self.slot_widgets: List[Label] = []
        self.placeholder: Optional[Label] = None
        self.floating_label: Optional[Label] = None
        self.game_pool_container: Optional[Frame] = None
        self.ranking_container: Optional[Frame] = None
        
    def create_widgets(self, voter_name: str, games: List[str]) -> None:
        Label(self.frame, 
             text=f"{voter_name}'s Vote", 
             font=('Arial', self.controller.get_scaled_font_size(20))).pack(pady=(10, 20))
        
        Label(self.frame, 
             text="Drag games to rank them from best (1) to worst", 
             font=('Arial', self.controller.get_scaled_font_size(14))).pack(pady=(0, 10))
        
        panels_frame = Frame(self.frame)
        panels_frame.pack(fill=BOTH, expand=True, pady=20)
        
        left_panel = Frame(panels_frame, relief=RAISED, bd=1)
        left_panel.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        
        Label(left_panel, 
             text="Game Pool (Drag to rank)", 
             font=('Arial', self.controller.get_scaled_font_size(14))).pack(pady=(10, 5))
        
        self.game_pool_container = Frame(left_panel, height=250, width=800)
        self.game_pool_container.pack_propagate(False)
        self.game_pool_container.pack(pady=10)
        
        right_panel = Frame(panels_frame, relief=RAISED, bd=1)
        right_panel.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))
        
        Label(right_panel, 
             text="Your Ranking (1 = Best)", 
             font=('Arial', self.controller.get_scaled_font_size(14))).pack(pady=(10, 5))
        
        self.ranking_container = Frame(right_panel, height=250, width=800)
        self.ranking_container.pack_propagate(False)
        self.ranking_container.pack(pady=10)
        
        Button(self.frame, 
              text="Submit Vote", 
              font=('Arial', self.controller.get_scaled_font_size(14)),
              command=self.controller.submit_vote).pack(pady=20)
        
        self.setup_drag_drop_interface(games)
    
    def setup_drag_drop_interface(self, games: List[str]) -> None:
        for widget in self.game_pool_container.winfo_children():
            widget.destroy()
                
        for widget in self.ranking_container.winfo_children():
            widget.destroy()
        
        shuffled_games = games[:]
        random.shuffle(shuffled_games)
        
        self.draggable_labels = []
        self.original_positions = {}
        
        max_per_row = 5
        
        for i, game in enumerate(shuffled_games):
            row = i // max_per_row
            column = i % max_per_row
            
            frame = Frame(self.game_pool_container)
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
            
            self.original_positions[game] = (row, column)
            
            self.game_pool_container.grid_rowconfigure(row, weight=1)
            self.game_pool_container.grid_columnconfigure(column, weight=1)
            
            lbl = Label(frame, image=self.controller.get_game_image(game), compound='center')
            lbl.image = self.controller.get_game_image(game)
            lbl.pack(expand=True, fill=BOTH)
            lbl.game_name = game
            lbl.bind('<Button-1>', self.on_drag_start)
            lbl.bind('<B1-Motion>', self.on_drag_motion)
            lbl.bind('<ButtonRelease-1>', self.on_drag_end)
            self.draggable_labels.append(lbl)
        
        self.slot_widgets = []
        
        num_rows = (len(games) + 2) // 3
        
        for r in range(num_rows):
            self.ranking_container.grid_rowconfigure(r, weight=1)
        for c in range(3):
            self.ranking_container.grid_columnconfigure(c, weight=1)
        
        for i in range(len(games)):
            row = i % num_rows
            column = i // num_rows
            
            slot_frame = Frame(self.ranking_container)
            slot_frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
            
            slot_num = Label(slot_frame, 
                           text=f"{i+1}.", 
                           width=5, 
                           relief=SUNKEN, 
                           padx=10, 
                           pady=10,
                           font=('Arial', 24))
            slot_num.pack(side=LEFT, padx=5)
            
            slot = Label(slot_frame, 
                       width=20, 
                       height=3, 
                       relief=RAISED,
                       font=('Arial', 24))
            slot.pack(side=LEFT, padx=5, fill=BOTH, expand=True)
            slot.game_name = None
            slot.slot_index = i
            slot.bind('<Button-1>', self.on_slot_click)
            self.slot_widgets.append(slot)
    
    def on_drag_start(self, event: Any) -> None:
        self.dragged_widget = event.widget
        
        self.original_frame = self.dragged_widget.master
        
        self.placeholder = Label(self.original_frame, 
                                width=20, 
                                height=3, 
                                relief=FLAT,
                                bg='SystemButtonFace')
        self.placeholder.pack(expand=True, fill=BOTH)
        
        self.dragged_widget.pack_forget()
        
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        self.floating_label = Label(self.root, 
                                   image=self.dragged_widget.image, 
                                   compound='center')
        self.floating_label.image = self.dragged_widget.image
        self.floating_label.place(x=event.x_root, y=event.y_root)
        self.floating_label.lift()
        
    def on_drag_motion(self, event: Any) -> None:
        if self.floating_label:
            x = event.x_root - self.drag_start_x
            y = event.y_root - self.drag_start_y
            self.floating_label.place(x=x, y=y)

    def on_drag_end(self, event: Any) -> None:
        if not self.dragged_widget:
            return
            
        if self.floating_label:
            self.floating_label.place_forget()
            self.floating_label.destroy()
            self.floating_label = None
                
        dropped_on_slot = False
        for slot in self.slot_widgets:
            if (event.x_root >= slot.winfo_rootx() and 
                event.x_root <= slot.winfo_rootx() + slot.winfo_width() and
                event.y_root >= slot.winfo_rooty() and 
                event.y_root <= slot.winfo_rooty() + slot.winfo_height()):
                
                dropped_on_slot = True
                if slot.game_name:
                    old_game = slot.game_name
                    self.controller.return_game_to_pool(old_game, self.original_positions[old_game])
                    
                self.controller.place_game_in_slot(
                    self.dragged_widget.game_name, 
                    slot.slot_index,
                    slot
                )
                
                if self.placeholder:
                    self.placeholder.destroy()
                break
        
        if not dropped_on_slot and self.placeholder:
            self.placeholder.destroy()
            self.dragged_widget.pack(expand=True, fill=BOTH)
        
        self.dragged_widget = None

    def on_slot_click(self, event: Any) -> None:
        slot = event.widget
        if slot.game_name:
            self.controller.return_game_to_pool(slot.game_name, self.original_positions[slot.game_name])
            
            slot.config(text='', bg='SystemButtonFace')
            slot.game_name = None
    
    def get_ranked_games(self) -> List[Optional[str]]:
        ranked = [None] * len(self.slot_widgets)
        for slot in self.slot_widgets:
            if slot.game_name:
                ranked[slot.slot_index] = slot.game_name
        return ranked
    
    def restore_game_to_pool(self, game_name: str, position: Tuple[int, int]) -> None:
        for lbl in self.draggable_labels:
            if lbl.game_name == game_name:
                row, col = position
                lbl.master.grid(row=row, column=col)
                lbl.pack(expand=True, fill=BOTH)
                break


class ResultsView(BaseView):
    def __init__(self, root: Tk, controller: Any):
        super().__init__(root, controller)
        self.nav_frame: Optional[Frame] = None
        self.current_round_index: int = 0
        self.round_results: Dict[str, Any] = {}
        self.games: List[str] = []
        self.votes: List[List[int]] = []
        self.voter_names: List[str] = []
        self.filename: str = ""
        self.winner: Optional[str] = None
        self.trashcan_image: Optional[ImageTk.PhotoImage] = None
        self.results_canvas: Optional[Canvas] = None
        self.round_counter: Optional[Label] = None
        self.detailed_button: Optional[Button] = None
        self.restart_button: Optional[Button] = None
        self.bg_color: str = 'SystemButtonFace'
        self.text_color: str = 'SystemWindowText'
        self.button_color: str = 'SystemButtonFace'
        self.button_text_color: str = 'SystemWindowText'
        
    def create_widgets(self, winner: Optional[str], round_results: Dict[str, Any], 
                      filename: str, games: List[str], votes: List[List[int]], 
                      voter_names: List[str]) -> None:
        """Initialize the results view with voting data"""
        # Clear existing widgets
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # Store data
        self.winner = winner
        self.round_results = round_results
        self.filename = filename
        self.games = games
        self.votes = votes
        self.voter_names = voter_names
        
        # Reset state
        self.current_round_index = 0
        
        # Create header
        self._create_header()
        
        # Create round counter
        self._create_round_counter()
        
        # Create results frame
        self.results_frame = Frame(self.frame, bg=self.bg_color)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create control frame with save button
        self._create_control_frame()
        
        # Set up animation view
        self.setup_animation_view()
        
        # Always start with the first elimination round, even if we have podium data
        # The podium will be shown after all elimination rounds are completed
        self.animate_elimination_round()

    def _create_header(self) -> None:
        """Create the results header"""
        header = Label(
            self.frame,
            text="Boys Night Points Voting Results",
            font=("Arial", 20, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        header.pack(pady=20)

    def _create_round_counter(self) -> None:
        """Create the round counter label"""
        total_rounds = len(self.round_results.get('rounds', []))
        # Add 1 for the final results screen if we have podium data
        if self._has_podium_data():
            total_rounds += 1
            
        self.round_counter = Label(
            self.frame,
            text=f"Round 1 of {total_rounds}",
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.round_counter.pack()

    def _create_control_frame(self) -> None:
        """Create the control frame with save button"""
        control_frame = Frame(self.frame, bg=self.bg_color)
        control_frame.pack(fill="x", pady=10)
        
        save_button = Button(
            control_frame,
            text="Save Results", 
            command=self.controller.save_results,
            bg=self.button_color,
            fg=self.button_text_color,
            font=("Arial", 10),
            relief="flat",
            padx=15,
            pady=5
        )
        save_button.pack(side="right", padx=20)

    def _has_podium_data(self) -> bool:
        """Check if podium data exists in the results"""
        # Check for podium data in both possible locations
        has_podium = 'podium' in self.round_results
        is_final_round_podium = (len(self.round_results.get('rounds', [])) > 0 and 
                                'podium' in self.round_results['rounds'][-1])
        return has_podium or is_final_round_podium

    def setup_animation_view(self) -> None:
        """Set up the animation view with canvas and scroll support"""
        # Create a frame to contain the canvas and ensure proper sizing
        canvas_container = Frame(self.results_frame)
        canvas_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas with proper configuration
        self.results_canvas = Canvas(canvas_container, bg='lightgray')
        self.results_canvas.pack(fill=BOTH, expand=True)
        
        # Add mousewheel scrolling support
        self.results_canvas.bind("<MouseWheel>", self.on_mousewheel)
        
        self.create_trashcan_image()

    def create_trashcan_image(self) -> None:
        """Create a trashcan image for animations"""
        trashcan_size = 400  # Doubled again to make it much larger
        img = Image.new('RGB', (trashcan_size, trashcan_size), 'lightgray')
        draw = ImageDraw.Draw(img)
        
        # Calculate proportional coordinates based on size
        body_left = trashcan_size * 0.2    # 80
        body_top = trashcan_size * 0.2     # 80
        body_right = trashcan_size * 0.8   # 320
        body_bottom = trashcan_size * 0.8  # 320
        
        lid_left = trashcan_size * 0.1     # 40
        lid_top = trashcan_size * 0.1      # 40
        lid_right = trashcan_size * 0.9    # 360
        lid_bottom = trashcan_size * 0.2   # 80
        
        # Draw the main body of the trashcan
        draw.rectangle(
            [body_left, body_top, body_right, body_bottom], 
            fill='gray', outline='black', width=6
        )
        
        # Draw the lid
        draw.rectangle(
            [lid_left, lid_top, lid_right, lid_bottom], 
            fill='darkgray', outline='black', width=6
        )
        
        # Add vertical bars (changed from horizontal lines)
        bar_spacing = trashcan_size * 0.05  # 20 pixels
        bar_start_x = body_left + bar_spacing  # 100
        bar_end_x = body_right - bar_spacing   # 300
        bar_top = body_top + bar_spacing       # 100
        bar_bottom = body_bottom - bar_spacing # 300
        
        for i in range(int(bar_start_x), int(bar_end_x), int(bar_spacing * 2)):
            draw.line([i, bar_top, i, bar_bottom], fill='black', width=4)
        
        self.trashcan_image = ImageTk.PhotoImage(img)

    def on_mousewheel(self, event: Any) -> None:
        """Handle mousewheel scrolling on the canvas"""
        self.results_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def animate_elimination_round(self) -> None:
        """Animate the current elimination round"""
        rounds = self.round_results.get('rounds', [])
        
        # Check if we've processed all elimination rounds
        if self.current_round_index >= len(rounds):
            # Only show final results if we have podium data
            if self._has_podium_data():
                self.show_final_results()
            else:
                # If no podium data but we've processed all rounds, show winner animation
                self.show_winner_animation()
            return
            
        round_data = rounds[self.current_round_index]
        
        # Clear canvas
        self.results_canvas.delete("all")
        
        # Get current canvas dimensions
        canvas_width, canvas_height = self._get_canvas_dimensions()
        center_x = canvas_width // 2
        
        # Display round header
        self.results_canvas.create_text(
            center_x, 30,
            text=f"Round {round_data['round']}",
            font=("Arial", 24, "bold"),
            fill="black"
        )
        
        # Check if this is the final elimination round (before winner reveal)
        is_final_round = (self.current_round_index == len(rounds) - 1)
        
        if is_final_round:
            # Display suspense message instead of scores
            self.results_canvas.create_text(
                center_x, canvas_height // 2,
                text="And the winner is..!",
                font=("Arial", 76, "bold"),
                fill="black"
            )
            
          # Add some decorative elements to build anticipation
            self.results_canvas.create_text(
                center_x, canvas_height // 2 + 95,
                text=f"You punks had better've voted for Jaxson's nominee!",
                font=("Arial", 25, "italic"),
                fill="gray"
            )
        else:
            # Display scores with percentages and bar charts for non-final rounds
            y_pos = 70
            total_points = sum(round_data['game_totals'].values())
            sorted_games = sorted(round_data['game_totals'].items(), key=lambda x: x[1], reverse=True)
            max_score = max(round_data['game_totals'].values()) if round_data['game_totals'] else 1

            for game, score in sorted_games:
                self._draw_score_bar(game, score, total_points, max_score, center_x, y_pos, canvas_width)
                y_pos += 30
        
        # Display elimination explanation (unless it's the final round)
        eliminated_game = round_data.get('eliminated')
        if eliminated_game and not is_final_round:
            y_pos = self._draw_elimination_explanation(round_data, eliminated_game, center_x, y_pos, canvas_width)
        
        # Display total points and eliminated points (unless it's the final round)
        if not is_final_round:
            y_pos = self._draw_points_info(round_data, center_x, y_pos)
        
        # Position trashcan at bottom right
        self._draw_trashcan(canvas_width, canvas_height)
        
        # Create navigation controls
        self._create_navigation_controls()
        
        # Update round counter
        total_rounds = len(rounds)
        # Add 1 for the final results screen if we have podium data
        if self._has_podium_data():
            total_rounds += 1
            
        self.round_counter.config(text=f"Round {self.current_round_index + 1} of {total_rounds}")
        
        # Animate eliminated games if any (unless it's the final round)
        if eliminated_game and not is_final_round:
            trashcan_x = canvas_width - 300
            trashcan_y = canvas_height - 300
            self.controller.root.after(1000, lambda: self.animate_games_sequentially(
                [eliminated_game], trashcan_x, trashcan_y
            ))

    def _get_canvas_dimensions(self) -> Tuple[int, int]:
        """Get the current canvas dimensions with fallback defaults"""
        canvas_width = self.results_canvas.winfo_width()
        canvas_height = self.results_canvas.winfo_height()
        
        # Use default dimensions if canvas hasn't been rendered yet
        if canvas_width <= 1:
            canvas_width = 1920
        if canvas_height <= 1:
            canvas_height = 1080
            
        return canvas_width, canvas_height

    def _draw_score_bar(self, game: str, score: float, total_points: float, 
                       max_score: float, center_x: int, y_pos: int, 
                       canvas_width: int) -> None:
        """Draw a score bar for a game"""
        percentage = (score / total_points * 100) if total_points > 0 else 0
        
        # Get color for this game
        if game in self.games:
            color_index = self.games.index(game) % len(self.controller.get_color_palette())
            color = self.controller.get_color_palette()[color_index]
        else:
            color = "gray"
        
        # Create bar chart visualization
        bar_width = min(400, canvas_width * 0.6)  # Responsive bar width
        bar_fill = (score / max_score) * bar_width if max_score > 0 else 0
        
        # Position bars in the center
        bar_x = center_x - bar_width // 2
        
        # Draw bar background
        self.results_canvas.create_rectangle(
            bar_x, y_pos - 10,
            bar_x + bar_width, y_pos + 10,
            fill='#EEEEEE', outline=''
        )
        
        # Draw filled portion of bar
        self.results_canvas.create_rectangle(
            bar_x, y_pos - 10,
            bar_x + bar_fill, y_pos + 10,
            fill=color, outline=''
        )
        
        # Add score text
        self.results_canvas.create_text(
            bar_x + bar_width + 10, y_pos,
            text=f"{game}: {score:.1f} points ({percentage:.1f}%)",
            font=("Arial", 12),
            fill=color,
            anchor="w"
        )

    def _draw_elimination_explanation(self, round_data: Dict[str, Any], 
                                    eliminated_game: str, center_x: int, 
                                    y_pos: int, canvas_width: int) -> int:
        """Draw the elimination explanation and return the new y position"""
        min_score = min(round_data['game_totals'].values()) if round_data['game_totals'] else 0
        
        explanation = f"{eliminated_game} was eliminated for having the lowest score ({min_score:.1f} points)"
        
        # Wrap text if it's too long
        max_width = canvas_width - 40
        lines = self._wrap_text(explanation, max_width, 10)  # 10 pixels per character estimate
        
        for i, line in enumerate(lines):
            self.results_canvas.create_text(
                center_x, y_pos + 20 + i * 20,
                text=line,
                font=("Arial", 12, "bold"),
                fill="red",
                anchor="center"
            )
        
        return y_pos + 20 * len(lines) + 20

    def _wrap_text(self, text: str, max_width: int, char_width: int) -> List[str]:
        """Wrap text to fit within a specified width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            # Approximate text width
            if len(test_line) * char_width > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line)
            
        return lines

    def _draw_points_info(self, round_data: Dict[str, Any], center_x: int, y_pos: int) -> int:
        """Draw points information and return the new y position"""
        total_points = sum(round_data['game_totals'].values()) if round_data['game_totals'] else 0
        
        self.results_canvas.create_text(
            center_x, y_pos + 20,
            text=f"Total Points: {total_points:.1f}",
            font=("Arial", 50, "bold"),
            fill="black",
            anchor="center"
        )
        y_pos += 30
        
        return y_pos

    def _draw_trashcan(self, canvas_width: int, canvas_height: int) -> None:
        """Draw the trashcan image on the canvas"""
        # Get the actual size of the trashcan image
        trashcan_width = 400  # Should match the size you set in create_trashcan_image
        trashcan_height = 400
        
        # Position with proper margin from edges
        margin = 50  # Desired margin from canvas edges
        trashcan_x = canvas_width - margin - (trashcan_width // 2)
        trashcan_y = canvas_height - margin - (trashcan_height // 2)
        
        if self.trashcan_image:
            self.results_canvas.create_image(
                trashcan_x, trashcan_y,
                image=self.trashcan_image,
                anchor="center"
            )

    def _create_navigation_controls(self) -> None:
        """Create navigation controls for round navigation"""
        # Remove previous navigation frame if it exists
        if self.nav_frame:
            self.nav_frame.destroy()
        
        # Create single navigation frame
        self.nav_frame = Frame(self.frame)
        self.nav_frame.pack(pady=10)
        
        rounds = self.round_results.get('rounds', [])
        
        # Add previous button if not on first round
        if self.current_round_index > 0:
            prev_button = Button(
                self.nav_frame,
                text="Previous Round",
                command=self.previous_round,
                font=("Arial", 12),
                padx=15,
                pady=5
            )
            prev_button.pack(side="left", padx=10)
        
        # Add next button or final results button
        if self.current_round_index < len(rounds) - 1:
            next_button = Button(
                self.nav_frame,
                text="Next Round",
                command=self.next_round,
                font=("Arial", 12),
                padx=15,
                pady=5
            )
            next_button.pack(side="left", padx=10)
        else:
            # Check if we have podium data for final results
            if self._has_podium_data():
                final_button = Button(
                    self.nav_frame,
                    text="Show Final Results",
                    command=self.show_final_results,
                    font=("Arial", 12),
                    padx=15,
                    pady=5
                )
                final_button.pack(side="left", padx=10)
            else:
                # If no podium data, just show the winner
                final_button = Button(
                    self.nav_frame,
                    text="Show Winner",
                    command=self.show_winner_animation,
                    font=("Arial", 12),
                    padx=15,
                    pady=5
                )
                final_button.pack(side="left", padx=10)

    def animate_games_sequentially(self, games: List[str], trashcan_x: int, trashcan_y: int) -> None:
        """Animate games being eliminated sequentially"""
        if not games:
            rounds = self.round_results.get('rounds', [])
            if self.current_round_index < len(rounds) - 1:
                self.controller.root.after(1000, self.next_round)
            else:
                # After last elimination round, show final results if we have podium data
                if self._has_podium_data():
                    self.controller.root.after(1000, self.show_final_results)
                else:
                    self.controller.root.after(1000, self.show_winner_animation)
            return
                
        game = games.pop(0)
        
        # Get color for this game
        if game in self.games:
            game_index = self.games.index(game)
            color = self.controller.get_color_palette()[game_index % len(self.controller.get_color_palette())]
        else:
            color = "gray"
        
        # Get current canvas dimensions
        canvas_width, canvas_height = self._get_canvas_dimensions()
        
        # Find the position of this game in the results display
        round_data = self.round_results['rounds'][self.current_round_index]
        sorted_games = sorted(round_data['game_totals'].items(), key=lambda x: x[1], reverse=True)
        
        # Calculate the position based on the game's ranking
        start_y = 100  # Default starting position
        for i, (game_name, score) in enumerate(sorted_games):
            if game_name == game:
                # Position the game at its rank in the results
                start_y = 100 + i * 30  # 30 pixels between each game
                break
        
        # Position game text at the left side of the canvas
        start_x = 50
        
        game_id = self.results_canvas.create_text(
            start_x, start_y,
            text=game,
            font=('Arial', 75, 'bold'),
            fill=color,
            anchor='w'  # Anchor to the west (left) side
        )
        
        self.controller.root.after(500, lambda: self.animate_movement_with_callback(
            game_id, trashcan_x, trashcan_y, 15,
            lambda: self.on_game_reached_trashcan(game_id, games, trashcan_x, trashcan_y)
        ))
        
    def animate_movement_with_callback(self, item_id: int, target_x: int, target_y: int, 
                                     steps: int, callback: Callable) -> None:
        """Animate movement of an item with a callback when complete"""
        if not self.results_canvas or not self.results_canvas.winfo_exists():
            return
            
        current_coords = self.results_canvas.coords(item_id)
        if len(current_coords) < 2:
            callback()
            return
            
        current_x, current_y = current_coords[0], current_coords[1]
        
        if abs(current_x - target_x) < 5 and abs(current_y - target_y) < 5:
            self.results_canvas.delete(item_id)
            callback()
            return
            
        new_x = current_x + (target_x - current_x) / (steps / .55)
        new_y = current_y + (target_y - current_y) / (steps / .55)
        
        self.results_canvas.coords(item_id, new_x, new_y)
        
        if self.results_canvas.winfo_exists():
            self.controller.root.after(10, lambda: self.animate_movement_with_callback(
                item_id, target_x, target_y, steps, callback
            ))

    def on_game_reached_trashcan(self, game_id: int, remaining_games: List[str], 
                               trashcan_x: int, trashcan_y: int) -> None:
        """Handle when a game reaches the trashcan"""
        # Simply remove the game and proceed
        self.results_canvas.delete(game_id)
        
        if remaining_games:
            self.controller.root.after(500, lambda: self.animate_games_sequentially(
                remaining_games, trashcan_x, trashcan_y
            ))
        elif self.current_round_index < len(self.round_results.get('rounds', [])) - 1:
            self.controller.root.after(1000, self.next_round)
        else:
            # After last elimination round, show final results if we have podium data
            if self._has_podium_data():
                self.controller.root.after(1000, self.show_final_results)
            else:
                self.controller.root.after(1000, self.show_winner_animation)

    def next_round(self) -> None:
        """Move to the next round"""
        rounds = self.round_results.get('rounds', [])
        if self.current_round_index < len(rounds) - 1:
            self.current_round_index += 1
            self.animate_elimination_round()
        else:
            # After last elimination round, show final results if we have podium data
            if self._has_podium_data():
                self.show_final_results()
            else:
                self.show_winner_animation()

    def previous_round(self) -> None:
        """Move to the previous round"""
        if self.current_round_index > 0:
            self.current_round_index -= 1
            self.animate_elimination_round()

    def show_final_results(self) -> None:
        """Show the final results with podium"""
        # Check if canvas exists before trying to use it
        if hasattr(self, 'results_canvas') and self.results_canvas.winfo_exists():
            self.results_canvas.delete("all")
        else:
            # If canvas doesn't exist, recreate it
            self.setup_animation_view()
        
        # Clear any existing navigation controls
        if self.nav_frame:
            self.nav_frame.destroy()
            self.nav_frame = None
        
        # Update round counter to show final results
        rounds = self.round_results.get('rounds', [])
        total_rounds = len(rounds) + 1  # Add 1 for the final results screen
        self.round_counter.config(text=f"Final Results ({total_rounds} of {total_rounds})")
        
        # Show podium or winner animation
        if self._has_podium_data():
            self.show_podium()
        else:
            self.show_winner_animation()
        
        # Only add the filename text if the canvas exists
        canvas_width, canvas_height = self._get_canvas_dimensions()
        if hasattr(self, 'results_canvas') and self.results_canvas.winfo_exists():
            self.results_canvas.create_text(
                canvas_width // 2, canvas_height - 60,
                text=f"Results saved to: {self.filename}",
                font=('Arial', 12),
                fill='gray'
            )
        
        # Recreate buttons
        self.detailed_button = Button(
            self.frame,
            text="Show Detailed Results",
            font=('Arial', 16),
            command=self.show_detailed_results
        )
        self.detailed_button.pack(pady=10)
        
        self.restart_button = Button(
            self.frame,
            text="Start New Vote",
            font=('Arial', 16),
            command=self.controller.restart
        )
        self.restart_button.pack(pady=10)

    def back_to_animation(self) -> None:
        """Return to the animation view from detailed results"""
        # Clear the frame completely and recreate the results view
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # Recreate the results view
        self.create_widgets(self.winner, self.round_results, self.filename, 
                           self.games, self.votes, self.voter_names)

    def show_detailed_results(self) -> None:
        """Show detailed voting results"""
        # Clear the frame completely
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # Create detailed results view
        container = Frame(self.frame)
        container.pack(fill=BOTH, expand=True)
        
        scrollbar = Scrollbar(container)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        canvas = Canvas(container, yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=canvas.yview)
        
        # Add mousewheel scrolling support
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        scroll_frame = Frame(canvas)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        # Add voting details
        Label(scroll_frame, text="Voting Details (Boys Night Points Voting)", 
              font=('Arial', 24, 'bold')).pack(pady=20)
        
        for i, (voter, vote) in enumerate(zip(self.voter_names, self.votes)):
            voter_frame = Frame(scroll_frame, relief=RAISED, bd=1)
            voter_frame.pack(fill='x', padx=10, pady=5)
            
            Label(voter_frame, text=f"{voter}'s Vote:", 
                  font=('Arial', 16, 'bold')).pack(anchor='w', padx=10, pady=5)
            
            for j, game_idx in enumerate(vote):
                if game_idx < len(self.games):
                    game_name = self.games[game_idx]
                    color = self.controller.get_color_palette()[game_idx % len(self.controller.get_color_palette())]
                    
                    game_frame = Frame(voter_frame, bg=color)
                    game_frame.pack(fill='x', padx=20, pady=2)
                    
                    Label(game_frame, text=f"{j+1}. {game_name}", font=('Arial', 14), 
                          bg=color, fg='white').pack(anchor='w', padx=10, pady=5)
        
        # Add round results
        Label(scroll_frame, text="Round Results", 
              font=('Arial', 24, 'bold')).pack(pady=20)
        
        rounds = self.round_results.get('rounds', [])
        for round_data in rounds:
            round_frame = Frame(scroll_frame, relief=RAISED, bd=1)
            round_frame.pack(fill='x', padx=10, pady=5)
            
            Label(round_frame, text=f"Round {round_data.get('round', 'N/A')}", 
                  font=('Arial', 16, 'bold')).pack(anchor='w', padx=10, pady=5)
            
            total_points = sum(round_data['game_totals'].values()) if 'game_totals' in round_data else 0
            Label(round_frame, text=f"Total Boys Night Points: {total_points:.1f}", 
                  font=('Arial', 14)).pack(anchor='w', padx=20, pady=2)
            
            if 'game_totals' in round_data:
                sorted_games = sorted(round_data['game_totals'].items(), key=lambda x: x[1], reverse=True)
                for game, score in sorted_games:
                    percentage = (score / total_points) * 100 if total_points > 0 else 0
                    Label(round_frame, 
                          text=f"{game}: {score:.1f} Boys Night points ({percentage:.1f}%)", 
                          font=('Arial', 12)).pack(anchor='w', padx=30, pady=1)
            
            eliminated = round_data.get('eliminated')
            if eliminated:
                Label(round_frame, text=f"Eliminated: {eliminated}", 
                      font=('Arial', 14), fg='red').pack(anchor='w', padx=20, pady=5)
        
        # Add final result
        final_frame = Frame(scroll_frame, relief=RAISED, bd=1)
        final_frame.pack(fill='x', padx=10, pady=10)
        
        if self.winner:
            Label(final_frame, text=f"WINNER: {self.winner}", 
                  font=('Arial', 20, 'bold'), fg='green').pack(pady=10)
        else:
            Label(final_frame, text="No winner determined", 
                  font=('Arial', 20, 'bold'), fg='red').pack(pady=10)
        
        scroll_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # Add back button
        back_button = Button(
            self.frame,
            text="Back to Animation",
            font=('Arial', 16),
            command=self.back_to_animation
        )
        back_button.pack(pady=10)

    def show_winner_animation(self) -> None:
        """Show winner animation"""
        canvas_width, canvas_height = self._get_canvas_dimensions()
        
        if self.winner and self.winner in self.games:
            winner_index = self.games.index(self.winner)
            color = self.controller.get_color_palette()[winner_index % len(self.controller.get_color_palette())]
            
            self.results_canvas.create_text(
                canvas_width // 2, canvas_height // 2 - 50,
                text="THE WINNER IS",
                font=('Arial', 28, 'bold'),
                fill='black'
            )
            
            self.results_canvas.create_text(
                canvas_width // 2, canvas_height // 2,
                text=self.winner,
                font=('Arial', 150, 'bold'),
                fill=color
            )
            
            # Show winner's points
            rounds = self.round_results.get('rounds', [])
            if rounds:
                final_round = rounds[-1]
                if 'game_totals' in final_round and self.winner in final_round['game_totals']:
                    score = final_round['game_totals'][self.winner]
                    total_points = sum(final_round['game_totals'].values())
                    percentage = (score / total_points) * 100 if total_points > 0 else 0
                    self.results_canvas.create_text(
                        canvas_width // 2, canvas_height // 2 + 50,
                        text=f"with {score:.1f} Boys Night points ({percentage:.1f}%)",
                        font=('Arial', 20),
                        fill='black'
                    )
        else:
            self.results_canvas.create_text(
                canvas_width // 2, canvas_height // 2,
                text="No winner could be determined",
                font=('Arial', 28, 'bold'),
                fill='red'
            )

    def show_podium(self) -> None:
        """Show podium with top 3 winners"""
        self.results_canvas.delete("all")
        
        # Get podium data from the correct location
        if 'podium' in self.round_results:
            podium = self.round_results['podium']
        else:
            rounds = self.round_results.get('rounds', [])
            podium = rounds[-1]['podium'] if rounds and 'podium' in rounds[-1] else []
        
        if len(podium) < 3:
            self.show_winner_animation()
            return
            
        canvas_width, canvas_height = self._get_canvas_dimensions()
        base_y = canvas_height - 100
        
        # First place
        first_x = canvas_width // 2
        first_height = 650
        self.results_canvas.create_rectangle(
            first_x - 80, base_y - first_height,
            first_x + 80, base_y,
            fill="gold", outline="black", width=2
        )
        self.results_canvas.create_text(
            first_x, base_y - first_height - 30,
            text=f"1st: {podium[0]['game']}",
            font=("Arial", 25, "bold"),
            fill="black"
        )
        self.results_canvas.create_text(
            first_x, base_y - first_height + 20,
            text=f"{podium[0]['score']:.1f} Boys Night points",
            font=("Arial", 25),
            fill="black"
        )
        
        # Second place
        second_x = canvas_width // 3
        second_height = 325
        self.results_canvas.create_rectangle(
            second_x - 80, base_y - second_height,
            second_x + 80, base_y,
            fill="silver", outline="black", width=2
        )
        self.results_canvas.create_text(
            second_x, base_y - second_height - 30,
            text=f"2nd: {podium[1]['game']}",
            font=("Arial", 25, "bold"),
            fill="black"
        )
        self.results_canvas.create_text(
            second_x, base_y - second_height + 20,
            text=f"{podium[1]['score']:.1f} Boys Night points",
            font=("Arial", 25),
            fill="black"
        )
        
        # Third place
        third_x = 2 * canvas_width // 3
        third_height = 163
        self.results_canvas.create_rectangle(
            third_x - 80, base_y - third_height,
            third_x + 80, base_y,
            fill="#CD7F32", outline="black", width=2
        )
        self.results_canvas.create_text(
            third_x, base_y - third_height - 30,
            text=f"3rd: {podium[2]['game']}",
            font=("Arial", 25, "bold"),
            fill="black"
        )
        self.results_canvas.create_text(
            third_x, base_y - third_height + 20,
            text=f"{podium[2]['score']:.1f} Boys Night points",
            font=("Arial", 25),
            fill="black"
        )
        
        # Winner text
        self.results_canvas.create_text(
            canvas_width // 2, 50,
            text=f"WINNER: {podium[0]['game']}",
            font=("Arial", 100, "bold"),
            fill="gold"
        )


# Controller Class
class GameVotingController:
    def __init__(self, root: Tk):
        self.root = root
        self.model = JaxVotingSystem()
        self.view: Optional[BaseView] = None
        self.current_phase = "suggestion"
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.width = int(screen_width * 0.8)
        self.height = int(screen_height * 0.8)
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        self.root.minsize(800, 600)
        
        self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Configure>', self.on_window_resize)
        
        self.show_suggestion_phase()
    
    def toggle_fullscreen(self) -> None:
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
    
    def on_window_resize(self, event: Any) -> None:
        if event.widget == self.root:
            self.width = event.width
            self.height = event.height
            
            if self.view and hasattr(self.view, 'on_resize'):
                self.view.on_resize()
    
    def get_scaled_font_size(self, base_size: int) -> int:
        return max(base_size, self.height // 40)
    
    def get_game_image(self, game_name: str) -> Optional[ImageTk.PhotoImage]:
        return self.model.game_images.get(game_name)
    
    def get_color_palette(self) -> List[str]:
        return self.model.color_palette
    
    def show_suggestion_phase(self) -> None:
        self.current_phase = "suggestion"
        if self.view:
            self.view.hide()
        
        self.view = SuggestionView(self.root, self)
        self.view.show()
        if isinstance(self.view, SuggestionView):
            self.view.update_game_list(self.model.games)
    
    def add_game(self, game_name: str) -> None:
        if self.model.add_game(game_name):
            self.model.create_game_icon(game_name)
            if isinstance(self.view, SuggestionView):
                self.view.update_game_list(self.model.games)
                self.view.clear_entry()
        elif len(self.model.games) >= 15:
            messagebox.showerror("Error", "Maximum 15 games allowed")
        else:
            messagebox.showerror("Error", "Game already exists or invalid name")
    
    def remove_game(self, game_name: str) -> None:
        if self.model.remove_game(game_name):
            if isinstance(self.view, SuggestionView):
                self.view.update_game_list(self.model.games)
    
    def start_voting_phase(self) -> None:
        if len(self.model.games) < 2:
            messagebox.showerror("Error", "You need at least 2 games to vote")
            return
        
        random.shuffle(self.model.voter_names)
        self.model.num_voters = len(self.model.voter_names)
        self.model.current_voter = 0
        self.model.ranked_games = [None] * len(self.model.games)
        
        self.model.original_game_order = self.model.games.copy()
        
        self.show_voting_phase()
    
    def show_voting_phase(self) -> None:
        self.current_phase = "voting"
        if self.view:
            self.view.hide()
        
        self.view = VotingView(self.root, self)
        voter_name = self.model.voter_names[self.model.current_voter]
        if isinstance(self.view, VotingView):
            self.view.create_widgets(voter_name, self.model.games)
        self.view.show()
    
    def return_game_to_pool(self, game_name: str, position: Tuple[int, int]) -> None:
        if isinstance(self.view, VotingView):
            self.view.restore_game_to_pool(game_name, position)
    
    def place_game_in_slot(self, game_name: str, slot_index: int, slot_widget: Any) -> None:
        self.model.ranked_games[slot_index] = game_name
        color = self.model.color_palette[self.model.games.index(game_name) % len(self.model.color_palette)]
        slot_widget.config(
            text=game_name,
            bg=color
        )
        slot_widget.game_name = game_name
    
    def submit_vote(self) -> None:
        if not isinstance(self.view, VotingView):
            return
            
        ranked_games = self.view.get_ranked_games()
        
        if None in ranked_games:
            messagebox.showerror("Error", "Please rank all games before submitting")
            return
        
        vote = [self.model.games.index(game) for game in ranked_games if game is not None]
        self.model.votes.append(vote)
        
        self.model.current_voter += 1
        
        if self.model.current_voter < self.model.num_voters:
            self.model.ranked_games = [None] * len(self.model.games)
            self.show_voting_phase()
        else:
            self.show_results()
    
    def show_results(self) -> None:
        self.current_phase = "results"
        self.winner, self.round_results = self.model.calculate_jax_method_voting()
        
        self.model.winner = self.winner
        self.model.round_results = self.round_results
        
        filename = self.model.save_results()
        
        if self.view:
            self.view.hide()
        
        self.view = ResultsView(self.root, self)
        self.view.create_widgets(self.winner, self.round_results, filename, 
                               self.model.games, self.model.votes, self.model.voter_names)
        self.view.show()

    def save_results(self) -> None:
        filename = self.model.save_results()
        if filename:
            messagebox.showinfo("Results Saved", f"Results saved to:\n{filename}")
    
    def restart(self) -> None:
        self.model = JaxVotingSystem()
        self.show_suggestion_phase()


if __name__ == "__main__":
    root = Tk()
    app = GameVotingController(root)
    root.mainloop()
