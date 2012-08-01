#!/usr/bin/env python

import sys, os
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from models import *

class MainPage(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name') or 'MTV'
    player_name = users.get_current_user().nickname()

    games = Game.all()
    if not games.count():
        # TODO(billycao): Migrate to template
        self.response.out.write("No game has been created yet.<br />"
                                "The administrator must create one before the awesomeness begins.")
        return
    # TODO(billycao): Encapsulate database query calls into some sort of interface
    my_missions = Mission.in_game(game_name).filter(
        'assassin =', player_name)

    # Game statistics
    num_players = Player.in_game(game_name).count()
    winner = Mission.in_game(game_name).filter(
        'status =', 9001).get()

    # Player stats
    is_registered = Player.in_game(game_name).filter(
        'nickname =', player_name).count()
    player_code = ''
    target_mission = None
    death_mission = None
    is_suicide = False
    if is_registered:
        player_code = Player.in_game(game_name).filter(
            'nickname =', player_name).get().code
        target_mission = my_missions.filter('timestamp =', None).get()
        if target_mission is None:
          death_mission = Mission.in_game(game_name).filter(
            'victim =', player_name).get()
          is_suicide = Mission.in_game(game_name)\
                              .filter('assassin =', player_name)\
                              .get().status == -1

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'game_name': game_name,
      'game_started': Game.has_started(game_name),
      'games': games,
      'is_registered': is_registered,
      'is_suicide': is_suicide,
      'num_players': num_players,
      'target_mission': target_mission,
      'death_mission': death_mission,
      'url': url,
      'url_linktext': url_linktext,
      'player_name': player_name,
      'player_code': player_code,
      'winner': winner,
      'FLAGS_show_game_title': os.environ['show_game_title'] == "True",
      'FLAGS_max_players': int(os.environ['max_players'])
    }
    
    path = os.path.join(os.path.dirname(__file__)+ '/../templates/', 'index.html')
    self.response.out.write(template.render(path, template_values))

    
class JoinGame(webapp.RequestHandler):
  def post(self):
    game_name = self.request.get('game_name')

    if Player.in_game(game_name).count() >= int(os.environ['max_players']):
      self.response.out.write("The player maximum of " + os.environ['max_players'] + " has been reached.")
    elif users.get_current_user():
      exists = Player.in_game(game_name).filter(
          'nickname =', users.get_current_user().nickname()).count()
      if not exists:
        player = Player(parent=game_key(game_name),
            key_name=users.get_current_user().nickname())
        player.code = Player.newcode()
        player.nickname = users.get_current_user().nickname()
        player.uid = users.get_current_user().user_id()
        player.email = users.get_current_user().email()
        player.put()
      self.redirect('/?' + urllib.urlencode({'game_name': game_name}))
    else:
      url = users.create_login_url(self.request.uri)
      self.response.out.write("<a href=\"%s\">Login</a>" % url)
        
class Kill(webapp.RequestHandler):
  def post(self):
    game_name = self.request.get('game_name')
    code = self.request.get('killcode').lower()
    ksuccesstext = "true"

    if users.get_current_user():
      player = Player.get(game_name, users.get_current_user().nickname())
      mission = Mission.in_game(game_name).filter(
        'assassin =', users.get_current_user().nickname()).filter('timestamp =', None).get()
      victim = Player.get(game_name, mission.victim)
      
      if player.code.lower() == code:
        try:
          player.die(users.get_current_user().nickname())
          self.response.out.write(ksuccesstext)
        except AssassinationException, e:
          self.response.out.write(e)
      elif victim.code.lower() == code:
        try:
          victim.die(users.get_current_user().nickname())
          self.response.out.write("Congratulations! You've killed %s!" % victim.nickname)
        except AssassinationException, e:
          self.response.out.write(e)
      else:
        self.response.out.write("Invalid code.")
