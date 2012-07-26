#!/usr/bin/env python

import os
from random import shuffle

from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from models import *

class CreateGame(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    game = Game(key_name=game_name or 'default_game')
    game.put()
    self.response.out.write("Created")

class StartGame(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    started = Mission.in_game(game_name).filter('timestamp !=', None).count()
    if started:
      self.response.out.write("Already started")
      return

    missions = Mission.in_game(game_name).fetch(None)
    victims = [ mission.assassin for mission in missions ]
    shuffle(victims)

    for mission in missions:
      victim = victims.pop()
      while victim == mission.victim:
        victims.insert(0, victim)
        victim = victims.pop()
      mission.victim = victim
      mission.put()
    self.response.out.write("Done")
