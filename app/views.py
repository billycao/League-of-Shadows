﻿#!/usr/bin/env python

import os
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from models import *

class MainPage(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name') or 'MTV'

    games = Game.all()
    missions = Mission.all().ancestor(game_key(game_name))
    players = missions.order('assassin')

    # Game statistics
    num_players = players.count()
    target = missions.order('assassin').filter('assassin =', users.get_current_user().nickname()).fetch(1)

    # Get current player information

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'curr_game': game_name,
      'games': games,
      'target': target,
      'num_players': num_players,
      'url': url,
      'url_linktext': url_linktext,
      'FLAGS_show_game_title': os.environ['show_game_title'] == "True"
    }
    
    path = os.path.join(os.path.dirname(__file__)+ '/../templates/', 'index.html')
    self.response.out.write(template.render(path, template_values))

class JoinGame(webapp.RequestHandler):
  def post(self):
    game_name = self.request.get('game_name')
    mission = Mission(parent=game_key(game_name))

    if users.get_current_user():
      exists = Mission.all().filter('assassin =',
      users.get_current_user().nickname()).ancestor(game_key(game_name)).count()
      if not exists:
        mission.assassin = users.get_current_user().nickname()
        mission.put()
      self.redirect('/?' + urllib.urlencode({'game_name': game_name}))
    else:
      url = users.create_login_url(self.request.uri)
      self.response.out.write("<a href=\"%s\">Login</a>" % url)