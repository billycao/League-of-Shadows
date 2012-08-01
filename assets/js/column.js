/**
 * Adapted from http://www.switchonthecode.com/tutorials/javascript-and-css-tutorial-accordion-menus.
 */


var ContentHeight = 400;
var TimeToSlide = 200.0;

var openColumn = '';

function selectColumn(col_id) {
  if(openColumn == col_id)
    col_id = '';
    
  setTimeout("animate(" + new Date().getTime() + "," + TimeToSlide + ",'" 
      + openColumn + "','" + col_id + "')", 33);
  
  openColumn = col_id;
}

function animate(lastTick, timeLeft, closingId, openingId) {  
  var curTick = new Date().getTime();
  var elapsedTicks = curTick - lastTick;
  
  var opening = (openingId == '') ? null : document.getElementById(openingId);
  var closing = (closingId == '') ? null : document.getElementById(closingId);
 
  if(timeLeft <= elapsedTicks)
  {
    if(opening != null)
      opening.style.height = ContentHeight + 'px';
    
    if(closing != null)
    {
      closing.style.display = 'none';
      closing.style.height = '0px';
    }
    return;
  }
 
  timeLeft -= elapsedTicks;
  var newClosedHeight = Math.round((timeLeft/TimeToSlide) * ContentHeight);

  if(opening != null)
  {
    if(opening.style.display != 'block')
      opening.style.display = 'block';
    opening.style.height = (ContentHeight - newClosedHeight) + 'px';
  }
  
  if(closing != null)
    closing.style.height = newClosedHeight + 'px';

  setTimeout("animate(" + curTick + "," + timeLeft + ",'" 
      + closingId + "','" + openingId + "')", 33);
}