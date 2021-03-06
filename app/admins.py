﻿
import os
import math
import re
from random import shuffle, sample
from HTMLParser import HTMLParser

from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from google.appengine.api import users, mail
from google.appengine.ext import webapp
from models import *

class Renderer(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name') or os.environ['default_game_name']
    player_name = self.request.get('as')
    game_started = Game.has_started(game_name)

    games = Game.all()
    if not games.count():
        # TODO(billycao): Migrate to template
        self.response.out.write("No game has been created yet.<br />"
                                "The administrator must create one before the awesomeness begins.")
        return
    player = Player.get(game_name, player_name)

    # Game statistics
    stats_list = []
    num_players = Player.in_game(game_name).count()
    num_players_dead = Mission.in_game(game_name).filter('status !=', None).filter('status <', 0).count()
    num_kills = Mission.in_game(game_name)\
                       .filter('assassin =', player_name)\
                       .filter('status =', 1)\
                       .count()
    winner = Mission.in_game(game_name).filter('status =', 9001).get()

    stats_list.append(('Total Players', num_players))
    stats_list.append(('Players Dead', num_players_dead))
    stats_list.append(('Your Kills', num_kills))

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'game_name': game_name,
      'game_started': game_started,
      'games': games,
      'is_registered': player is not None,
      'killcode_quips': [
          "Remember it, and surrender it upon death.",
          "Hover to view. Keep it hidden. Keep it safe."
      ],
      'num_players': num_players,
      'target_mission': player.current_mission(),
      'assassination': player.last_assassination_attempt(),
      'stats_list': stats_list,
      'stats_list_width': len(stats_list) * 120,
      'url': url,
      'url_linktext': url_linktext,
      'player': player,
      'winner': winner,
      'FLAGS_show_game_title': os.environ['show_game_title'] == "True",
      'FLAGS_max_players': int(os.environ['max_players'])
    }

    path = os.path.join(os.path.dirname(__file__)+ '/../templates/', 'index.html')
    self.response.out.write(template.render(path, template_values))


class CreateGame(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name') or os.environ['default_game_name']
    if db.get(Game.get_key(game_name or 'default_game')):
      self.response.out.write("Exists")
      return
    game = Game(key_name=game_name or 'default_game')
    game.put()
    self.response.out.write("Created")

# Assigns top leaderboard player as winner if no winner already exists
class EndGame(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name') or os.environ['default_game_name']
    winner = Mission.in_game(game_name).filter('status =', Mission.WIN).get()
    if (winner):
      self.response.out.write("Done - " + winner.assassin + " already winner.")
      return
    else:
      leaders = Player.get_top_killers(1)
      if (len(leaders) > 0):
        winner_name = leaders[0][0]
        winner_mission = Mission(parent=Game.get_key(game_name))
        winner_mission.assassin = winner_name
        winner_mission.victim = winner_name
        winner_mission.status = 9001
        winner_mission.put()
        self.response.out.write("Done - " + winner_name + " marked winner.")


class ResetGame(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name') or os.environ['default_game_name']
    missions = Mission.in_game(game_name).fetch(None)
    db.delete(missions)
    self.response.out.write("Done")


class StartGame(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name') or os.environ['default_game_name']
    if Game.has_started(game_name):
      self.response.out.write("Already started")
      return

    users = Player.in_game(game_name).fetch(None)
    shuffle(users)

    assassin = users[len(users) - 1]
    for user in users:
      mission = Mission(parent=Game.get_key(game_name))
      mission.assassin = assassin.nickname
      mission.victim = user.nickname
      mission.put()
      user.numkills = 0
      user.publickills =  0
      user.publiclist = 0
      user.put()
      assassin = user
      # Send email to all players
      if not mail.is_email_valid(user.email):
        self.response.out.write("Warning: Invalid email: " + user.email)
      else:
        sender_address = os.environ['start_email_sender']
        subject = "[League of Interns] Let the games begin!"
        html = os.environ['start_email_body'] % game_name
        body = re.sub('<[^<]+?>', '', html)
        mail.send_mail(sender_address, user.email, subject, body, html=html)
    self.response.out.write("Done")


class UpdateNumKills(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    players = Player.in_game(game_name).fetch(None)
    update = []
    for p in players:
      p.numkills = p.get_kills().count()
      update.append(p)
    db.put(update)


class GenKillList(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    alive = Mission.in_game(game_name).filter('status =', None).fetch(None)
    alivenames = [ p.assassin for p in alive ]
    update = []
    candidates = []
    for name in alivenames:
      player = Player.get(game_name, name)
      if player.publiclist == 0 or player.publiclist == 1:
        player.publiclist = 0
        if player.numkills == 0:
          candidates.append(player)
        update.append(player)

    numpubliclist = 0
    targetnumpubliclist = min(int(os.environ['num_hitlist']), len(candidates))
    while (numpubliclist < targetnumpubliclist):
      for player in sample(candidates, targetnumpubliclist - numpubliclist):
        player.publiclist = 1
        numpubliclist = numpubliclist + 1
        candidates.remove(player)

    for p in update:
      self.response.out.write('%s %d<br />' % (p.nickname, p.publiclist))
    db.put(update)


class FreeAttempts(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    players = Player.in_game(game_name)
    updates = []
    for p in players:
      p.numfailtries = 0
      updates.append(p)
    db.put(updates)