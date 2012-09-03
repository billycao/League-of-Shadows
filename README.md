League of Shadows
=================

An [assassins](http://en.wikipedia.org/wiki/Assassin_\(game\)) game powered by App Engine.

Setup
-----

1. [Create an App Engine application](https://appengine.google.com).
2. [Download the Google App Engine SDK for Python](https://developers.google.com/appengine/downloads).
3. Change the application: line in app.yaml to the name of the application you just created.
4. Edit the env_variables in app.yaml to suit your needs. You'll likely at least need to change:
  global_name
  global_desc
  short_desc
  rules
  faq
  contact_emails
  time_*
5. Upload the application to appengine by running the following command:
    appcfg.py update .
6. Create a game by navigating to /admin/create?game_name=default

Administration
--------------

**Note that the game currently must be updated manually, even if you specified specific times in app.yaml.**

### Creating a game

Before players sign up, you'll have to create a game (the game_name parameter is optional):

https://example.com/admin/create?game_name=default

### Starting a game

When all the players have joined, go here on an admin account to start the game:

https://example.com/admin/start?game_name=default

### Ending a game

The game automatically ends when there is only one assassin left.
To end the game early and assign the winner to the #1 player on the leaderboard, go to:

https://example.com/admin/end?game_name=default

### Resetting a game

Accidentally start the game? Something go wrong? You can reset the game and delete all game data.
**WARNING**: This deletes all current game data.

https://example.com/admin/reset?game_name=default