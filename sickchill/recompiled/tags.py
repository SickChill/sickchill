import re

# Resolutions
resolution = [
    re.compile(r"(?P<vres>4320|2160|1080|720|480|360)(?P<scan>[pi])", re.I),
    re.compile(r"(:?[sph]d)(:?.?tv)?[ \-_\.]*(?P<vres>4320|2160|1080|720|480|360)(:?(?P<scan>[pi])|[^\d]|$)", re.I),
]

# Sources
tv = re.compile(r"([sph]d).?tv|tv(rip|mux)", re.I)
dvd = re.compile(r"(?P<hd>hd)?dvd(?P<rip>rip|mux)?", re.I)
web = re.compile(r"(web(?P<type>rip|mux|hd|uhd|.?dl|\b))", re.I)
bluray = re.compile(r"(blue?-?ray|b[rd](?:rip|mux))", re.I)
sat = re.compile(r"(dsr|satrip)", re.I)
itunes = re.compile(r"itunes(hd|uhd)?", re.I)
netflix = re.compile(r"netflix(hd|uhd)?", re.I)
amazon = re.compile(r"(amzn|amazon)(hd|uhd)?", re.I)

# Codecs
avc = re.compile(r"([xh].?26[45]|AVC)", re.I)
xvid = re.compile(r"(xvid|divx)", re.I)
mpeg = re.compile(r"(mpeg-?2)", re.I)

# anime
anime_sd = re.compile(r"(848x480|480p|360p|xvid)", re.I)
anime_hd = re.compile(r"((1280|960)x720|720p)", re.I)
anime_fullhd = re.compile(r"(1920x1080|1080p)", re.I)
anime_bluray = re.compile(r"(blue?-?ray|b[rd](?:rip|mux)|(?:\b|_)bd(?:\b|_))", re.I)
