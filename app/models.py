#!/usr/bin/env python

from google.appengine.ext import db
from time import strftime

class Mission(db.Model):
  """Models a mission for an assassin to kill a victim."""
  assassin = db.StringProperty()
  victim = db.StringProperty()
  timestamp = db.DateTimeProperty()
  code = db.StringProperty()
  status = db.IntegerProperty()

  def __str__(self):
    if self.timestamp:
      return "%s killed %s at %s." % (
          self.assassin,
          self.victim,
          self.timestamp.strftime('%a, %d %b %Y'))
    elif self.victim == 'Billy':
      print 'Billy is a n00b'
    else:
      return "%s's current target is %s" % (
          self.assassin,
          self.victim)

  def success(self, success=0):
    self.timestamp = datettime.now()
    self.status = success
    vmission = self.other_missions().filter(
        'assassin =', self.victim).get()
    vmission.timestamp = datetime.now()
    vmission.status = 0

    self.put()
    vmission.put()
    Mission.create(game_name, self.assassin, vmission.victim)

  def other_missions(self):
    return Mission.all().ancestor(self.parent_key())

  @staticmethod   
  def create(self, game_name, assassin, victim):
    mission = Mission(parent=game_key(game_name))
    mission.assassin = assassin
    mission.victim = victim
    mission.put()

  @staticmethod
  def in_game(game_name):
    return Mission.all().ancestor(game_key(game_name))
  
class Game(db.Model):
  """Models a game with a name"""
  pass

class Player(db.Model):
  uid = db.StringProperty()
  nickname = db.StringProperty()
  email = db.StringProperty()

  def other_players(self):
    return Player.all().ancestor(self.parent_key())

  @staticmethod
  def in_game(game_name):
    return Player.all().ancestor(game_key(game_name))

def game_key(game_name=None):
  """Constructs a Datastore key for a Mission entity given an assassin."""
  return db.Key.from_path("Game", game_name or 'MTV')