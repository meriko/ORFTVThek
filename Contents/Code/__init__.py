TITLE  = 'ORF TVThek'
PREFIX = '/video/orftvthek'

BASE_URL = 'http://tvthek.orf.at/'

ART   = "art-default.jpg"
THUMB = 'icon-default.png'

PREDEFINED_CHOICES = [ 
    {
        'title':    unicode('Neueste Sendungen'),
        'url':      BASE_URL + 'newest'
    },
    {
        'title':    unicode('Meist Gesehen'),
        'url':      BASE_URL + 'most_viewed'
    },
    {
        'title':    unicode('Sendungs Tipps'),
        'url':      BASE_URL + 'tips'
    }
]

###################################################################################################
def Start():
    DirectoryObject.thumb = R(THUMB)
    ObjectContainer.art   = R(ART)

    HTTP.CacheTime = 300 # 5 Minutes  

###################################################################################################
@handler(PREFIX, TITLE, thumb = THUMB, art = ART)
def MainMenu():
    oc = ObjectContainer(title1 = TITLE)
    
    if Client.Platform == 'Android':
        oc.header = unicode('Nicht unterstützt')
        oc.message = unicode('Dieser Kanal ist nicht auf Android unterstützt')
        
        return oc
    
    for choice in PREDEFINED_CHOICES:
        oc.add(
            DirectoryObject(
                key = 
                    Callback(
                        Items, 
                        name = choice['title'], 
                        url = choice['url']
                    ), 
                title = choice['title']
        )
    )

    title = 'Sendungen'
    oc.add(
        DirectoryObject(
            key = 
                Callback(
                    Programs, 
                    name = title, 
                    url = BASE_URL + 'programs'
                ), 
            title = title
        )
    )
    
    title = 'Themen'
    oc.add(
        DirectoryObject(
            key = 
                Callback(
                    Topics, 
                    name = title, 
                    url = BASE_URL + 'topics'
                ), 
            title = title
        )
    )

    title = 'Live'
    oc.add(
        DirectoryObject(
            key = 
                Callback(
                    LiveStreams, 
                    name = title, 
                    url = BASE_URL + 'live'
                ), 
            title = title
        )
    )
    
    title = 'Sendung Verpasst'
    oc.add(
        DirectoryObject(
            key = 
                Callback(
                    Schedule, 
                    name = title, 
                    url = BASE_URL + 'schedule'
                ), 
            title = title
        )
    )
    
    title = 'Archiv'
    oc.add(
        DirectoryObject(
            key = 
                Callback(
                    Archive, 
                    name = title, 
                    url = BASE_URL + 'archive'
                ), 
            title = title
        )
    )
    
    title = 'Suche'
    oc.add(
        InputDirectoryObject(
            key = 
                Callback(Search, name = title),
                title = title, 
                prompt = title
        )
    )
    
    return oc

###################################################################################################
@route(PREFIX + '/Search')
def Search(query, name):
    oc = ObjectContainer(title2 = unicode(name))
    
    searchURL = BASE_URL + 'search?q=' + String.Quote(query)
    
    programs = Program(name = unicode(query), url = searchURL)
    for program in programs.objects:
        oc.add(program)
    
    videos = Items(name = unicode(query), url = searchURL)
    for video in videos.objects:
        oc.add(video)
        
    if len(oc) > 0:
        return oc
    else:
        oc = ObjectContainer(title2 = unicode(query))
        oc.header = unicode('Ihre Suche ergab keine Treffer')
        oc.message = unicode('Unter Ihrem Suchbegriff wurden leider keine Sendungen bzw. Beiträge gefunden. Bitte verwenden Sie andere oder verwandte Begriffe bzw. vereinfachen Sie Ihre Suche.')
        
        return oc

