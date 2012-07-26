#!/usr/bin/env python

import wsgiref.handlers

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from app.admins import *
from app.views import *

application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/join', JoinGame),
  ('/admin/create', CreateGame),
  ('/admin/start', StartGame)
], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()