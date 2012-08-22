
import uuid
from google.appengine.ext import db
from datetime import datetime
from random import choice
from operator import itemgetter

class AssassinationException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)


class Mission(db.Model):
  """Models a mission for an assassin to kill a victim."""
  assassin = db.StringProperty()
  victim = db.StringProperty()
  timestamp = db.DateTimeProperty()
  status = db.IntegerProperty()

  SUCCESSP = 2  # public kill
  SUCCESS = 1
  INVALIDATED = 0
  FAILURE = -1
  SUICIDE = -2
  WIN = 9001

  ASSASSINATION_ACTIONS = [
    "assassinated", "air-conditioned", "annihilated", "barbequed", "bashed", "beat down", 
    "blasted", "bolted down", "butchered", "crushed", "creamed", "decaffeinated", "decimated", 
    "deep-fried", "destroyed", "disassembled", "discombobulated", "disintegrated", "dispatched", "diced", "dropkicked", 
    "eliminated", "eradicated", "eviscerated", "exterminated", "extinguished", "finished off", 
    "flame-broiled", "flatlined", "flattened", "fragged", "hosed", "humiliated", "incinerated", "impaled",
    "judo chopped", "knocked off", "liquidated", "lobotomized", "mangled", "massacred", "mauled", "mummified",
    "muted", "nuked", "nullified", "obliterated", "owned", "pancaked", "picked off", "plastered",
    "pummeled", "pwned", "railed", "recycled", "roasted", "rocked", "rolled and stuffed",
    "schooled", "served", "severed", "shut down", "sideswiped", "sizzled", "slapped", "slaughtered", "slayed",
    "sliced", "sliced and diced", "smacked down", "smashed", "smoked", "smote", "snuffed", "supressed", "switched off", 
    "took down", "took out", "trashed", "trounced", "vaporized", "ventilated", "vetoed", "whacked", "whipped",
    "wiped the floor with"
  ]
  SUICIDE_ACTIONS = [
    "committed seppuku",
    "slipped on a banana",
    "fell off a cliff",
    "committed suicide",
  ]

  def __str__(self):
    if self.timestamp:
      return "%s killed %s at %s." % (self.assassin, self.victim,
                                      self.timestamp.strftime('%a, %d %b %Y'))
    else:
      return "%s's current target is %s" % ( self.assassin, self.victim)

  def other_missions(self):
    return Mission.all().ancestor(self.parent_key())

  def set_status(self, status):
    self.status = status
    self.timestamp = datetime.now()

  @staticmethod
  def in_game(game_name):
    return Mission.all().ancestor(Game.get_key(game_name))


class Game(db.Model):
  """Models a game with a name"""
  @staticmethod
  def has_started(game_name):
    return Mission.in_game(game_name).count()

  @staticmethod
  def get_key(game_name):
    """Constructs a Datastore key for a Mission entity given an assassin."""
    return db.Key.from_path("Game", game_name)


class Player(db.Model):
  uid = db.StringProperty()
  nickname = db.StringProperty()
  email = db.StringProperty()
  code = db.StringProperty()
  publiclist = db.IntegerProperty(default=0)
  publickills = db.IntegerProperty(default=0)

  def other_players(self):
    return Player.all().ancestor(self.parent_key())

  def die(self, killer):
    assassination = Mission.all().ancestor(self.parent_key()).filter(
        "victim = ", self.nickname).filter("timestamp = ", None).get()
    mission = Mission.all().ancestor(self.parent_key()).filter(
        "assassin = ", self.nickname).filter("timestamp = ", None).get()
    if not assassination or not mission:
      raise AssassinationException("%s already dead." % self.nickname)

    revive = False
    updates = []

    if killer == assassination.assassin:
      assassination.set_status(Mission.SUCCESS)
      mission.set_status(Mission.FAILURE)
    elif killer == self.nickname:
      assassination.set_status(Mission.INVALIDATED)
      mission.set_status(Mission.SUICIDE)
    elif self.publiclist > 0:
      assassination.set_status(Mission.INVALIDATED)
      mission.set_status(Mission.FAILURE)

      publicmission = Mission(parent=self.parent_key())
      publicmission.assassin = killer
      publicmission.victim = self.nickname
      publicmission.set_status(Mission.SUCCESSP)
      updates.append(publicmission)

      publickiller = self.other_players().filter("nickname = ", killer).get()
      if not publickiller.current_mission():  # killer is dead
        if publickiller.publickills + 1 == 3:
          publickiller.publickills = 0
          revive = True
        else:
          publickiller.publickills += 1
        updates.append(publickiller)
    else:
      raise AssassinationException("Invalid code.")
    updates.append(assassination)
    updates.append(mission)

    if revive:
      newmission = Mission(parent=self.parent_key())
      newmission.assassin = assassination.assassin
      newmission.victim = killer
      newmission2 = Mission(parent=self.parent_key())
      newmission2.assassin = killer
      newmission2.victim = mission.victim
      updates.append(newmission)
      updates.append(newmission2)
    else:
      newmission = Mission(parent=self.parent_key())
      newmission.assassin = assassination.assassin
      newmission.victim = mission.victim
      if newmission.assassin == newmission.victim:
        newmission.set_status(Mission.WIN)
      updates.append(newmission)

    self.publiclist = -1
    updates.append(self)
    db.put(updates)

  def past_missions(self):
    return Mission.all().ancestor(self.parent_key()).filter(
        "assassin = ", self.nickname).filter("status !=", None).order("status").order("-timestamp")

  def current_mission(self):
    return Mission.all().ancestor(self.parent_key()).filter(
        "assassin = ", self.nickname).filter("timestamp =", None).get()

  def last_assassination_attempt(self):
    return Mission.all().ancestor(self.parent_key()).order("-timestamp") \
        .filter("victim = ", self.nickname).get()

  def is_alive(self):
    return self.current_mission() != None

  @staticmethod
  def get_top_killers(number):
    all_player_kills = [(player.nickname, player.get_kills().count(), player.is_alive()) for player in Player.all()]
    all_player_kills.sort(key=itemgetter(1), reverse=True)
    return all_player_kills[:number]

  @staticmethod
  def in_game(game_name):
    return Player.all().ancestor(Game.get_key(game_name))

  @staticmethod
  def get(game_name, name):
    return Player.all().ancestor(Game.get_key(game_name)).filter(
      "nickname = ", name).get()

  @staticmethod
  def newcode():
    killcode = uuid.uuid4().hex[:6]
    while Player.all().filter('code =',killcode).count():
      killcode = uuid.uuid4().hex[:6]
    return killcode.upper()