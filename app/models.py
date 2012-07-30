#!/usr/bin/env python

from google.appengine.ext import db
from datetime import datetime

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
    elif self.victim == 'Billy':
      print 'Billy is a n00b'
    else:
      return "%s's current target is %s" % (
          self.assassin,
          self.victim)

  def other_missions(self):
    return Mission.all().ancestor(self.parent_key())

  @staticmethod
  def in_game(game_name):
    return Mission.all().ancestor(game_key(game_name))
  
class Game(db.Model):
  """Models a game with a name"""
  @staticmethod
  def has_started(game_name):
    return Mission.in_game(game_name).count()

class AssassinationException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)
  
class Player(db.Model):
  uid = db.StringProperty()
  nickname = db.StringProperty()
  email = db.StringProperty()
  code = db.StringProperty()

  def other_players(self):
    return Player.all().ancestor(self.parent_key())
    
  def die(self, killer):
    assassination = Mission.all().ancestor(self.parent_key()).filter(
        "victim = ", self.nickname).filter("timestamp = ", None).get()
    mission = Mission.all().ancestor(self.parent_key()).filter(
        "assassin = ", self.nickname).filter("timestamp = ", None).get()
    if not assassination or not mission:
      raise AssassinationException("%s already dead." % self.nickname)
        
    if killer == self.nickname:
      assassination.status = 0
      mission.status = -1
    elif killer == assassination.assassin:
      assassination.status = 1
      mission.status = -1
    else:
      raise AssassinationException("%s cannot kill %s." % (killer, self.nickname))
    assassination.timestamp = datetime.now()
    mission.timestamp = datetime.now()
    assassination.put()
    mission.put()
    
    newmission = Mission(parent=self.parent_key())
    newmission.assassin = assassination.assassin
    newmission.victim = mission.victim
    if newmission.assassin == newmission.victim:
      newmission.status = 9001
    newmission.put()

  @staticmethod
  def in_game(game_name):
    return Player.all().ancestor(game_key(game_name))

  @staticmethod
  def get(game_name, name):
    return Player.all().ancestor(game_key(game_name)).filter(
      "nickname = ", name).get()

def game_key(game_name=None):
  """Constructs a Datastore key for a Mission entity given an assassin."""
  return db.Key.from_path("Game", game_name or 'MTV')