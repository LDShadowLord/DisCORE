from bs4 import BeautifulSoup
import urllib3, requests, re

class BaseNovelProvider:
    def __init__(self, url):
        """
        Provides a base for all other classes.
        """
        #Fiction Namespace is generic details about the book and the website. This information is unlikely to change, and can be safely cached.
        #The only exception to this is if you are targeting a chapter, in which case the title will be replaced with the chapter information.
        self.fiction_url = url
        self.fiction_id = None
        self.fiction_provider = None
        self.fiction_title = None

        #Note that this is now seperate, but for historical reasons is still under the "fiction" namespace.
        self.fiction_author = None
        self.fiction_author_id = None
        self.fiction_author_url = None

        #Book Namespace is more specific details about the book and is transient information that can probably not be cached.
        self.book_chapters = None
        self.book_chapter_amount = None
        self.book_description = None
        self.book_genres = []
        self.book_cover_image = None
        self.book_is_active = None


class ScribbleHub(BaseNovelProvider):
    def __init__(self, url=None, is_chapter=False, only_chapter_info=False):
        """
        Scans a ScribbleHub Book or Chapter to Gather Information which is exposed in class variables beginning either 'fiction_' or 'book_' dependant on namespace
        'url' should be a Fully Qualified ScribbleHub URL pointing towards the book, not a chapter
        'is_chapter' is a boolean that only returns 'fiction' data when 'True'
        'only_chapter_info' is a boolean that only returns the list of chapters ('book_chapters') when 'True'
        """
        if not url.startswith("https://www.scribblehub.com/series/") and is_chapter == False:
            raise ValueError("Not a properly formatted ScribbleHub Book URL")
        elif not url.startswith("https://www.scribblehub.com/read/") and is_chapter == True:
            raise ValueError("Not a properly formatted ScribbleHub Chapter URL")

        BaseNovelProvider.__init__(self, url=url)
        self.fiction_provider = "ScribbleHub"
        self._author_regex = re.compile(r"<span property=\"name\"><a href=\"(?P<url>https://www\.scribblehub\.com/profile/(?P<id>\d+)/.+)\"><span class=\"auth_name_fic\">(?P<name>.+)</span></a></span>")
        if is_chapter == False:
            self.fiction_id = url.strip("https://www.scribblehub.com/series/").split("/")[0]
        else:
            self.fiction_id = url.strip("https://www.scribblehub.com/read/").split("-")[0]

        soup = BeautifulSoup(urllib3.PoolManager().request('GET', url).data, "html5lib")

        if only_chapter_info:
            self.chapters()
        elif is_chapter:
            self.fiction(soup, True)
        elif not is_chapter:
            self.fiction(soup, False)
            self.author(soup)
            self.book(soup)

    def author(self, soup):
        author = soup.find('span', attrs={'property': 'name'})
        
        if author == None or author == "":
            #Something has gone wrong somewhere, return None because we can't find the data.
            self.fiction_author = None
            self.fiction_author_id = None
            self.fiction_author_url = None
        else:
            #Do REGEX magic to pull the url, name, and ID.
            author_details = self._author_regex.match(str(author))
            self.fiction_author = author_details.group('name')
            self.fiction_author_id = author_details.group('id')
            self.fiction_author_url = author_details.group('url')

    def fiction(self, soup, is_chapter):
        if not is_chapter:
            self.fiction_title = soup.find('div', attrs={'class': 'fic_title'}).text.strip()
        else:
            self.fiction_title = soup.find('div', attrs={'class': 'chapter-title'}).text.strip()

    def book(self, soup):

        self.chapters()

        if not soup.find('div', attrs={'class': 'number font-red-sunglo'}):
            self.book_is_active = True
        else:
            self.book_is_active = False

        self.book_description = soup.find('div', attrs={'property': 'description'}).text.strip()

        self.book_cover_image = soup.find('img', attrs={'property': 'image'}).get('src')
        if self.book_cover_image == "undefined":
            self.book_cover_image = "/content/images/nocover-new-min.png"

        for tag in soup.findAll('span', attrs={'property': 'genre'}):
            self.book_genres.append(tag.text.strip())

    def chapters(self):
        payload = {
            "action":"wi_getreleases_pagination",
            "mypostid":self.fiction_id,
            "pagenum":"-1"
            }
        soup = BeautifulSoup(requests.post("https://www.scribblehub.com/wp-admin/admin-ajax.php", data=payload).text, "html5lib")
        self.book_chapters = [
            tag['href'] for tag in soup.findAll('a', attrs={'class': 'toc_a'}, href=True)
            ]

        self.book_chapters.reverse()
        self.book_chapter_amount = len(self.book_chapters)