###################################################################################################
@route(PREFIX + '/Programs')
def Programs(name, url):
    oc = ObjectContainer(title2 = unicode(name))

    title = 'A-Z'
    oc.add(
        DirectoryObject(
            key = 
                Callback(
                    ProgramByLetter, 
                    name = title, 
                    url = url
                ), 
            title = title
        )
    )
    
    title = 'Kategorien'
    oc.add(
        DirectoryObject(
            key = 
                Callback(
                    Categories, 
                    name = title, 
                    url = url
                ), 
            title = title
        )
    )
    
    return oc

###################################################################################################
@route(PREFIX + '/ProgramByLetter')
def ProgramByLetter(name, url):
    oc = ObjectContainer(title2 = unicode(name))
    
    pageElement = HTML.ElementFromURL(url)
    
    for item in pageElement.xpath("//*[contains(@class,'mod_name_list')]//*[@class = 'base_list_item']"):
        url   = item.xpath(".//a/@href")[0]
        title = item.xpath(".//h4/text()")[0]
        
        oc.add(
            DirectoryObject(
                key = 
                    Callback(
                        Program, 
                        name = title, 
                        url = url
                    ), 
                title = title
            )
        )
    
    return oc    
          
###################################################################################################
@route(PREFIX + '/Program')
def Program(name, url):
    oc = ObjectContainer(title2 = unicode(name))
    
    pageElement = HTML.ElementFromURL(url)
    
    titles = []
    
    for item in pageElement.xpath("//*[contains(@class,'results_item')]"):
        title = item.xpath(".//h4/text()")[0]
        
        if title in titles:
            continue
        
        try:
            thumb = item.xpath(".//img/@src")[0]
        except:
            # Shows that do not have an image does not contain any content
            continue
        
        episodes = Episodes(title, url, thumb)
        
        if len(episodes) == 1:
            oc.add(
                episodes.objects[0]
            )
        
        elif len(episodes) > 1:
            oc.add(
                DirectoryObject(
                    key = 
                        Callback(
                            Episodes, 
                            name = title, 
                            url = url,
                            image = thumb
                        ), 
                    title = title,
                    thumb = thumb
                )
            )
            
            titles.append(title)
    
    return oc       
    
###################################################################################################
@route(PREFIX + '/Episodes')
def Episodes(name, url, image):
    oc = ObjectContainer(title2 = unicode(name))
    
    pageElement = HTML.ElementFromURL(url)
    
    urls = []
    
    for item in pageElement.xpath("//*[contains(@class,'results_item')]"):
        title = item.xpath(".//h4/text()")[0]
        
        if not title == name:
            continue
        
        for episode in item.xpath(".//*[contains(@class,'base_list_item')]"):
            try:
                url = episode.xpath(".//a/@href")[0]
            except:
                continue
                
            if url in urls:
                continue

            try:
                originally_available_at = Datetime.ParseDate(episode.xpath(".//*[@class = 'meta meta_date']/text()")[0].split(" ")[1]).date()
            except:
                continue

            try:
                summary = unicode(episode.xpath(".//*[@class = 'item_description']/text()")[0].strip())
            except:
                summary = None
                
            try:
                thumb = episode.xpath(".//a//img/@src")[0]
                if not thumb.startswith("http"):
                    thumb = BASE_URL + '/' + thumb
            except:
                thumb = image
    
            try:
                durationString = episode.xpath(".//*[@class = 'meta meta_duration']/text()")[0]
                
                hours   = 0
                minutes = 0
                seconds = 0
                
                if 'min' in durationString.lower():
                    minutes = int(durationString.split(" ")[0].split(":")[0])
                    seconds = int(durationString.split(" ")[0].split(":")[1])
                else:
                    hours = int(durationString.split(" ")[0].split(":")[0])
                    minutes = int(durationString.split(" ")[0].split(":")[1])
                    
                duration = (hours * 3600 + minutes * 60 + seconds) * 1000
                
            except:
                duration = None
            
            oc.add(
                VideoClipObject(
                    url = url,
                    title = title,
                    summary = summary,
                    thumb = thumb,
                    duration = duration,
                    originally_available_at = originally_available_at
                )
            )
            
            urls.append(url)
    
    return oc 
  
