import re, string
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
from lxml import html

TCN_PREFIX      = "/video/TheComedyNetwork"
TCN_URL         = 'http://watch.thecomedynetwork.ca/'
TCN_SEARCH      = 'http://watch.thecomedynetwork.ca/AJAX/SearchResults.aspx?query=%s'
TCN_CLIP_LOOKUP = 'http://watch.thecomedynetwork.ca/AJAX/ClipLookup.aspx?episodeid=%s'
CACHE_TIME      = 1800

####################################################################################################
def Start():
  Log('(TCN): Start')
  Plugin.AddPrefixHandler(TCN_PREFIX, MainMenu, 'The Comedy Network', 'icon-default.png', 'art-default.jpg')
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.title1 = 'The Comedy Network'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.jpg')

####################################################################################################
def MainMenu():
  Log('(TCN): MainMenu')
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(GetVideoLibrary, title="Video Library", thumb=R('icon-default.png')), url= TCN_URL + 'library/', level=1, title2="Video Library"))
  dir.Append(Function(DirectoryItem(GetFeatured, title="Featured", thumb=R('icon-default.png')), url= TCN_URL + 'featured/', title2="Featured"))
  dir.Append(Function(SearchDirectoryItem(Search, title=L("Search"), prompt=L("Search for Videos"), thumb=R('search.png'))))
  HTTP.SetCacheTime(CACHE_TIME)
  return dir

####################################################################################################
def GetVideoLibrary(sender, level, url, title2):
  Log('(TCN): GetVideoLibrary: %d' % level )
  dir = MediaContainer(title2=title2)
  for show in XML.ElementFromURL(url, True).xpath('//div[@id="Level%d"]/ul/li' % level):   
    title = show.find('a').get('title')
    url = show.find('a').get('href')
    if level == 3:
      item = show.xpath('.//dl[@class="Item"]')[0]   
      try: summary =  item.find('dd[@class="Description"]' ).text 
      except: summary ="No Summary Available" 
      try:
        thumb =  item.find('dd[@class="Thumbnail"]/a/img').get('src')
        thumb = thumb[:thumb.rfind('.jpg') + 4]
      except: thumb = None
      dir.Append(WebVideoItem(url, title, date="", summary=summary, thumb=thumb))
    else:
      dir.Append(Function(DirectoryItem(GetVideoLibrary, title, thumb=R('icon-default.png')), level=level+1, url=url, title2=title))
  return dir

def GetFeatured(sender, url, title2):
  Log('(TCN): GetFeatured' )
  dir = MediaContainer(title2=title2)
  for show in XML.ElementFromURL(url, True).xpath('//div[@class="Frame"]/ul/li'):    
    try:
      item = show.xpath('.//dl[@class="Item"]')[0]    
      title = item.find('dt/a').get('title')
      url = item.find('dt/a').get('href')
      Log('Title: %s  URL: %s' % (title, url))
      try: summary = item.find('dd[@class="Description"]').text
      except: summary = "No Summary Available" 
      try:
        thumb =  item.find('dd[@class="Thumbnail"]/a/img').get('src')
        thumb = thumb[:thumb.rfind('.jpg') + 4]
      except: thumb = None
      dir.Append(WebVideoItem(url, title, date="", summary=summary, thumb=thumb))    
    except: pass    
  return dir

def GetVideoFromEpisodeId( episodeId):
  show = HTTP.Request(TCN_CLIP_LOOKUP % episodeId)
  expression = re.compile("EpisodePermalink:'(.+?)'", re.MULTILINE)
  url = expression.search(show).group(1)
  return url

def Search(sender, query):
  dir = MediaContainer(viewGroup='Details', title2='Search Results')
  query = query.replace(' ', '+')
  for result in XML.ElementFromURL(TCN_SEARCH % query, True).xpath('//div[@class="Frame Search"]/ul/li'):
    if result.find('dl').get('class') != "NotPlayable":      
      try:
        try:
          result.find('.//b').drop_tag()
          result.find('.//strong').drop_tag()
        except: pass 
        title = result.find('dl/dd[@class="ResultTitle"]/a').text
        try: summary = result.find('dl/dd[@class="ResultDescription"]').text
        except: summary = "No Description Available"  
        try:
          thumb = result.find('dl/dd[@class="SearchThumbnail"]/a/img').get('src')
          thumb = thumb[:thumb.rfind('.jpg') + 4]
        except: thumb = None
        episodeId = result.find('dl/dd[@class="PlayNow"]/a').get('href')
        episodeId = re.search("(\d+)",episodeId).group()  
        url = GetVideoFromEpisodeId(episodeId)
        dir.Append(WebVideoItem(url, title, date="", summary=summary, thumb=thumb))            
      except: pass      
  return dir