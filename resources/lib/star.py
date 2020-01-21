# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import json, re

from youtube_resolver import resolve as yt_resolver
from tulip import bookmarks, directory, client, cache, youtube, control
from tulip.compat import urlparse, iteritems, OrderedDict


class Indexer:

    def __init__(self):

        self.list = []; self.data = []; self.groups = []
        self.stargr_link = 'http://www.star.gr'
        self.starx_link = 'https://www.starx.gr'
        self.startv_link = ''.join([self.stargr_link, '/tv/'])
        self.star_video_link = ''.join([self.stargr_link, '/video'])
        self.starx_latest_link = ''.join([self.starx_link, '/latest'])
        self.starx_viral_link = ''.join([self.starx_link, '/viral'])
        self.starx_popular_link = ''.join([self.starx_link, '/popular'])
        self.starx_shows_link = ''.join([self.starx_link, '/shows'])
        self.ajax_player = ''.join([self.startv_link, 'ajax/Atcom.Sites.StarTV.Components.Show.PopupSliderItems'])
        self.player_query = '&'.join(
            [
                'showid={show_id}', 'type=Episode', 'itemIndex={item_index}', 'seasonid={season_id}', 'single=false'
            ]
        )
        self.m3u8_link = 'https://cdnapisec.kaltura.com/p/713821/sp/0/playManifest/entryId/{0}/format/applehttp/protocol/https/flavorParamId/0/manifest.m3u8'
        self.live_link = self.m3u8_link.format('1_fp7fyi3j')
        self.youtube_key = 'AIzaSyBOS4uSyd27OU0XV2KSdN3vT2UG_v0g9sI'
        self.youtube_link = 'UCwUNbp_4Y2Ry-asyerw2jew'

    def root(self):

        self.list = [
            {
                'title': control.lang(32009),
                'action': 'play',
                'isFolder': 'False',
                'url': self.live_link,
                'icon': 'live.png'
            }
            ,
            {
                'title': control.lang(32003),
                'action': 'startv',
                'icon': 'tvshows.png'
            }
            ,
            {
                'title': control.lang(32007),
                'action': 'videos',
                'icon': 'videos.png'
            }
            ,
            {
                'title': control.lang(32008),
                'action': 'starx',
                'icon': 'starx.png'
            }
            ,
            {
                'title': control.lang(32010),
                'action': 'news',
                'icon': 'news.png'
            }
            ,
            {
                'title': control.lang(32002),
                'action': 'archive',
                'icon': 'archive.png'
            }
            ,
            {
                'title': control.lang(32006),
                'action': 'bookmarks',
                'icon': 'bookmarks.png'
            }
        ]

        for item in self.list:
            cache_clear = {'title': 30403, 'query': {'action': 'cache_clear'}}
            item.update({'cm': [cache_clear]})

        directory.add(self.list)

    def bookmarks(self):

        self.list = bookmarks.get()

        if self.list is None:
            self.list = [{'title': 'N/A', 'action': None}]
            directory.add(self.list)
            return

        for i in self.list:
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['delbookmark'] = i['url']
            i.update({'cm': [{'title': 32502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list)

    def archive(self):

        self.list = cache.get(youtube.youtube(key=self.youtube_key).playlists, 24, self.youtube_link)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'youtube'})
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        control.sortmethods('title')

        directory.add(self.list)

    def youtube(self, url):
    
        self.list = cache.get(youtube.youtube(key=self.youtube_key).playlist, 1, url)

        if self.list is None:
            return

        for i in self.list: i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list)

    def index(self):

        html = client.request(self.startv_link)

        divs = client.parseDOM(html, 'div', {'class': 'wrapper'})[3:6]

        htmls = '\n'.join(divs)

        items = client.parseDOM(htmls, 'div', attrs={'class': 'tileRow'})

        for item in items:

            title = client.parseDOM(item, 'b')[0]
            title = client.replaceHTMLCodes(title)
            url = client.parseDOM(item, 'a', attrs={'class': 'tile_title'}, ret='href')[0]
            try:
                image = client.parseDOM(item, 'div', attrs={'data-tile-img': 'background-image:.+'}, ret='style')[0]
            except IndexError:
                image = client.parseDOM(item, 'div', attrs={'data-tile-img': 'background-image:.+'}, ret='data-grid-img')[0]
            image = re.search(r'(http.+?\.jpg)', image).group(1)
            group = urlparse(url).path.split('/')[2]

            self.list.append({'title': title, 'image': image, 'url': url, 'group': group})

        return self.list

    def listing(self, url):

        html = client.request(url)

        content = client.parseDOM(html, 'div', attrs={'class': 'seasons'})[0]

        items = client.parseDOM(content, 'li', attrs={'class': 'horizontal-cell.+?'})

        for i in items:

            try:
                title = client.replaceHTMLCodes(client.parseDOM(i, 'a', ret='data-title')[0])
            except Exception:
                break
            try:
                image = client.parseDOM(i, 'img', ret='src')[0]
            except IndexError:
                image = client.parseDOM(i, 'img', ret='data-src')[0]

            show_id = client.parseDOM(i, 'a', ret='data-showid')[0]
            season_id = client.parseDOM(i, 'a', ret='data-seasonid')[0]
            index_id = client.parseDOM(i, 'a', ret='data-index')[0]
            url = '?'.join([self.ajax_player, self.player_query.format(show_id=show_id, item_index=index_id, season_id=season_id)])
            sep = client.parseDOM(i, 'a', ret='href')[0]
            group = client.replaceHTMLCodes(
                client.stripTags(client.parseDOM(html.partition(sep.encode('utf-8'))[0], 'h3')[-1])
            )

            self.data.append(group)
            self.list.append({'title': title, 'image': image, 'url': url, 'group': group})

        self.groups = list(OrderedDict.fromkeys(self.data))

        return self.list, self.groups

    def show(self, url):

        self.list, self.groups = cache.get(self.listing, 1, url)

        if self.list is None:
            return

        try:
            self.list = [i for i in self.list if i['group'] == self.groups[int(control.setting('group'))]]
        except IndexError:
            control.setSetting('group', '0')

        for i in self.list:
            i.update({'action': 'play', 'isFolder': 'False'})

        try:
            title = u''.join([control.lang(32005), u': {0}'.format(self.groups[int(control.setting('group'))])])
        except IndexError:
            try:
                title = u''.join([control.lang(32005), u': {0}'.format(self.groups[0])])
            except Exception:
                return

        selector = {
            'title': title,
            'action': 'selector',
            'icon': 'selector.png',
            'isFolder': 'False',
            'isPlayable': 'False',
            'query': json.dumps(self.groups)
        }

        self.list.insert(0, selector)

        directory.add(self.list)

    def startv(self):

        self.list = cache.get(self.index, 12)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'show'})
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        option = control.setting('option')

        selector = {
            'title': u''.join([control.lang(32005), u': {0}'.format(control.lang(self.vod_groups()[option]))]),
            'action': 'selector',
            'icon': 'selector.png',
            'isFolder': 'False',
            'isPlayable': 'False'
        }

        self.list = [i for i in self.list if i['group'] == option]

        self.list.insert(0, selector)

        directory.add(self.list)

    def _videos(self):

        html = client.request(self.star_video_link)

        items = client.parseDOM(html, 'div', attrs={'class': 'video__title'})

        for i in items:

            title = client.parseDOM(i, 'a', attrs={'style': 'color.+?'})[0]
            url = client.parseDOM(i, 'a', attrs={'style': 'color.+?'}, ret='href')[0]

            self.list.append({'title': title, 'url': url})

        return self.list

    def videos(self):

        self.list = cache.get(self._videos, 12)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'category'})
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list)

    def _category(self, url):

        html = client.request(url)

        content = client.parseDOM(html, 'div', attrs={'class': 'block block--no-space'})[0]

        items = client.parseDOM(content, 'div', attrs={'style': 'margin-bottom:20px;'})

        try:
            next_url = client.parseDOM(html, 'a', {'rel': 'next'}, ret='href')[0]
        except Exception:
            next_url = ''

        for i in items:

            title = client.parseDOM(i, 'div', attrs={'class': 'title'})[0].strip()
            title = client.replaceHTMLCodes(title)
            url = client.parseDOM(i, 'a', ret='href')[0]
            if not url.startswith('http'):
                url = ''.join([self.stargr_link, url])
            image = client.parseDOM(i, 'img', ret='src')[0]

            self.list.append({'title': title, 'image': image, 'url': url, 'next': next_url})

        return self.list

    def category(self, url):

        self.list = cache.get(self._category, 1, url)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'play', 'isFolder': 'False', 'nextlabel': 32500, 'nextaction': 'category'})

        directory.add(self.list)

    def starx(self):

        self.list = [
            {
                'title': u''.join([control.lang(32008), ': ', control.lang(32004)]),
                'url': self.starx_latest_link,
                'icon': 'starx.png',
                'action': 'starx_videos'
            }
            ,
            {
                'title': u''.join([control.lang(32008), ': ', control.lang(32013)]),
                'url': self.starx_viral_link,
                'icon': 'starx.png',
                'action': 'starx_videos'
            }
            ,
            {
                'title': u''.join([control.lang(32008), ': ', control.lang(32014)]),
                'url': self.starx_popular_link,
                'icon': 'starx.png',
                'action': 'starx_videos'
            }
            ,
            {
                'title': u''.join([control.lang(32008), ': ', control.lang(32012)]),
                'icon': 'starx.png',
                'action': 'starx_shows'
            }
        ]

        directory.add(self.list)

    def news(self):

        self.list = [
            {
                'title': 32018,
                'action': 'show',
                'icon': 'news.png',
                'url': 'https://www.star.gr/tv/enimerosi/mesimeriano-deltio-eidiseon/'
            }
            ,
            {
                'title': 32019,
                'action': 'show',
                'icon': 'news.png',
                'url': 'https://www.star.gr/tv/enimerosi/kedriko-deltio-eidiseon/'
            }
            ,
            {
                'title': 32022,
                'action': 'show',
                'icon': 'news.png',
                'url': 'https://www.star.gr/tv/enimerosi/kentriko-deltio-eidiseon-sabbatokuriakou/'
            }
            ,
            {
                'title': 32020,
                'action': 'show',
                'icon': 'sign.png',
                'url': 'https://www.star.gr/tv/enimerosi/apogeumatino-deltio-eidiseon/'
            }
            ,
            {
                'title': 32021,
                'action': 'show',
                'icon': 'weather.png',
                'url': 'https://www.star.gr/tv/enimerosi/star-kairos/'
            }
        ]

        directory.add(self.list)

    def _starx_videos(self, url, title):

        try:
            title = title.decode('utf-8')
        except Exception:
            pass

        html = client.request(url)

        if 'javascript:void(0)' in html and 'rel="more"' in html:

            items = json.loads(re.search('var episodes = (.+?);', html).group(1))

            episodes = list(range(1, len(items) + 1))[::-1]

            for i, e in zip(items, episodes):

                try:
                    label = u''.join([title, ' - ', control.lang(32016), str(e), '[CR][I]', i['title'], '[/I]'])
                except Exception:
                    label = u''.join([title, ' - ', control.lang(32016), str(e)])
                image = self.thumb_maker(i['video_id'])
                url = i['video_id']

                data = {'title': label, 'url': url, 'image': image}

                if i['kaltura_id']:
                    data.update({'query': i['kaltura_id']})

                self.list.append(data)

        else:

            items = client.parseDOM(html, 'div', attrs={'class': 'video-.+?'})

            try:
                next_url = client.parseDOM(html, 'a', attrs={'rel': 'next'}, ret='href')[0]
            except Exception:
                next_url = ''

            for i in items:

                title = client.parseDOM(i, 'span', attrs={'class': 'name'})[0]
                title = client.replaceHTMLCodes(title)
                url = html.partition(i.encode('utf-8'))[0]
                url = client.parseDOM(url, 'a', ret='href')[-1]
                image = client.parseDOM(i, 'img', attrs={'class': 'lozad'}, ret='src')[0]
                if image == 'https://www.starx.gr/images/1x1.png':
                    image = client.parseDOM(i, 'img', attrs={'class': 'lozad'}, ret='data-src')[0]

                self.list.append({'title': title, 'url': url, 'image': image, 'next': next_url})

        return self.list

    def starx_videos(self, url, title):

        self.list = cache.get(self._starx_videos, 1, url, title)

        if self.list is None:
            return

        for i in self.list:

            i.update({'action': 'play', 'isFolder': 'False'})

            if 'next' in i:
                i.update({'nextlabel': 32500, 'nextaction': 'starx_videos'})

        directory.add(self.list)

    def _starx_shows(self):

        html = client.request(self.starx_shows_link)

        items = client.parseDOM(html, 'div', attrs={'class': 'video-.+?'})

        for i in items:

            title = client.parseDOM(i, 'span', attrs={'class': 'name'})[0]
            url = html.partition(i.encode('utf-8'))[0]
            url = client.parseDOM(url, 'a', ret='href')[-1]
            image = client.parseDOM(i, 'img', ret='data-src')[0]

            self.list.append({'title': title, 'url': url, 'image': image})

        return self.list

    def starx_shows(self):

        self.list = cache.get(self._starx_shows, 12)

        if self.list is None:
            return

        for i in self.list:
            i.update({'action': 'starx_videos'})
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list)

    def play(self, url, query=None):

        if url == self.live_link or url == 'wkFF9llFqRs':
            meta = {'title': 'Star TV'}
            icon = control.icon()
        else:
            meta = None
            icon = None

        if len(url) == 11:

            try:
                stream = self.yt_session(url)
                directory.resolve(stream, dash=stream.endswith('.mpd'))
                return
            except Exception:
                return self.play(query)

        elif len(url) == 10:

            url = self.m3u8_link.format(url)

        elif url.startswith('plugin://'):

            return self.play(url[-11:])

        elif 'Atcom.Sites' in url or '/video/' in url:

            html = client.request(url)

            try:

                url = re.search(r'url: ["\'](.+?)["\']', html).group(1)

            except AttributeError:

                url = self.m3u8_link.format(re.search(r'kaltura-player(\w+)', html).group(1))

        elif '/episode/' in url:

            html = client.request(url)

            url = self.m3u8_link.format(re.search(r'kalturaPlayer\(["\'](\w+)["\']', html).group(1))

        elif '/viral/' in url or '/popular/' in url:

            html = client.request(url)

            yt_id = re.search(r'onYouTubeIframeAPIReady\(["\']([\w-]{11})["\']\);', html).group(1)

            return self.play(yt_id)

        elif url == self.live_link and int(client.request(url, output='response', error=True)[0]) == 404:

            return self.play('wkFF9llFqRs')

        try:

            addon_enabled = control.addon_details('inputstream.adaptive').get('enabled')

        except KeyError:

            addon_enabled = False

        version = int(control.infoLabel('System.AddonVersion({0})'.format('xbmc.python')).replace('.', ''))

        dash = addon_enabled and version >= 2260

        if dash:

            directory.resolve(
                url, meta=meta, icon=icon, dash=True, manifest_type='hls', mimetype='application/vnd.apple.mpegurl'
            )

        else:

            directory.resolve(url, meta=meta, icon=icon)

    @staticmethod
    def thumb_maker(video_id):

        return 'http://img.youtube.com/vi/{0}/{1}.jpg'.format(video_id, 'mqdefault')

    @staticmethod
    def yt_session(yt_id):

        streams = yt_resolver(yt_id)

        try:
            addon_enabled = control.addon_details('inputstream.adaptive').get('enabled')
        except KeyError:
            addon_enabled = False

        if not addon_enabled:
            streams = [s for s in streams if 'mpd' not in s['title'].lower()]

        stream = streams[0]['url']

        return stream

    @staticmethod
    def vod_groups():

        return OrderedDict(
            [
                ('enimerosi', 32010), ('psychagogia', 32011), ('seires', 32012)
            ]
        )

    def selector(self, query=None):

        if query:

            query = json.loads(query)

            choice = control.selectDialog(query, control.lang(32017))

            if choice != -1:
                control.setSetting('group', str(choice))

        else:

            choices = [control.lang(i) for i in list(self.vod_groups().values())]

            groups = list(self.vod_groups().keys())

            choice = control.selectDialog(choices, control.lang(32003))

            option = groups[choice]

            if choice != -1:
                control.setSetting('option', option)

        if choice != -1:
            control.sleep(200)
            control.refresh()
