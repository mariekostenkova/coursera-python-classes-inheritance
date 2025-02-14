import json
import random
import time
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(message)s')

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
VOWELS = 'AEIOU'
VOWEL_COST = 250


class WheelResult(Enum):
    BANKRUPT = 'bankrupt'
    LOSE_TURN = 'loseturn'
    CASH = 'cash'


class WheelSegment:
    def __init__(self, text, type, value=0, prize=''):
        self.text = text
        self.type = WheelResult(type)
        self.value = value
        self.prize = prize


class Player:
    def __init__(self, name):
        self.name = name
        self.prize_money = 0
        self.prizes = set()

    def add_money(self, amt):
        self.prize_money += amt

    def go_bankrupt(self):
        self.prize_money = 0

    def add_prize(self, prize):
        self.prizes.add(prize)

    def __str__(self):
        return f'{self.name} ({self.prize_money} Kč)'


class HumanPlayer(Player):
    def get_move(self, category, obscured_phrase, guessed):
        print(f'\n{self.name}, máte {self.prize_money} Kč')
        print(show_board(category, obscured_phrase, guessed))
        return input('Hádej písmeno, frázi nebo napiš "exit" nebo "pass": ').upper()


class ComputerPlayer(Player):
    SORTED_FREQUENCIES = 'ZQXJKVBPYGFWMUCLDRHSNIOATE'

    def __init__(self, name, difficulty):
        super().__init__(name)
        self.difficulty = difficulty

    def smart_coin_flip(self):
        return random.randint(1, 10) > self.difficulty

    def get_possible_letters(self, guessed):
        return [l for l in LETTERS if l not in guessed and (l not in VOWELS or self.prize_money >= VOWEL_COST)]

    def get_move(self, category, obscured_phrase, guessed):
        letters_to_guess = self.get_possible_letters(guessed)
        if not letters_to_guess:
            return 'PASS'
        return sorted(letters_to_guess, key=lambda x: self.SORTED_FREQUENCIES.index(x))[
            -1] if self.smart_coin_flip() else random.choice(letters_to_guess)


# Game Functions
def get_number_between(prompt, min_val, max_val):
    while True:
        try:
            n = int(input(prompt))
            if min_val <= n <= max_val:
                return n
            print(f'Musí být mezi {min_val} a {max_val}')
        except ValueError:
            print('Neplatný vstup! Musí to být číslo.')


def load_wheel():
    try:
        with open('wheel.json', 'r') as f:
            return [WheelSegment(**segment) for segment in json.load(f)]
    except FileNotFoundError:
        print('Chyba: Soubor "wheel.json" nebyl nalezen.')
        raise
    except json.JSONDecodeError:
        print('Chyba: Soubor "wheel.json" obsahuje neplatná data.')
        raise


def spin_wheel(wheel):
    return random.choice(wheel)


def load_phrases():
    try:
        with open('phrases.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print('Chyba: Soubor "phrases.json" nebyl nalezen.')
        raise
    except json.JSONDecodeError:
        print('Chyba: Soubor "phrases.json" obsahuje neplatná data.')
        raise


def get_random_category_and_phrase(phrases):
    category = random.choice(list(phrases.keys()))
    return category, random.choice(phrases[category]).upper()


def obscure_phrase(phrase, guessed):
    return ''.join('_' if c in LETTERS and c not in guessed else c for c in phrase)


def show_board(category, obscured_phrase, guessed):
    return f'\nKategorie: {category}\nFráze:   {obscured_phrase}\nHádaná písmena: {", ".join(sorted(guessed))}'


def request_player_move(player, category, guessed, phrase):
    while True:
        move = player.get_move(category, obscure_phrase(phrase, guessed), guessed)
        if move in {'EXIT', 'PASS'} or (len(move) == 1 and move in LETTERS and move not in guessed and (
                move not in VOWELS or player.prize_money >= VOWEL_COST)):
            return move
        print('Neplatný tah!')


def main():
    try:
        print('=' * 15)
        print('KOLO ŠTĚSTÍ')
        print('=' * 15)
        print('')

        num_human = get_number_between('Kolik lidských hráčů?\n', 0, 10)
        human_players = [HumanPlayer(input(f'Jméno hráče #{i + 1}: ')) for i in range(num_human)]
        num_computer = get_number_between('Kolik počítačových hráčů?\n', 0, 10)
        difficulty = get_number_between('Jaká obtížnost (1-10, 1 = nejtěžší)?\n', 1, 10) if num_computer >= 1 else None
        computer_players = [ComputerPlayer(f'Počítač {i + 1}', difficulty) for i in range(num_computer)]

        players = human_players + computer_players
        if not players:
            raise ValueError('Potřebujeme hráče!')

        phrases = load_phrases()
        category, phrase = get_random_category_and_phrase(phrases)
        guessed = set()
        player_index = 0
        winner = None
        wheel = load_wheel()

        while not winner:
            player = players[player_index]
            wheel_result = spin_wheel(wheel)

            print(f'\n{player.name} ({player.prize_money} Kč) točí...')
            time.sleep(2)
            print(wheel_result.text)
            time.sleep(1)

            if wheel_result.type == WheelResult.BANKRUPT:
                player.go_bankrupt()
            elif wheel_result.type == WheelResult.LOSE_TURN:
                pass
            else:
                move = request_player_move(player, category, guessed, phrase)
                if move == 'EXIT':
                    print('Na shledanou!')
                    return
                elif move == 'PASS':
                    print(f'{player.name} vynechává.')
                elif len(move) == 1:
                    guessed.add(move)
                    if obscure_phrase(phrase, guessed) == phrase:
                        winner = player
                        break
                elif move == phrase:
                    winner = player
                    break
            player_index = (player_index + 1) % len(players)

        print(f'{winner.name} vítězí! Fráze byla: {phrase}')

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error('Došlo k chybě při načítání souborů. Program končí.')
    except ValueError as e:
        logging.error(str(e))
    except Exception as e:
        logging.error(f'Došlo k neočekávané chybě: {str(e)}')


if __name__ == '__main__':
    main()
