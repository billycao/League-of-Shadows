﻿#!/usr/bin/env python

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
    if db.get(game_key(game_name or 'default_game')):
      self.response.out.write("Exists")
      return
    game = Game(key_name=game_name or 'default_game')
    game.put()
    self.response.out.write("Created")
	
class EndGame(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    missions = Mission.in_game(game_name).fetch(None)
    db.delete(missions)
    self.response.out.write("Done")

class StartGame(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    if Game.has_started(game_name):
      self.response.out.write("Already started")
      return

    users = Player.in_game(game_name).fetch(None)
    players = [ player.nickname for player in users ]
    shuffle(players)

    assassin = players[len(players) - 1]
    for player in players:
      mission = Mission(parent=game_key(game_name))
      mission.assassin = assassin
      mission.victim = player
      mission.put()
      assassin = player
    self.response.out.write("Done")
    
