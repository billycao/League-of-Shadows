
import logging, email
from google.appengine.ext import webapp
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp.util import run_wsgi_app
from app.models import *

class LogSenderHandler(InboundMailHandler):
  def receive(self, mail_message):
    code = mail_message.subject
    sender = mail_message.sender
    assassin = Player.all().filter('email =', sender).get()
    players = Player.all().filter('code =', code).fetch(None)
    for player in players:
      mission = Mission.all().filter('assassin =', assassin.nickname).filter(
          'victim =', player.nickname).filter('timestamp =', None).count()
      if mission:
        player.die(assassin.nickname)
        return

application = webapp.WSGIApplication([LogSenderHandler.mapping()], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
