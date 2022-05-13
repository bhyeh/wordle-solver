# Import packages performing actions on Website
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
# Import aux libraries
import pickle
import numpy as np
from numpy import random
from time import sleep
from wordfreq import zipf_frequency
# Parent class
from Bot import Bot

class ZipfBot(Bot):

    """A bot that makes attempts based on current word state and greedily chooses
    the word with the highest zipf frequency.

    Methods
    -------
    play_wordle()
        \\TODO: Write docstrings. 
    
    """

    def __init__(self, compute = False, save = False):
        """\\TODO: Write constructor docstrings
        
        """
        super(ZipfBot, self).__init__()

        if compute:
            self.zipf_dict = self.__create_zipf_dict()
            # \\TODO: Write branch to save file
        else:
            with open('zipf_dict.pkl', 'rb') as dict:
                self.zipf_dict = pickle.load(dict)

    def __create_zipf_dict(self):
        """\\TODO: Write docstrings

        Parameters
        ----------
        None

        Returns
        -------
        zipf_dict : dict
        
        """

        # Anon aux function to calculate zipf frequency of an array element
        zipf = lambda x : zipf_frequency(x, 'eng')
        # Compute zipf frequencies of all words in word state
        zipf_words = [*map(zipf, self.word_state)]
        # Create zipf dictionary with key: word, value : zipf frequency
        zipf_dict = dict(zip(self.word_state, zipf_words))
        return zipf_dict

    def __make_random_guess(self):
        """Generates random guess from current word state and plays guess.

        In ZipfBot class, start game by random guess from word state. 

        """

        # Generate random guess
        guess_idx = random.randint(low = 0, high = len(self.word_state))
        guess = self.word_state[guess_idx]
        # Play guess on gameboard
        self.actions.send_keys(guess)
        self.actions.send_keys(Keys.RETURN)
        self.actions.perform()

    def __make_guess(self):
        """Generates a greedy guess from current word state and considering 
        highest zipf frequency. 
        
        """

        # Determine word with highest zipf frequency at current word state
        guess = max(self.zipf_dict.items(), key=lambda x: x[1])[0]
        print(self.zipf_dict[guess])
        # Play guess on gameboard
        self.actions.send_keys(guess)
        self.actions.send_keys(Keys.RETURN)
        self.actions.perform()

    def __update_word_state(self, game_tiles):
        """Updates word and zipf state based on most recent attempt.
        
        Parses current game state through `game_tiles` and reduces search space 
        based on the tile evaluation results. Further updates `zipf_dict`. 

        Parameters
        ----------
        game_tiles : list
            List of 'tile' elements from gameboard.

        Returns
        -------
        None
        
        """

        # Print current state size
        print('Current word state size: {}'.format(self.word_state.size))
        # Initialize lists for correct, present, absent
        #   -> Elements of each are sublists
        correct = []
        present = []
        absent = []
        # First pass; append CORRECT and PRESENT letters;
        #   -> This helps with resolving issues of REPEAT letters
        # Intialize running list to track PRESENT and CORRECT letters;
        correct_present = []
        for tile in game_tiles:
            letter = tile.get_attribute('letter')
            eval = tile.get_attribute('evaluation')
            if (eval == 'correct') or (eval == 'present'):
                correct_present.append(letter)
        # Second pass; update search space
        for i, tile in enumerate(game_tiles):
            letter = tile.get_attribute('letter')
            eval = tile.get_attribute('evaluation')
            # Letter is present and at exact position in answer
            if eval == 'correct':
                # Add words to new state with letter at POSITION `i` in word;
                #   -> This requires later filtering; 
                #      E.g: multiple correct letters at multiple positions
                #         ('t' @ idx 0) : ['train', 'tank', ... ] 
                #         ('r' @ idx 1) : ['train', 'brain', ... ]
                #   -> correct : ['train']
                #   -> needs to satsify all 'CORRECT' tags
                correct.append([word for word in self.word_state if word[i] == letter])
            # Letter is present in answer
            elif eval == 'present':
                # Add words to new state WITH LETTER in word
                #   -> This requires further filtering; 
                #      E.g: multiple present letters
                #         ('a') : ['apple', 'tank', 'alone' ] 
                #         ('e') : ['apple', 'prey', 'alone ]
                #   -> present : ['apple', 'alone']
                #   -> needs to satsify all 'PRESENT' tags
                present.append([word for word in self.word_state if letter in word])
            # Letter is not present in answer
            else:
                # Add words to new state WITHOUT LETTER in word
                #   -> Note: only the first PRESENT letter is marked; the second is marked ABSENT
                #   -> Resolve: maintain list of PRESENT letters; add condition 
                #   -> Issue : if repeat letter is before a CORRECT letter; it is marked ABSENT
                #   -> Resolve: maintain list of CORRECT letters
                # Add iff letter is correct/present already (REPEAT case handling)
                if letter not in correct_present:
                    absent.append([word for word in self.word_state if letter not in word ])
        # Filter lists; each list is sublist satsifying different letter properties
        #   -> For each list, we intersect and find common between each sublist
        #   -> Note: Can not use set.intersection() method on empty list
        #   -> Note: It is possible that set.intersection() itself returns an empty list
        sets = [correct, present, absent]
        for i in np.arange(len(sets)):
            subset = sets[i]
            # Perform intersection method if list is non empty
            if subset:
                # Find intersection of sub list 
                sets[i] = list(set.intersection(*map(set, subset)))
        correct, present, absent = tuple(sets)
        # New word state is the INTERSECTION of three lists: (correct ∩ present ∩ absent)
        #   -> Note: if either sets - correct, present, or absent are EMPTY;
        #            the intersection including an EMPTY list is also EMPTY
        #   -> Resolve: check for non-emptiness again and intersect on non-empty subsets
        sets = [subset for subset in [correct, present, absent] if subset]
        new_state = np.array(list(set.intersection(*map(set, sets))))
        self.word_state = new_state
        print('New word state size: {}'.format(new_state.size))
        print('-'*80)
        # Update state of `zipf_dict`
        self.zipf_dict = {word:zipf for word, zipf in self.zipf_dict.items() if word in self.word_state}

    def __rank_word_state(self):
        """\\TODO: Write docstrings.
        
        """

        pass

    # Naïve approach — simply count in how many words does each letter appear, 
    # and choose the word with the aggregate 
    # highest number on its five letters. 
    #   -> For each correct/present letter guessed; choose the next word 
    #      with the highest number of each correct/present letter in it

    def play_wordle(self):
        """Plays game of Wordle.

        Sequence of actions:
            (1) Open Wordle
            (2) Begin playing; while game is ON / attempts left
                -> Make random guess and play it
                -> Retrieve game state
                -> Update game state
                -> Update word state
                -> Repeat

        """

        # Open Wordle site
        self.open_wordle()
        # Play Wordle; 
        #   -> Start game with a random guess
        self.__make_random_guess()
        game_tiles = self.get_game_tiles(0)
        # Update game state
        self.update_game_state(game_tiles)
        # Update word state
        self.__update_word_state(game_tiles)
        # Sleepy
        sleep(2.5)
        # Continue playing; until solved or attempts are exhausted
        idx = 1
        while (self.game_state) and (idx != 6):
            self.__make_guess()
            # Get game state
            game_tiles = self.get_game_tiles(idx)
            # Update game state
            self.update_game_state(game_tiles)
            if not self.game_state:
                break
            else:
                # Update word state
                self.__update_word_state(game_tiles)
                # Update idx
                idx += 1
                # Sleepy
                sleep(2.5)
        # Click anywhere to minimize outro tab;
        self.actions = ActionChains(self.driver)
        self.actions.click()
        self.actions.perform()
        # Close Web Driver after 15 seconds;
        sleep(15)