import collections
import json
import operator
import random
import argparse
import typing
import scipy.special as sc

import numpy as np
import itertools


class Wordler:
    """Creates a game of Wordler"""
    RESP_BK = 0
    RESP_YL = 1
    RESP_GN = 2

    H_OFFSET = 4660
    H_SCALE = 2500

    _emojis = ['⬛', '🟨', '🟩']

    responses: list[str]
    guesses: list[str]
    bank: dict[str, list[float, bool]]

    def __init__(self):
        self.responses = []
        self.guesses = []
        with open('freq_map.json') as fp:
            self.bank = {
                word: [sc.expit((Wordler.H_OFFSET - i) / Wordler.H_SCALE), True]
                for i, (word, freq)
                in enumerate(sorted(json.load(fp)['words'].items(), key=operator.itemgetter(1)))
            }

    def reset(self):
        self.responses = []
        self.guesses = []
        for word in self.bank:
            self.bank[word][1] = True

    def record_response(self, guess: str, response: typing.Union[list, str], human=False):
        """Record the last guess and the game's response."""
        assert len(guess) == 5
        assert len(response) == 5
        self.guesses.append(guess.casefold())
        if all(isinstance(x, str) for x in response):
            assert all(x in Wordler._emojis for x in response)
        elif all(isinstance(x, int) for x in response):
            assert all(0 <= x <= 2 for x in response)
            response = ''.join(Wordler._emojis[x] for x in response)
        else:
            raise ValueError('invalid response')

        self.responses.append(response)
        for word in self.bank:
            if Wordler.calc_response(guess, word) != response:
                self.bank[word][0] = 0.0
    
    def entropy(self, guess: str):
        """Calculate the entropy of the guess."""
        addend = 1 / sum(1 for word, (freq, flag) in self.bank.items() if freq != 0)
        check = collections.defaultdict(float)
        for word, (freq, flag) in self.bank.items():
            if freq != 0:
                check[self.calc_response(guess, word)] += addend * freq
        return sum(-x * np.log2(x) for x in check.values())

    @staticmethod
    def prompt_response(guess: str):
        """If the solution is chosen externally, ask the player for the app's response."""
        while True:
            data = input(f'{guess.upper()} >').casefold()
            if len(data) != 5:
                print('err: invalid length')
            elif not data.isnumeric():
                if data == 'xxxxx':
                    print('Gotcha, I am removing this word from my bank.')
                    return None
                print('err: not numeric')
            elif not all(c in '012' for c in data):
                print('err: only 0-2 accepted')
            else:
                return ''.join(Wordler._emojis[int(c)] for c in data)

    @staticmethod
    def calc_response(guess: str, solution: str):
        """Calculate what the game's response would be.
        This is a core routine used to calculate guess entropy and filter the word bank."""
        response = [Wordler._emojis[Wordler.RESP_BK] for _ in range(5)]
        for i, (c, d) in enumerate(zip(guess, solution)):
            if c == d:
                response[i] = Wordler._emojis[Wordler.RESP_GN]
            elif c in solution:
                count = sum(1 for d in solution if d == c)
                index = sum(1 for d in guess[:i] if d == c)
                if index < count:
                    response[i] = Wordler._emojis[Wordler.RESP_YL]
        return ''.join(response)

    @staticmethod
    def get_response(guess, solution: str = None):
        """Calculates or prompts the game's response"""
        if solution is None:
            return Wordler.prompt_response(guess)
        else:
            return Wordler.calc_response(guess, solution)

    def prompt_guess(self, turn: int):
        while True:
            guess = input(f'Round {turn} > ').casefold()
            if guess in self.bank:
                return guess, self.entropy(guess)
            print(f'Invalid word: {guess}')

    def make_guess(self, turn: int, human=False):
        if human:
            return self.prompt_guess(turn)
        if turn == 1:
            return 'tares', self.entropy('tares')
        entropies: list[tuple[str, float]] = [(word, self.entropy(word)) for word, (freq, flag) in self.bank.items() if freq != 0]
        entropies.sort(reverse=True, key=operator.itemgetter(1))
        if len(entropies) > 1 and entropies[1][1] == entropies[0][1]:
            choices = list(itertools.takewhile(lambda x: x[1] == entropies[0][1], entropies))
            return random.choice(choices)
        else:
            return entropies[0]

    def play(self, secret: str = None, human=False):
        """Play the game.
        If secret is None, the solution is chosen externally.
        Otherwise, autoplay with the given solution."""
        if secret is None:
            print("This is the wordler solver.\n\n"
                  "On each round, I will suggest a word to use.\n"
                  "Enter this word into the game, and tell me what\n"
                  "the game responds with.\n\n"
                  "Your response should be a 5-digit number according to\n"
                  "the following key:\n\n"
                  "0 = black (letter is not in solution)\n"
                  "1 = yellow (letter in the wrong place)\n"
                  "2 = green (letter in the correct place)\n\n"
                  "If the word I suggest is not in the app's wordbank,\n"
                  "say \"xxxxx\".")
        elif human:
            print('This is a wordle clone.\n\n'
                  'On each round, you will guess a 5-letter word.\n'
                  'I will tell you how close you are to the solution using the following hints:\n\n'
                  '⬛ - The letter is not in the solution\n'
                  '🟨 - The letter is in the solution but not in that position\n'
                  '🟩 - The letter is in the solution at that position')
        for i in range(1, 7):
            # The initial guess of 'tares' was chosen by playing one round of this game with no prior information.
            # Since the entropy calculation is O(n^2), we only want to do this opening move calculation once.
            while True:
                guess, entropy = self.make_guess(i, human=human)
                response = Wordler.get_response(guess, secret)
                self.bank[guess][1] = False
                if response is not None:
                    break
                assert i != 1, 'The initial guess is a guaranteed word. You are pulling my leg here.'
            print(f'Round {i}: {guess} - H = {entropy: 3.4f} -- {response}')
            if response == ''.join(Wordler._emojis[Wordler.RESP_GN] for _ in range(5)):
                # We won the game, tell the user and exit
                suffix = 'tsnrhtdd'[((i // 10) % 10 != 1) * (i % 10 < 4) * (i % 10)::4]
                print(f'Got it on the {i}{suffix} try!')
                break
            self.record_response(guess, response, human=human)
            if not self.bank:
                raise ValueError('ruled out all possibilities somehow (secret = {})'.format(secret))
        else:
            if secret is not None:
                print(f'Did not get the word ({secret})')
            else:
                print('Wait what was the word? So frustrating...')


class Namespace(argparse.Namespace):
    auto: typing.Union[bool, str, None]
    human: bool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', nargs='?', const=False,
                        help='The game runs itself against a given solution. '
                             'If no solution is given, one is chosen at random from the word bank.')
    parser.add_argument('--human', action='store_true',
                        help='You the user are playing the game. This cannot be used in tandem with --auto.')
    args = parser.parse_args(namespace=Namespace())
    game = Wordler()
    secret: typing.Optional[str]
    if args.auto is None and not args.human:
        secret = None
    elif args.auto:
        assert args.auto in game.bank, 'I don\'t know that word!'
        assert not args.human, 'Can\'t have a solution with --human'
        secret = args.auto
    else:
        secret = random.choice(list(game.bank))
    game.play(secret, human=args.human)


if __name__ == '__main__':
    main()
