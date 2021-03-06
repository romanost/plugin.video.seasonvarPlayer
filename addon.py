'''
Created on Dec 19, 2015

@author: Roman Ost.
'''

import os



import sys
import re
import json
import urllib
import urllib2
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import HTMLParser
from collections import OrderedDict
from bs4 import BeautifulSoup

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
site_url="http://seasonvar.ru"
thumbs_url="http://cdn.seasonvar.ru/oblojka/" ## +id.jpg
pl_url=site_url+"/playls2/"                   ## +secure+x/trans/+id+/list.xml
srch_url=site_url+"/autocomplete.php?query="  ## +string
info_url=site_url+"/serialinfo/"              ## +id+"/"  
faddon=xbmcaddon.Addon(id='plugin.video.seasonvarPlayer')
favs_url= xbmc.translatePath(faddon.getAddonInfo('profile'))+"favs.xml" 
##favs_url="special://userdata/"

ipp=20      # Items per page

xbmcplugin.setContent(addon_handle, 'movies')

items=[]

class myHTML(HTMLParser.HTMLParser):
    act=False
    ser=False
    stab=False
    read_info=False
    curlet=""
    sid=0
    slink=""
    biglist=OrderedDict()
    sinfo=""
    def handle_starttag(self,tag,attrs):
        if (tag=="a") and self.ser:
            self.sid=attrs[0][1][1:]
            self.slink=attrs[2][1]
        if (tag=="td"):
            #print "TD:",tag,attrs
            if self.read_info:
                self.stab=True
        if tag !="div":
            return
        if ('class','betterT') in attrs:
            self.ser=True
            self.stab=False
        if ('class','alf-letter hideLetter') in attrs:
            self.act=True
            self.stab=False
        else:
            self.act=False
    def handle_data(self,data):
        if self.read_info:
            if self.stab:
                data=data.strip()
                self.sinfo+=data
                if data[-1:]!=":":
                    self.sinfo+="\n"
        else:
            if self.act:
                self.curlet=data
                self.biglist[self.curlet]={}
                self.act=False
            if self.ser:
                self.ser=False
                self.biglist[self.curlet][data]={}
                self.biglist[self.curlet][data]['id']=self.sid
                self.biglist[self.curlet][data]['link']=self.slink

def log(str,lvl="NOTICE"):
    output="[plugin.video.seasonvarPlayer]: "+str
    print output

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def get_site(s_url):
    return urllib2.urlopen(s_url).read()

def get_file(fname):
    f=open(fname,'r')
    return f.read() 

def endoflist():
    #log("Adding items")
    xbmcplugin.addDirectoryItems(addon_handle, items, len(items))
    #xbmcplugin.addSortMethod(addon_handle,xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)
    return

mysite=myHTML()
def parse(link=site_url):
    #log("Parsing")
    page=get_site(link)
    mysite.feed(page)
    return

def add_link(s_url,sname,sid=0,isfldr=False,contx=[]):
    #log("adding:"+sname)
    sname=sname.replace("<br>", " - ")
    if sid==0:
        simg='DefaultFolder.png'
    else:
        simg=thumbs_url+sid+'.jpg'
    li = xbmcgui.ListItem(sname, iconImage=simg)
    mysite.read_info=True
    mysite.sinfo=""
    parse(info_url+str(sid)+"/")
    mysite.read_info=False
    li.setInfo('video',{'title':sname, 'plot':mysite.sinfo})
    if contx:
        li.addContextMenuItems(contx)
    items.append((s_url,li,isfldr))
    return True

def read_playlist(surl):
    page=get_site(surl)
    elem=re.findall('id": "(.*)", "serial": "(.*)" , "type": "html5", "secure": "(.*)"', page)[0]
    serid=elem[0]
    sersec=elem[2]
    playlink=pl_url+sersec+'x/trans/'+serid+'/list.xml'
    page=get_site(playlink)
    return json.loads(page)

def parse_playlist(plurl):
    plist=[]
    parsed=read_playlist(plurl)
