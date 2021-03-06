#!/usr/bin/env python3

import time
import curses
import settings
from deck import Deck

class Game:

    def __init__(self):
        """
        __init__(): show the rules and initialize the game settings
        """
        # Show the logo during setup
        settings.mainscreen.bkgd(' ', curses.color_pair(1))
        settings.scoreboard.addstr(0, 0, settings.buildLogo())
        settings.scoreboard.refresh()

        # Show the instuctions
        settings.mainscreen.addstr(1, 2, '🏌  The objective is to get the lowest score over all rounds.')
        settings.mainscreen.addstr(3, 2, '🏌  Each player starts each round with 6 face-down cards, and flips over 2')
        settings.mainscreen.addstr(4, 2, '   during their first turn.')
        settings.mainscreen.addstr(6, 2, '🏌  During each turn, players draw a card from the discard or stock stack. This card ')
        settings.mainscreen.addstr(7, 2, '   can either be swapped with one of the six from the player’s hand or discarded.')
        settings.mainscreen.addstr(9, 2, '🏌  The round ends when one player’s cards are all face up.')
        settings.mainscreen.addstr(11, 2, '🏌  The game ends when all rounds are over or [ctrl-c] is pressed')
        settings.mainscreen.addstr(13, 2, '┌───────┬────────┬───────────────────┬────────────┬───────┐')
        settings.mainscreen.addstr(14, 2, '│ A = 1 │ 2 = -2 │ 3-10 = Face Value │ Q & J = 10 │ K = 0 │')
        settings.mainscreen.addstr(15, 2, '└───────┴────────┴───────────────────┴────────────┴───────┘')
        settings.mainscreen.addstr(17, 31, '[ Press any key to begin ]', curses.color_pair(4))
        start = settings.mainscreen.getch() # Wait for feedback

        # Initialize number of players
        settings.mainscreen.clear()
        self.numPlayers = -1
        while(self.numPlayers < 2 or self.numPlayers > 4):
            settings.mainscreen.addstr(2, 2, "How many people are playing? [2-4]: ")
            self.numPlayers = settings.mainscreen.getch() - 48
            if(self.numPlayers < 2 or self.numPlayers > 4):
                settings.mainscreen.addstr(3 , 2, "Please enter a number between 2 and 4")

        # Initialize number of rounds
        self.numRounds = -1
        settings.mainscreen.clear()
        while(self.numRounds < 1 or self.numRounds > 9):
            settings.mainscreen.addstr(2, 2, "How many rounds would you like to play? [1-9]: ")
            self.numRounds = settings.mainscreen.getch() - 48
            if(self.numRounds < 1 or self.numRounds > 9):
                settings.mainscreen.addstr(3 , 2, "Please enter a number between 1 and 9")

        curses.curs_set(0); # Hide the cursor

        # Start game from scratch
        self.scores = [0] * self.numPlayers
        self.prevScores = [0] * self.numPlayers
        self.curPlayer = 1
        self.curRound = 0
        self.curTurn = 0
        self.roundFinished = False

        # Prepare the screen for gameplay
        settings.mainscreen.clear()
        # Hide the logo if the terminal is not wide enough to fit it
        if(curses.COLS < 100): settings.scoreboard.clear()

    def buildScoreboard(self):
        """
        buildScoreboard(): Updates the scoreboard on the left of scoreboard screen
        """
        scoreboardText = []
        line = 0

        # Upper Border
        settings.scoreboard.addstr(line, 0, ' ┌────────' + ('┬─────' * self.numPlayers) + '┐')
        line += 1

        # Middle Rows
        for i in range(2):
            # Row label
            row = ' │ ' + ('Player │ ' if i == 0 else ' Score │ ')
            # Row content
            for j in range(self.numPlayers):
                row += '{:^3d}'.format((j+1) if i == 0 else self.scores[j]) + ' │ '
            # Display row
            settings.scoreboard.addstr(line, 0, row)
            line += 1
            # Middle Border
            settings.scoreboard.addstr(line, 0, ' ├────────' + ('┼─────' * self.numPlayers) + '┤')
            line += 1

        # Bottom Border
        settings.scoreboard.addstr(line-1, 0, ' └────────' + ('┴─────' * self.numPlayers) + '┘')

        # Show the scoreboard
        settings.scoreboard.refresh()

    def buildRoundStatus(self):
            """
            buildRoundStatus(): Updates the counter on the right of scoreboard screen
            """
            roundIndicator = [('_', '🏌️‍')[round == self.curRound] for round in range(1, self.numRounds+1)]
            roundStatus = '│ Round ' + str(self.curRound) + ': ' + ' '.join(roundIndicator) + ' │'
            playerStatus = ' P' + str(self.curPlayer) + '\'s turn!'
            boxWidth = len(roundStatus)
            x = curses.COLS - boxWidth - 1

            settings.scoreboard.addstr(0, x, '┌' + ('─' * (boxWidth - 3)) + '┐')
            settings.scoreboard.addstr(1, x, roundStatus)
            settings.scoreboard.addstr(2, x, '│' + (' ' * (boxWidth - 3)) + '│')
            settings.scoreboard.addstr(3, x, '│' + playerStatus + (' ' * (boxWidth - 14)) + '│')
            settings.scoreboard.addstr(4, x, '└' + ('─' * (boxWidth - 3)) + '┘')
            settings.scoreboard.refresh()

    def showHand(self):
        """
        showHand(): display the current players hand, as well as discard and draw piles
        """
        # Show the deck and discard pile
        if(len(self.deck.cards) > 0): settings.displayCard(1, 48, self.deck.cards[-1], "[7] Draw")
        if(len(self.discard.cards) > 0): settings.displayCard(1, 62, self.discard.cards[-1], "[8] Discard")

        # Print the Player's Hand
        i = 0
        for row in range(2):
            for col in range(3):
                settings.displayCard((row*9)+1, (col*14)+1, self.hands[self.curPlayer-1].cards[i], '['+str(i+1)+']')
                i += 1

    def calculateScores(self):
        """
        calculateScores(): updated the self.scores for the current player
        """
        # For the current  player
        playerHand = self.hands[self.curPlayer-1]

        # The current tally for this round, which will change every turn.
        # Therefore it is not cemented until the end of the round
        curScore = 0

        # Matching columns count as 0 points
        for col in range(3):
            topCard = playerHand.cards[col]
            bottomCard = playerHand.cards[col+3]

            if((topCard.faceUp and bottomCard.faceUp) and (topCard.value == bottomCard.value)):
                continue
            else:
                for card in [topCard, bottomCard]:
                    if(card.faceUp):
                        if(card.value == 2):
                            curScore -= 2
                        elif(card.value == 11 or card.value == 12):
                            curScore += 10
                        elif(card.value != 13):
                            curScore += card.value

        # Update current total score, including previous rounds
        self.scores[self.curPlayer-1] = curScore + self.prevScores[self.curPlayer-1]

        self.buildScoreboard()

    def takeTurn(self):
        """
        TakeTurn(): One player takes a turn in a round

        There are three turn behaviors: first turn, normal turn, and last turn
        """
        # Update the Screen
        settings.mainscreen.clear()
        self.buildRoundStatus()
        self.showHand()

        # Print the current player
        settings.mainscreen.addstr(11, 48, 'Player ' + str(self.curPlayer) + ':', curses.color_pair(2))

        # Check if this is the player's first turn
        if(self.curTurn < self.numPlayers):
            settings.mainscreen.addstr(12, 48, 'This is your first turn!', curses.color_pair(2))
            settings.mainscreen.addstr(14, 48, 'Choose two cards [1-6]', curses.color_pair(2))
            settings.mainscreen.addstr(15, 48, 'to flip over.', curses.color_pair(2))
            settings.mainscreen.refresh()
            # Let the player decide which 2 cards to flip
            for i in range(2):
                move = -1
                validInput = False
                while not validInput:
                    move = settings.mainscreen.getch() - 48
                    curses.flushinp()
                    if(move < 1 or move > 6):
                        settings.mainscreen.addstr(17, 48, 'Press [1-6]', curses.color_pair(4))
                    else:
                        if not(self.hands[self.curPlayer-1].cards[move-1].faceUp):
                            self.hands[self.curPlayer-1].cards[move-1].flipUp()
                            validInput = True
                self.showHand()
        # Take a normal turn
        else:
            settings.mainscreen.addstr(13, 48, 'Draw from pile', curses.color_pair(2))
            settings.mainscreen.addstr(14, 48, '[7] or [8]', curses.color_pair(2))
            # Warn the player if it is their last turn
            if(self.roundFinished):
                settings.mainscreen.addstr(16, 48, 'You have one last turn', curses.color_pair(4))
                settings.mainscreen.addstr(17, 48, 'before your cards are flipped!', curses.color_pair(4))
            settings.mainscreen.refresh()

            # Let the player decide where to draw from
            drawFrom = None
            validInput = False
            while not validInput:
                drawFrom = settings.mainscreen.getch() - 48
                curses.flushinp()
                if(drawFrom == 7):
                     # Draw top card of draw pile
                    self.deck.cards[-1].flipUp()
                    self.showHand()
                    settings.mainscreen.addstr(9, 48, '[7]', curses.color_pair(4))
                    validInput = True
                elif(drawFrom == 8):
                    # Draw top card of discard pile
                    settings.mainscreen.addstr(9, 62, '[8]', curses.color_pair(4))
                    validInput = True
                else:
                    # Invalid Input
                    settings.mainscreen.addstr(17, 48, 'Press [7] or [8]', curses.color_pair(4))

            # Let the player decide where to place the drawn card
            settings.mainscreen.addstr(11, 48, 'Player ' + str(self.curPlayer) + ':', curses.color_pair(2))
            settings.mainscreen.addstr(13, 48, 'Swap with a card [1-6]', curses.color_pair(2))
            settings.mainscreen.addstr(14, 48, 'or choose discard [8]', curses.color_pair(2))
            putCard = None
            validInput = False
            while not validInput:
                putCard = settings.mainscreen.getch() - 48
                curses.flushinp()
                if(putCard == 8):
                    # Put the card in the discard pile
                    if(drawFrom == 7):
                        # Move from Drawn to Discard
                        drawnCard = self.deck.cards.pop()
                        self.discard.addCard(drawnCard)
                    # Otherwise leave in discard
                    validInput = True
                elif(putCard >= 1 and putCard <= 6):
                    # Swap with card [putCard-1]
                    toDiscard = self.hands[self.curPlayer-1].cards.pop(putCard-1)
                    toDiscard.flipUp()
                    if(drawFrom == 7):
                        # Draw top card of draw pile
                        drawnCard = self.deck.cards.pop()
                    else:
                        # Draw top card of discard
                        drawnCard = self.discard.cards.pop()
                    # Perform the swap
                    self.hands[self.curPlayer-1].cards.insert(putCard-1, drawnCard)
                    self.discard.addCard(toDiscard)
                    validInput = True
                else:
                    # Invalid Input
                    settings.mainscreen.addstr(17, 48, 'Invalid input', curses.color_pair(4))

            if(self.roundFinished):
                # Flip up remaining cards if round is finished
                for card in self.hands[self.curPlayer-1].cards:
                    if not(card.faceUp): card.flipUp()

        # Calculate scores
        self.showHand()
        self.calculateScores()

        # Give players a chance to see their hand on the last round
        if(self.roundFinished): time.sleep(1)

        # Increment the turn counter
        time.sleep(1)
        self.curTurn += 1

        # Move to the next player
        self.curPlayer += 1
        if (self.curPlayer > self.numPlayers):
            self.curPlayer = 1

    def playGolf(self):
        """
        playGolf(): play a full game of golf
        """
        self.buildScoreboard()

        # For each round
        for round in range(self.numRounds):
            self.roundFinished = False              # Flag for when all cards are flipped
            self.prevScores = self.scores.copy()    # Update based on final scores of previous round
            self.curRound = round + 1                   # Label of current round
            self.curTurn = 0                        # The turn within the round

            # Initialize a full deck
            self.deck = Deck()
            self.deck.fillDeck()
            self.deck.shuffle()

            # Deal each player 6 cards
            self.hands = []
            for i in range(self.numPlayers):
                curHand = Deck()
                for c in range(6):
                    curHand.addCard(self.deck.drawCard())
                self.hands.append(curHand)

            # Add one card from draw pile to the discard pile
            self.discard = Deck()
            self.discard.addCard(self.deck.drawCard())
            self.discard.cards[0].flipUp()

            # Each player can take turns moving
            # Until one player has all 6 cards face up
            while not self.roundFinished:

                # One player takes a turn
                self.takeTurn()

                # End the round if the previous player has flipped all their cards
                numFaceUp = len([c for c in self.hands[self.curPlayer-2].cards if c.faceUp])
                if(numFaceUp == 6):
                    self.roundFinished = True
                    # Let each player play one more turn
                    for p in range(self.numPlayers - 1):
                        self.takeTurn()

            # Announce the winner of the round
            settings.mainscreen.clear()
            roundScores = [self.scores[i]-self.prevScores[i] for i in range(len(self.scores))]
            # Check for ties
            if(len(roundScores) != len(set(roundScores))):
                winner = 'There was a tie in'
            else:
                winnerId = roundScores.index(min(roundScores)) + 1
                winner = 'Player ' + str(winnerId) + ' is the winner of'
            settings.mainscreen.addstr(2, 0, winner.center(curses.COLS-1))
            settings.mainscreen.addstr(3, 0, ('Round #' + str(self.curRound) + ' of').center(curses.COLS-1))
            settings.mainscreen.addstr(5, 0, settings.buildLogo())
            settings.mainscreen.addstr(17, 31, '[ Press any key to continue ]', curses.color_pair(4))
            settings.mainscreen.refresh()
            start = settings.mainscreen.getch() # Wait for feeback

        # Announce the winner of the game
        settings.mainscreen.clear()
        # Check for ties
        if(len(self.scores) != len(set(self.scores))):
            winner = 'There was a tie for this game of'
        else:
            winner = 'Player ' + str(self.scores.index(min(self.scores))+1) + ' is the winner of'
        settings.mainscreen.addstr(2, 0, winner.center(curses.COLS-1))
        settings.mainscreen.addstr(5, 0, settings.buildLogo())
        settings.mainscreen.addstr(17, 31, '[ Press any key to continue ]', curses.color_pair(1))
        settings.mainscreen.bkgd(' ', curses.color_pair(4))
        settings.mainscreen.refresh()
        start = settings.mainscreen.getch() # Wait for feeback

        # Clean for next game
        settings.mainscreen.clear()