###################################################################################################
@route(PREFIX + '/Categories')
def Categories(name, url):
    oc = ObjectContainer(title2 = unicode(name))
    
    pageElement = HTML.ElementFromURL(url)
    
    for item in pageElement.xpath("//*[contains(@class,'mod_genre_list')]//*[contains(@class,'base_list_item')]"):
        try:
            url = item.xpath(".//a/@href")[0]
        except:
            continue
            
        title = item.xpath(".//h4/text()")[0]
        
        oc.add(
            DirectoryObject(
                key = 
                    Callback(
                        Program, 
                        name = title, 
                        url = url
                    ), 
                title = title
            )
        )
    
    return oc 

###################################################################################################
@route(PREFIX + '/Topics')
def Topics(name, url):
    oc = ObjectContainer(title2 = unicode(name))

    pageElement = HTML.ElementFromURL(url)
    
    for item in pageElement.xpath("//section[@class = 'item_wrapper']"):
        url   = item.xpath(".//footer//a/@href")[0]
        title = unicode(item.xpath(".//h3/text()")[0].strip())
        
        oc.add(
            DirectoryObject(
                key = 
                    Callback(
                        Items, 
                        name = title, 
                        url = url
                    ), 
                title = title
            )
        )
    
    return oc
 
###################################################################################################
@route(PREFIX + '/Schedule')
def Schedule(name, url):
    oc = ObjectContainer(title2 = unicode(name))
    
    pageElement = HTML.ElementFromURL(url)
    
    for item in pageElement.xpath("//*[contains(@class,'slider_list')]//*[contains(@class,'slider_list_item')]"):
        url   = item.xpath(".//a/@href")[0]
        title = unicode(item.xpath(".//strong/text()")[0] + ' '  + item.xpath(".//small/text()")[0])
        
        oc.add(
            DirectoryObject(
                key = 
                    Callback(
                        Items, 
                        name = title, 
                        url = url,
                        useImage = 1,
                        dateinfo = title
                    ), 
                title = title
            )
        )
    
    oc.objects.reverse()    
    oc.objects[0].title = 'Heute'
    oc.objects[1].title = 'Gestern'
    oc.objects[2].title = 'Vorgestern'
    
    return oc  
  
###################################################################################################
@route(PREFIX + '/Archive')
def Archive(name, url):
    oc = ObjectContainer(title2 = unicode(name))

    title = 'Alle Archive'
    oc.add(
        DirectoryObject(
            key = 
                Callback(
                    Items, 
                    name = title, 
                    url = url,
                    video = False
                ), 
            title = title
        )
    )

    pageElement = HTML.ElementFromURL(url)

    for item in pageElement.xpath("//*[@class = 'base_list_item']"): 
        url   = item.xpath(".//a/@href")[0]
        title = unicode(item.xpath(".//h4/text()")[0].strip())
        
        oc.add(
            DirectoryObject(
                key = 
                    Callback(
                        Items, 
                        name = title, 
                        url = url,
                        video = False
                    ), 
                title = title
            )
        )
    
    return oc

###################################################################################################
@route(PREFIX + '/LiveStreams')
def LiveStreams(name, url):
    oc = ObjectContainer(title2 = unicode(name))

    pageElement = HTML.ElementFromURL(url)
    
    for channel in pageElement.xpath("//*[contains(@class,'program')]"):
        try:
            thumb = channel.xpath(".//img/@src")[0]
            if not thumb.startswith("http"):
                thumb = BASE_URL + '/' + thumb
        except:
            thumb = None
        
        for program in channel.xpath(".//*[@class = 'base_list_item']"):            
            url     = program.xpath(".//a/@href")[0]
            summary = program.xpath(".//*[@class = 'meta meta_time']/text()")[0] + '\r\n\r\n' + unicode(program.xpath(".//h4/text()")[0].strip())
    
            try:
                title = channel.xpath(".//img/@alt")[0].split("Logo von")[1].strip()
            except:
                title = None
    
            oc.add(
                VideoClipObject(
                    url = url,
                    title = title,
                    thumb = thumb,
                    summary = summary
                )
            )
            
            break
            
    return oc
    
