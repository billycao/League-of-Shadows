#!/usr/bin/env python

import os

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