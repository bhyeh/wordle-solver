from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

import numpy as np
from numpy import random
from time import sleep

from bot import Bot

class RandomBot(Bot):

    """
    A bot that makes random guessed-attempts

    Method
    ------
    play_worlde(self)
        Opens web browser, navigates to NYT Wordle site, and proceeds to make 
        six random guessed-attempts.

    """

    def make_random_guess(self):
        """
        Generates random guess from list of valid guesses

        """

        guess_idx = random.randint(low = 0, high = len(self.state))
        guess = self.state[guess_idx]
        self.actions.send_keys(guess)
        self.actions.send_keys(Keys.RETURN)
        self.actions.perform()

    def evaluate_guess(self, idx):
        """
        Evaluates the quality of guess at time step `idx` through simple scoring metric

        Scoring system:
            (1) Each letter of an attempt can take on three values: 'correct', 'present', 'absent'
                --> 'correct' : letter is in answer and at correct position
                --> 'present' : letter is in answer but at incorrect position
                --> 'absent'  : letter is not in answer
            (2) Assign each label an integer value
                --> 'correct' : 2
                --> 'present' : 1
                --> 'absent'  : 0
            (3) Score an attempt by evaluating each letter, multiply by coresponding label-integer, sum and 
                divide by 10. 
                --> Maximum score is 1.0 (all letters correct)
                --> Minimum score is 0.0 (no letters in answer)

        Parameters
        ----------
        idx : int
            integer indicating attempt number

        Returns
        -------
        correctness : float
            ratio describing quality of attempt
        
        """

        # Interpret gameboard
        game_app = self.driver.find_element(By.TAG_NAME , 'game-app')
        game_rows = self.driver.execute_script("return arguments[0].shadowRoot.getElementById('board')", game_app).find_elements(By.TAG_NAME, 'game-row')
        letters = self.driver.execute_script('return arguments[0].shadowRoot', game_rows[idx]).find_elements(By.CSS_SELECTOR , 'game-tile')

        # Quantize evaluation 
        eval_to_int = {
            'correct' : 2,
            'present' : 1,
            'absent'  : 0
        }

        # Evaluate guess
        correctness = 0
        for letter in letters:
            correctness += eval_to_int[letter.get_attribute('evaluation')]
        correctness /= 10
        print('Correctness: {:.2f}'.format(correctness))

    def play_wordle(self):
        """
        Plays game of Wordle

        """

        # Open Wordle site
        self.open_wordle()

        # Make guesses
        for i in np.arange(6):
            self.make_random_guess()
            self.evaluate_guess(i)
            sleep(2.5)

        # Quit
        sleep(3)
        self.driver.quit()