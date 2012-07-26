#!/usr/bin/env python

from google.appengine.ext import db
from time import strftime

class Mission(db.Model):
  """Models a mission for an assassin to kill a victim."""
  assassin = db.StringProperty()
  victim = db.StringProperty()
  timestamp = db.DateTimeProperty()
  status = db.IntegerProperty()

  def __str__(self):
    if self.timestamp:
      return "%s killed %s at %s." % (
          self.assassin,
          self.victim,
          self.timestamp.strftime('%a, %d %b %Y'))
    else:
      return "%s's current target is %s" % (
          self.assassin,
          self.victim)

  def finish(self):
    self.timestamp = datettime.now()
    vmission = self.other_players().filter(
        'assassin =', self.victim).get()
    vmission.timestamp = datetime.now()

    newmission = Mission()
    newmission.assassin = self.assassin
    newmission.victim = vmission.victim

    self.put()
    vmission.put()
    newmission.put()

  def other_players(self):
    return Mission.all().ancestor(self.parent_key())

  @staticmethod
  def in_game(game_name):
    return Mission.all().ancestor(game_key(game_name))
  
class Game(db.Model):
  """Models a game with a name"""
  pass

def game_key(game_name=None):
  """Constructs a Datastore key for a Mission entity given an assassin."""
  return db.Key.from_path("Game", game_name or 'MTV')