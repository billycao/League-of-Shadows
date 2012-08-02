
import uuid
from google.appengine.api import memcache

def get_csrf_token(username):
  token = memcache.get(username, namespace='csrf-token')
  if token:
    return token
  else:
    token = str(uuid.uuid4())
    memcache.add(username, value=token, time=3600, namespace='csrf-token')
    return token
    
def check_csrf_token(username, token):
  return memcache.get(username, namespace='csrf-token') == token
  
def clear_csrf_token(username):
  memcache.delete(username, namespace='csrf-token')