class RoyalRoad(BaseNovelProvider):
    def __init__(self, url=None, is_chapter=False, only_chapter_info=False):
        """
        Scans a RoyalRoad Book or Chapter to Gather Information which is exposed in class variables beginning either 'fiction_' or 'book_' dependant on namespace
        'url' should be a Fully Qualified RoyalRoad URL
        'is_chapter' is a boolean that only returns 'fiction' data when 'True'
        'only_chapter_info' is a boolean that only returns the list of chapters ('book_chapters') when 'True'
        """
        if not url.startswith("https://www.royalroad.com/fiction/"):
            raise ValueError("Not a properly formatted RoyalRoad URL")

        BaseNovelProvider.__init__(self, url=url)
        self.fiction_provider = "RoyalRoad"
        self._author_regex = re.compile(r"<span property=\"name\"><a href=\"(?P<url_uq>\/profile\/(?P<id>\d+))\" class=\"font-white\">(?P<name>.+)<\/a><\/span>")

        soup = BeautifulSoup(urllib3.PoolManager().request('GET', url).data, "html5lib")

        if only_chapter_info:
            self.chapters(soup)
        elif is_chapter:
            self.fiction(soup)
        elif not is_chapter:
            self.fiction(soup)
            self.author(soup)
            self.book(soup)

    def author(self, soup):
        author = soup.find('span', attrs={'property': 'name'})
        
        if author == None or author == "":
            #Something has gone wrong somewhere, return None because we can't find the data.
            self.fiction_author = None
            self.fiction_author_id = None
            self.fiction_author_url = None
        else:
            #Do REGEX magic to pull the url, name, and ID.
            author_details = self._author_regex.match(str(author))
            self.fiction_author = author_details.group('name')
            self.fiction_author_id = author_details.group('id')
            self.fiction_author_url = "https://www.royalroad.com" + author_details.group('url_uq')

    def fiction(self, soup):
        self.fiction_id = (self.fiction_url).strip("https://www.royalroad.com/fiction/").split("/")[0]
        self.fiction_title = soup.find('h1', attrs={'class': 'font-white'}).text.strip()

    def book(self, soup):

        self.chapters(soup)

        if not soup.find('div', attrs={'class': 'number font-red-sunglo'}):
            self.book_is_active = True
        else:
            self.book_is_active = False

        self.book_description = soup.find('div', attrs={'property': 'description'}).text.strip()

        self.book_cover_image = soup.find('img', attrs={'property': 'image'}).get('src')
        if self.book_cover_image == "undefined":
            self.book_cover_image = "/content/images/nocover-new-min.png"

        for tag in soup.findAll('span', attrs={'class': 'label label-default label-sm bg-blue-hoki'}):
            self.book_genres.append(tag.text.strip())
        for tag in soup.findAll('a', attrs={'property': 'genre'}):
            self.book_genres.append(tag.text.strip())

    def chapters(self, soup):
        book_chapters = [
            tag.get("data-url") for tag in soup.findAll('tr', attrs={'style': 'cursor: pointer'})
        ]
        if len(book_chapters) > 0:
            self.book_chapters = []
            for item in book_chapters:
                self.book_chapters.append("https://www.royalroad.com"+item)

            self.book_chapter_amount = len(self.book_chapters)