#     for one in parsed['playlist']:
#         sname=one['comment']
#         slink=one['file']
#         add_link(slink,sname,serid)
        
    for one in parsed['playlist']:
        if one.has_key('file'):
            plist.append(one)
        elif one.has_key('playlist'):
            for two in one['playlist']:
                plist.append(two)
    return plist

mode = args.get('mode', None)

if mode is None:
    url = build_url({'mode': 'search', 'foldername': 'Search'})
    add_link(url,'Search',0,True)
    url = build_url({'mode': 'browse', 'foldername': 'Browse'})
    add_link(url,'Browse',0,True)
    url = build_url({'mode': 'favs', 'foldername': 'Favorites'})
    add_link(url,'Favorites',0,True)
    endoflist()

elif mode[0] == 'search':
    kkbd=xbmc.Keyboard("", "Search for:",False)
    kkbd.doModal()
    if (kkbd.isConfirmed()):
        ktext=unicode(kkbd.getText(),"utf-8")
        ktext=ktext.encode('utf-8')
        ksrch=urllib.quote_plus(ktext)
        kurl=srch_url+ksrch
        page=get_site(kurl)
        parsed=json.loads(page)
        playlist=[]
        if parsed['query']:
            total=len(parsed["suggestions"])
            for i in range(0,total):
                slink=site_url+"/"+parsed['data'][i]
                sid=parsed['id'][i]
                sname=parsed['suggestions'][i].encode('utf8')
                sdata=site_url+parsed['data'][i]  ### wrong ????
                url=build_url({'mode':'series', 'sname':sname, 'sdata':sdata, 'slink':slink, 'sid':sid})
                add_link(url,sname,sid,True)
            endoflist()

elif mode[0] == 'browse':
    '''
    foldername = args['foldername'][0]
    url = 'http://localhost/some_video.mkv'
    li = xbmcgui.ListItem(foldername + ' Video', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)
    '''
    #log("Start browse")
    parse()
    #log("Looping")
    for ltrs,q in mysite.biglist.items():
        url=build_url({'mode':'letter', 'letter':ltrs, 'page':0})
        add_link(url,ltrs,0,True)
    endoflist()
    #log("End browse")

elif mode[0] == 'favs':
    renew=False
    if os.path.isfile(favs_url):
        page=get_file(favs_url)
        f=open(favs_url,'r')
        jfav=f.read()
        f.close()            
        fav=json.loads(jfav)
        for one in fav:
            #parsed=read_playlist(one['slink'])
            parsed=parse_playlist(one['slink'])
            #tots=len(parsed['playlist'])
            tots=len(parsed)
            if tots != one['total']:
                sname='[COLOR red]'+one['sname']+'[/COLOR]'
                renew=True
            else:
                sname=one['sname']
            url=build_url({'mode':'season', 'snum':one['sname'], 'link':one['slink'], 'sid':one['sid']})
            con_url=build_url({'mode':'delfav', 'snum':one['sname'], 'link':one['slink'], 'sid':one['sid']})
            add_link(url,sname,one['sid'],True,[('Delete','XBMC.RunPlugin('+con_url+')')])
            #print one
        #print fav        
    #else:
    endoflist()
    if renew:
        for one in fav:
            #parsed=read_playlist(one['slink'])
            parsed=parse_playlist(one['slink'])
            #tots=len(parsed['playlist'])
            tots=len(parsed)
            one['total']=tots
        jfav=json.dumps(fav,indent=4)
        f=open(favs_url,'w')
        f.write(jfav)
        f.close()

