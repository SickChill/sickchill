import attr


@attr.s
class Image(object):
    url = attr.ib()
    width = attr.ib()
    height = attr.ib()


class TitleEpisodes(object):

    def __init__(self, facade, imdb_id):
        self._facade = facade
        episodes = self._facade._client.get_title_episodes(
            imdb_id=imdb_id
        )
        self._episode_imdb_ids = []
        for season in episodes['seasons']:
            for episode in season['episodes']:
                imdb_id = self._facade._parse_id(episode['id'])
                self._episode_imdb_ids.append(imdb_id)
        self._count = len(self._episode_imdb_ids)

    def __len__(self):
        return self._count

    def __bool__(self):
        return self._count > 0

    def __getitem__(self, index):
        imdb_id = self._episode_imdb_ids[index]
        return self._facade.get_title(imdb_id=imdb_id)


@attr.s
class Title(object):
    imdb_id = attr.ib()
    title = attr.ib()
    type = attr.ib()
    certification = attr.ib()
    year = attr.ib()
    genres = attr.ib()
    writers = attr.ib()
    creators = attr.ib()
    credits = attr.ib()
    directors = attr.ib()
    stars = attr.ib()
    image = attr.ib()
    episodes = attr.ib()
    rating_count = attr.ib(default=0)
    releases = attr.ib(default=())
    season = attr.ib(default=None)
    episode = attr.ib(default=None)
    rating = attr.ib(default=None)
    plot_outline = attr.ib(default=None)
    release_date = attr.ib(default=None)
    runtime = attr.ib(default=None)

    def __repr__(self):
        return 'Title(imdb_id={0}, title={1})'.format(self.imdb_id, self.title)


@attr.s
class TitleSearchResult(object):
    imdb_id = attr.ib()
    title = attr.ib()
    type = attr.ib()
    year = attr.ib()


@attr.s
class NameSearchResult(object):
    imdb_id = attr.ib()
    name = attr.ib()


@attr.s
class TitleRelease(object):
    date = attr.ib()
    region = attr.ib()


@attr.s
class TitleName(object):
    name = attr.ib()
    category = attr.ib()
    imdb_id = attr.ib()
    job = attr.ib(default=None)
    characters = attr.ib(default=())


@attr.s
class Name(object):
    name = attr.ib()
    imdb_id = attr.ib()
    image = attr.ib()
    birth_place = attr.ib()
    gender = attr.ib()
    bios = attr.ib()
    date_of_birth = attr.ib()
    filmography = attr.ib()
