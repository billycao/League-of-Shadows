
from datetime import timedelta
import sys, os
import urllib
from lib import csrf
try:
    import json
except ImportError:
    import simplejson as json
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from app.models import *

class MainPage(webapp.RequestHandler):
  def get(self):
    games = Game.all()
    if not games.count():
      # TODO(billycao): Migrate to template
      self.response.out.write("No game has been created yet.<br />"
                              "The administrator must create one before the awesomeness begins.")
      return

    game_name = self.request.get('game_name') or os.environ['default_game_name']
    game_started = Game.has_started(game_name)

    player_name = users.get_current_user().nickname()
    player = Player.get(game_name, player_name)

    # Game statistics
    num_players = Player.in_game(game_name).count()
    num_players_dead = Mission.in_game(game_name).filter('status !=', None).filter('status <', 0).count()
    num_players_alive = num_players - num_players_dead
    winner = Mission.in_game(game_name).filter('status =', Mission.WIN).get()
    publiclist = Player.in_game(game_name).filter('publiclist >', 0).fetch(None)

    # Leaderboard
    leaderboard = []
    leaders = Player.get_top_killers(5)
    leaderboard = [(name, kills, 'ACTIVE' if status else 'DEAD') for name, kills, status in leaders]

    # Player specific statistics
    num_kills = 0
    missions = None
    if player != None:
      num_kills = player.get_kills().count()
      missions = player.past_missions().fetch(None)

    stats_list = []
    stats_list.append(('Total Players', num_players))
    stats_list.append(('Survivors', num_players_alive))
    stats_list.append(('Players Dead', num_players_dead))
    stats_list.append(('Your Kills', num_kills))

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'csrf_token': csrf.get_csrf_token(player_name),
      'game_name': game_name,
      'game_started': game_started,
      'games': games,
      'is_registered': player is not None,
      'killcode_quips': [
          "Remember it, and surrender it upon death.",
          "Hover to view. Keep it hidden. Keep it safe."
      ],
      'missions': missions,
      'leaderboard': leaderboard,
      'num_players': num_players,
      'stats_list': stats_list,
      'stats_list_width': len(stats_list) * 120,
      'target_mission': None,
      'url': url,
      'url_linktext': url_linktext,
      'player': player,
      'publiclist': publiclist,
      'winner': winner,
      'max_players': int(os.environ['max_players']),
      'FLAGS': os.environ,
    }

    if player:
      template_values['target_mission'] = player.current_mission()
      template_values['assassination'] = player.last_assassination_attempt()
    
    path = os.path.join(os.path.dirname(__file__)+ '/../templates/', 'index.html')
    self.response.out.write(template.render(path, template_values))

    
class KillList(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    public_hitlist = []
    if (os.environ['public_hitlist'] == 'true'):
      public_hitlist = Player.in_game(game_name).filter('publiclist >', 0).fetch(None)
    template_values = {
      'public_hitlist': public_hitlist
    }
    path = os.path.join(os.path.dirname(__file__)+ '/../templates/', 'killlist.html')
    self.response.out.write(template.render(path, template_values))


class DeathList(webapp.RequestHandler):
  def get(self):
    game_name = self.request.get('game_name')
    events = Mission.in_game(game_name).order('-timestamp').fetch(None)

    template_values = {
      'events': events
    }
    path = os.path.join(os.path.dirname(__file__)+ '/../templates/', 'feed.html')
    self.response.out.write(template.render(path, template_values))


class JoinGame(webapp.RequestHandler):
  def post(self):
    game_name = self.request.get('game_name')

    if Player.in_game(game_name).count() >= int(os.environ['max_players']):
      self.response.out.write("The player maximum of " + os.environ['max_players'] + " has been reached.")
    elif users.get_current_user():
      exists = Player.in_game(game_name).filter(
          'nickname =', users.get_current_user().nickname()).count()
      if not exists:
        player = Player(parent=Game.get_key(game_name),
            key_name=users.get_current_user().nickname())
        player.code = Player.newcode()
        player.nickname = users.get_current_user().nickname()
        player.uid = users.get_current_user().user_id()
        player.email = users.get_current_user().email()
        player.put()
      self.redirect('/?' + urllib.urlencode({'game_name': game_name}))
    else:
      url = users.create_login_url(self.request.uri)
      self.response.out.write("<a href=\"%s\">Login</a>" % url)


class Kill(webapp.RequestHandler):
  def post(self):
    terminator = os.environ['public_hitlist'] == 'True'
    game_name = self.request.get('game_name')
    code = self.request.get('killcode').upper()

    # If a winner already exists no kills can be made.
    winner = Mission.in_game(game_name).filter('status =', Mission.WIN).get()
    if (winner):
      return

    if users.get_current_user():
      player_name = users.get_current_user().nickname()
      if not csrf.check_csrf_token(player_name, self.request.get('csrf_token')):
        self.response.out.write(json.dumps({
          'status': 'error',
          'message': "Invalid CSRF token. Please refresh the page and try again."
        }))
        return

      player = Player.get(game_name, player_name)
      mission = Mission.in_game(game_name).filter(
        'assassin =', player_name).filter('timestamp =', None).get()

      if player.numfailtries > 3:
        self.response.out.write(json.dumps({
          'status': 'error',
          'message': "Too many failed attempts. Please wait a while before trying again."
        }))
        return
      
      if os.environ['allow_suicide'] == 'True' and player.code.upper() == code:
        try:
          player.die(player_name)
          self.response.out.write(json.dumps({
            'status': 'suicide',
            'message': "You've commited suicide!"
          }))
        except AssassinationException, e:
          self.response.out.write(json.dumps({
            'status': 'error',
            'message': "Cannot commit suicide. (%s)" % e
          }))
      elif not terminator:
        # Be more restrictive if terminator is off and make sure code is right.
        try:
          victim = Player.get(game_name, mission.victim)
          if victim.code.upper() != code:
            raise AssassinationException(victim.nickname)
          victim.die(player_name)
          self.response.out.write(json.dumps({
            'status': 'success',
            'message': "You've killed %s!" % victim.nickname
          }))
        except AssassinationException, e:
          self.response.out.write(json.dumps({
            'status': 'error',
            'message': "Invalid code."
          }))
      elif terminator:
        try:
          victim = Player.in_game(game_name).filter("code = ", code).get()
          if not victim:
            raise AssassinationException("--")
          victim.die(player_name)
          self.response.out.write(json.dumps({
            'status': 'success',
            'message': "You've killed %s!" % victim.nickname
          }))
        except AssassinationException, e:
          player.numfailtries = player.numfailtries + 1
          player.put()
          self.response.out.write(json.dumps({
            'status': 'error',
            'message': "Invalid code."
          }))
      else:
        self.response.out.write(json.dumps({
          'status': 'error',
          'message': "Invalid code."
        }))