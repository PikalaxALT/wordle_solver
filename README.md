# Automatic Wordle solver

Inspired by the popular word game and subsequent video by [3Blue1Brown](https://github.com/3blue1brown). This version uses the relative frequencies of all five-letter words accepted by Wordle in computing the information content of each guess. This dictionary was unapologetically copied from 3Blue1Brown's public repository.

## Requirements:

You should have Python version 3.9 or newer. Then, install the packages listed in `requirements.txt`.

## To run:

`python main.py [--auto [SOLUTION]]`

This script has three run modes: Manual, Auto-Random, and Auto-Given

### Manual mode
In each round, the program will give you its guess. Your job is to give it feedback on how well that guess matches the solution, using an easy-to-type format mimicking the Wordle response. Instead of feeding it the colors of the squares (black, yellow, green), the script expects a 5-digit strings of 0, 1, and 2, assigning a numeric value to the respective color. For instance, if the game guesses `CHILD` and the answer is `THEIR`, your response should be `02100` indicating that
- there is no 'C', 'L', or 'D' in the solution,
- there is an 'H' in the second positon, and
- there is an 'I' in the solution but it is not in the third position.

To run this mode, run the script with no arguments.

### Auto-Random mode
In this version, the program will randomly choose a solution, then play the game using the maximum-information guess in each round to try and guess this solution.

To run this mode, run the script with the `--auto` flag.

### Auto-Given mode

This version is the same as Auto-Random mode except this time you provide the solution yourself.

To run this mode, pass the `--auto` flag followed by a 5-letter word. The word MUST be in the game's wordbank or else it will never be guessed.
