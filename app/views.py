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
    user_name = users.get_current_user().nickname()

    games = Game.all()
    missions = Mission.all().ancestor(game_key(game_name)).order('assassin')
    my_missions = missions.filter('assassin =', user_name)

    # Game statistics
    num_players = missions.filter('timestamp =', None).count()

    # Player stats
    is_registered = my_missions.count()
    target_mission = my_missions.order('timestamp').fetch(1)

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'curr_game': game_name,
      'games': games,
      'is_registered': is_registered,
      'num_players': num_players,
      'target_mission': target_mission,
      'url': url,
      'url_linktext': url_linktext,
      'user_name': user_name,
      'FLAGS_show_game_title': os.environ['show_game_title'] == "True"
    }
    
    path = os.path.join(os.path.dirname(__file__)+ '/../templates/', 'index.html')
    self.response.out.write(template.render(path, template_values))

class JoinGame(webapp.RequestHandler):
  def post(self):
    game_name = self.request.get('game_name')
    mission = Mission(parent=game_key(game_name))

    if users.get_current_user():
      exists = Mission.all().filter('assassin =', users.get_current_user().nickname())\
                            .ancestor(game_key(game_name)).count()
      if not exists:
        mission.assassin = users.get_current_user().nickname()
        mission.put()
      self.redirect('/?' + urllib.urlencode({'game_name': game_name}))
    else:
      url = users.create_login_url(self.request.uri)
      self.response.out.write("<a href=\"%s\">Login</a>" % url)