###################################################################################################
@route(PREFIX + '/Items', video = bool, useImage = int)
def Items(name, url, video = True, useImage = 0, dateinfo = ''):
    oc = ObjectContainer(title2 = unicode(name))
    
    pageElement = HTML.ElementFromURL(url)
    
    for item in pageElement.xpath("//article[contains(@class,'item')]"): 
        url = item.xpath(".//a/@href")[0]
        
        title = unicode(item.xpath(".//*[@class = 'item_title']/text()")[0].strip())

        if video:
            if dateinfo:
                try:
                    day   = dateinfo.split(" ")[1].split(".")[0]
                    month = dateinfo.split(" ")[1].split(".")[1]
                    year  = dateinfo.split(" ")[1].split(".")[2]
                    
                    originally_available_at = Datetime.ParseDate(year + '-' + month + '-' + day).date()
                except:
                    originally_available_at = None
            else:
                try:
                    originally_available_at = Datetime.ParseDate(item.xpath(".//*[@class = 'meta meta_date']/text()")[0].split(" ")[1]).date()
                except:
                    continue
        else:
            originally_available_at = None  
        
        try:
            description = unicode(item.xpath(".//*[@class = 'item_description']/text()")[0].strip())
        except:
            description = ''

        if not dateinfo:
            try:
                dateinfo = item.xpath(".//*[@class = 'meta meta_date']/text()")[0]
            except:
                dateinfo = ''

        try:
            timeinfo = item.xpath(".//*[@class = 'meta meta_time']/text()")[0]
        except:
            timeinfo = ''

        try:
            channelinfo = item.xpath(".//a//img/@alt")[0].strip().split('Logo zu')[1]
        except:
            channelinfo = '' 
        
        summary = channelinfo + ' ' + dateinfo + ' ' + timeinfo 
        summary = summary.strip()
        summary = summary + '\r\n\r\n' + description
            
        try:
            thumb = item.xpath(".//a//img/@src")[useImage]
            if not thumb.startswith("http"):
                thumb = BASE_URL + '/' + thumb
        except:
            thumb = None

        try:
            durationString = item.xpath(".//*[@class = 'meta meta_duration']/text()")[0]
            
            hours   = 0
            minutes = 0
            seconds = 0
            
            if 'min' in durationString.lower():
                minutes = int(durationString.split(" ")[0].split(":")[0])
                seconds = int(durationString.split(" ")[0].split(":")[1])
            else:
                hours = int(durationString.split(" ")[0].split(":")[0])
                minutes = int(durationString.split(" ")[0].split(":")[1])
                
            duration = (hours * 3600 + minutes * 60 + seconds) * 1000
            
        except:
            duration = None
        
        if video:
            oc.add(
                VideoClipObject(
                    url = url,
                    title = title,
                    summary = summary,
                    thumb = thumb,
                    duration = duration,
                    originally_available_at = originally_available_at
                )
            )
        else:
            oc.add(
                DirectoryObject(
                    key =
                        Callback(
                            Items,
                            name = title,
                            url = url,
                            video = True
                        ),
                    title = unicode(title),
                    summary = unicode(summary),
                    thumb = thumb
                )
            )       
    
    for item in pageElement.xpath("//*[@class='pager_list']//*[contains(@class,'pager_item next')]"):
        oc.add(
            NextPageObject(
                key = 
                    Callback(
                        Items,
                        name = name,
                        url = item.xpath(".//a/@href")
                    ),
                title = unicode("Vor...")
            )
        )
        break
    
    return oc