elif mode[0] == 'addfavs':
    sname=args['snum'][0]
    slink=args['link'][0]
    sid=args['sid'][0]
    fav=[]
    fnd=False
    #fav=[{'sname':sname,'slink':slink}]
    if not os.path.exists(os.path.dirname(favs_url)):
        os.makedirs(os.path.dirname(favs_url))
    if os.path.isfile(favs_url):
        f=open(favs_url,'r')
        jfav=f.read()
        f.close()            
        fav=json.loads(jfav)
    for k in fav:
        #print k
        #print(sid)
        #print(k['sid'])
        if k['sid']==sid:
            fnd=True
            #print "Found!"
    if fnd:
        dialog = xbmcgui.Dialog()
        dialog.ok("Error", "Season already in favorites")
    else:
        #parsed=read_playlist(slink)
        parsed=parse_playlist(slink)
        #tots=len(parsed['playlist'])
        tots=len(parsed)
        fav.append({'sname':sname,'slink':slink,'sid':sid,'total':tots})
        jfav=json.dumps(fav,indent=4)
        f=open(favs_url,'w')
        f.write(jfav)
        f.close()
    
elif mode[0] == 'delfav':
    sid=args['sid'][0]
    f=open(favs_url,'r')
    jfav=f.read()
    f.close()            
    fav=json.loads(jfav)
    #print fav.index('sid')
    z=-1
    i=0
    for k in fav:
        #print k
        if k['sid']==sid:
            #print "Found!"
            z=i
        i+=1
    if z>=0:
        fav.pop(z)
    jfav=json.dumps(fav,indent=4)
    f=open(favs_url,'w')
    f.write(jfav)
    f.close()
    xbmc.executebuiltin("Container.Refresh")

#          con_url=build_url({'mode':'delfav', 'snum':one['sname'], 'link':one['slink'], 'sid':one['sid']})


elif mode[0] == 'letter':
    #log("Start letter")
    parse()
    ltr=args['letter'][0]
    page=int(args['page'][0])
    ef=page*ipp
    el=(page+1)*ipp
    if page > 0:
        url=build_url({'mode':'letter', 'letter':ltr, 'page':0})
        add_link(url,"First page",0,True)
        url=build_url({'mode':'letter', 'letter':ltr, 'page':(page-1)})
        add_link(url,"Previous page - #"+str(page),0,True)
        
    epsds=sorted(mysite.biglist[ltr].items())
    pages=(len(epsds)/ipp)+(len(epsds)%ipp>0)-1

    for one in epsds[ef:el]:
        sname=one[0]
        sid=one[1]['id']
        slink=site_url+one[1]['link']
        url=build_url({'mode':'series', 'sname':sname, 'slink':slink, 'sid':sid})
        add_link(url,sname,sid,True)
    if page<pages:
        url=build_url({'mode':'letter', 'letter':ltr, 'page':(page+1)})
        add_link(url,"Next page - #"+str(page+2),0,True)
        url=build_url({'mode':'letter', 'letter':ltr, 'page':(pages)})
        add_link(url,"Last page - #"+str(pages+1),0,True)
    endoflist()
    #log("End letter")
elif mode[0] == 'series':
    #log("Start series")
    serurl=args['slink'][0]
    sid=args['sid'][0]
    page=get_site(serurl)
    sp=BeautifulSoup(page)
    ses=sp.body.find("div", {"class":"seasonlist"})
    for bl in ses.find_all("a"):
        snum=bl.text
        snum=snum.encode('utf-8')
        slink=site_url+bl['href']
        url=build_url({'mode':'season', 'snum':snum, 'link':slink, 'sid':sid})
        con_url=build_url({'mode':'addfavs', 'snum':snum, 'link':slink, 'sid':sid})
        add_link(url,snum,sid,True,[('Add to plugin favorites','XBMC.RunPlugin('+con_url+')')])
    endoflist()
    #log("End series")
elif mode[0] == 'season':
    #log("Start season")
    serurl=args['link'][0]
    serid=args['sid'][0]
    #parsed=read_playlist(serurl)
    parsed=parse_playlist(serurl)
    for one in parsed:
        #print one
        sname=one['comment']
        slink=one['file']
        add_link(slink,sname,serid)
#     for one in parsed['playlist']:
#         sname=one['comment']
#         slink=one['file']
#         add_link(slink,sname,serid)
    endoflist()
    #log("End season")
else:
    
    log("Error!!! unknown mode:")
    log(mode[0])
        
    
      
