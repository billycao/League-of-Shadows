#!/usr/bin/env python

from google.appengine.ext import db

class Mission(db.Model):
  """Models a mission for an assassin to kill a victim."""
  assassin = db.StringProperty()
  victim = db.StringProperty()
  timestamp = db.DateTimeProperty()
  
class Game(db.Model):
  """Models a game with a name"""
  pass

def game_key(game_name=None):
  """Constructs a Datastore key for a Mission entity given an assassin."""
  return db.Key.from_path("Game", game_name or 'MTV')